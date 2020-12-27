import logging
from queue import Queue

from telegram import Bot
from telegram.error import Unauthorized
from telegram.ext import Defaults, Updater, Dispatcher, JobQueue
from telegram.utils.request import Request

from nyanyabot.core.configuration import Configuration
from nyanyabot.core.constants import Constants


class NyaNyaBot:
    """
    The main NyaNyaBot class.

    Args:
        config (:obj:`Configuration`): Initialized Configuration class
    """

    def __init__(self, config: Configuration):
        self.config = config
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
                        update_queue=Queue(),
                        job_queue=JobQueue(),
                        workers=8,
                ),
        )
        self.updater.dispatcher.job_queue.set_dispatcher(self.updater.dispatcher)  # type: ignore

        try:
            self.logger.info("Logged in as @%s: %s (%s)",
                             self.updater.bot.first_name,
                             self.updater.bot.username,
                             self.updater.bot.id)
        except Unauthorized:
            self.logger.critical("Login failed, check your bot token")
            return

    def start(self):
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