import html
import logging
import operator
import sys
import traceback
from importlib import import_module
from io import StringIO
from queue import Queue

from sqlalchemy import select
from telegram import Bot, ParseMode
from telegram.error import Unauthorized
from telegram.ext import Defaults, Updater, JobQueue, CallbackContext
from telegram.utils.request import Request

from nyanyabot.core.configuration import Configuration
from nyanyabot.core.constants import Constants
from nyanyabot.core.dispatcher import Dispatcher
from nyanyabot.database.database import Database


class NyaNyaBot:
    """
    The main NyaNyaBot class.

    Args:
        config (:obj:`Configuration`): Initialized Configuration class
    """

    def error_handler(self, update: object, context: CallbackContext) -> None:
        if not context.error:
            self.logger.error("Unknown exception happened.")
            if self.config.error_channel:
                context.bot.send_message(
                        chat_id=self.config.error_channel,
                        text="❌❌❌ <strong>Eine unbekannte Exception ist aufgetreten.</strong>",
                        parse_mode=ParseMode.HTML
                )
            return

        trace = ''.join(traceback.format_tb(context.error.__traceback__))

        if update:
            log_msg = f"Exception happened with update:\n" \
                      f"{update}\n\n" \
                      f"Traceback (most recent call last):\n" \
                      f"{trace}{context.error}"
        else:
            log_msg = f"Exception happened:\n{trace}{context.error}"

        self.logger.error(log_msg)

        if self.config.error_channel:
            context.bot.send_document(
                    chat_id=self.config.error_channel,
                    caption=f"❌❌❌ <strong>Update verursachte Fehler</strong>:\n"
                            f"<code>{html.escape(str(context.error))}</code>",
                    document=StringIO(log_msg),
                    filename="traceback.txt",
                    parse_mode=ParseMode.HTML
            )

    def __init__(self, config: Configuration):
        self.config = config
        self.database = Database(config.database_name, config.database_user, config.database_password,
                                 config.database_host, config.database_port)
        self.plugins = []  # type: ignore

        self.logger = logging.getLogger(__name__)
        self.logger.info("Starting up bot")

        defaults = Defaults(tzinfo=Constants.UTC_TIMEZONE)
        self.updater = Updater(
                workers=None,  # type: ignore
                defaults=defaults,
                use_context=True,
                dispatcher=Dispatcher(
                        bot=Bot(
                                token=self.config.bot_token,
                                request=Request(
                                        con_pool_size=14,
                                        connect_timeout=10,
                                        read_timeout=7
                                ),
                                defaults=defaults
                        ),
                        database=self.database,
                        update_queue=Queue(),
                        job_queue=JobQueue(),
                        workers=8,
                ),
        )
        self.updater.dispatcher.job_queue.set_dispatcher(self.updater.dispatcher)  # type: ignore
        self.updater.dispatcher.add_error_handler(self.error_handler, run_async=True)

        self.load_plugins()
        if self.config.set_commands_enabled:
            self.setup_commands()

    def load_plugins(self):
        plugins = []
        group = 0

        # Load enabled plugins from database
        with self.database.engine.begin() as conn:
            for row in conn.execute(
                    select(self.database.tables.bot_plugins.c.name).where(
                            self.database.tables.bot_plugins.c.enabled == 1
                    )
            ):
                plugins.append(row.name)

        # Setup plugins
        for num, plugin in enumerate(plugins):
            self.logger.info("(%s/%s) Loading plugin: %s", num + 1, len(plugins), plugin)
            try:
                import_module("nyanyabot.plugin." + plugin)
            except Exception:
                self.logger.error("".join(traceback.format_exc()))
                continue

            # Setup handlers, jobs and commands
            module = sys.modules.get("nyanyabot.plugin." + plugin)
            if hasattr(module, "plugin"):  # Is Plugin?
                try:
                    plugin_module = module.plugin(self)  # type: ignore
                except Exception:
                    self.logger.error("".join(traceback.format_exc()))
                    continue
                for handler in plugin_module.handlers:
                    handler.name = plugin_module.name
                    self.updater.dispatcher.add_handler(handler, group=group)
                    group += 1

                self.plugins.append(plugin_module)

    def setup_commands(self):
        commands = []
        for plugin in self.plugins:
            for command in plugin.commands:
                commands.append(command)

        self.logger.info("Setting commands...")
        if len(commands) > 100:
            self.logger.warning("More than 100 commands detected, skipping")
        else:
            commands.sort(key=operator.attrgetter("command"))
            self.updater.bot.set_my_commands(commands)

    def start(self):
        try:
            self.logger.info("Logged in as @%s: %s (%s)",
                             self.updater.bot.first_name,
                             self.updater.bot.username,
                             self.updater.bot.id)
        except Unauthorized:
            self.logger.critical("Login failed, check your bot token")
            return

        if self.config.webhook_enabled:
            self.logger.info("Setting webhook")
            if self.updater.bot.set_webhook(
                    url=self.config.webhook_url,
                    allowed_updates=["message", "edited_message", "inline_query", "callback_query"]
            ):
                self.logger.info("Starting Tornado")
                self.updater.start_webhook(
                        listen=self.config.webhook_interface,
                        port=self.config.webhook_port,
                        webhook_url=self.config.webhook_url,
                        url_path=self.config.webhook_path,
                        cert=self.config.webhook_certificate,
                        key=self.config.webhook_private_key,
                        clean=True,
                        allowed_updates=["message", "edited_message", "inline_query", "callback_query"]
                )
            else:
                self.logger.critical("Webhook could not be set.")
                return
        else:
            self.logger.info("Starting long-polling")
            self.updater.start_polling(
                    clean=True,
                    allowed_updates=["message", "edited_message", "inline_query", "callback_query"]
            )

        self.logger.info("Bot completely loaded")
        self.updater.idle()
        self.logger.info("Bye!")
