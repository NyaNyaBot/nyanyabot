import traceback
from operator import attrgetter

from sqlalchemy import select, update
from sqlalchemy.dialects.mysql import insert
from telegram import Update, BotCommand, ChatAction
from telegram.ext import CallbackContext

import nyanyabot.plugin
from nyanyabot.core.nyanyabot import NyaNyaBot
from nyanyabot.core.plugin import Plugin
from nyanyabot.core.util import Util
from nyanyabot.handler.regexhandler import RegexHandler


class PluginManager(Plugin):
    def __init__(self, nyanyabot_instance: NyaNyaBot):
        super().__init__(nyanyabot_instance)
        self.name = "plugin_manager"
        self.handlers = [
            RegexHandler(rf"^/list(?:@{self.username})?$", callback=self.list_plugins, privileged=True),
            RegexHandler(rf"^/disable(?:@{self.username})? (.+)$", callback=self.disable_plugin, privileged=True),
            RegexHandler(rf"^/enable(?:@{self.username})? (.+)$", callback=self.enable_plugin, privileged=True),
        ]
        self.commands = [
            BotCommand("list", "Listet aktive Plugins auf (nur Superuser)")
        ]
        self.pluginloader = nyanyabot_instance.plugin_loader

    @Util.send_action(ChatAction.TYPING)
    def list_plugins(self, tg_update: Update, context: CallbackContext) -> None:
        text = "<strong>Geladene Plugins:</strong>\n"
        if self.pluginloader.plugins:
            text += ", ".join(o.name for o in sorted(self.pluginloader.plugins, key=attrgetter("name")))
        else:
            text += "<i>Keine aktiv</i>"

        tg_update.effective_message.reply_html(text)

    @Util.send_action(ChatAction.TYPING)
    def disable_plugin(self, tg_update: Update, context: CallbackContext) -> None:
        plg_name = context.match[1]

        if plg_name in nyanyabot.plugin.__all__:
            tg_update.effective_message.reply_text("❌ Dies ist ein Core-Plugin und kann nicht deaktiviert werden.")
            return

        with self.db.engine.begin() as conn:
            plg = conn.execute(
                    select(self.db.tables.bot_plugins.c.enabled).where(
                            self.db.tables.bot_plugins.c.name == plg_name
                    )
            ).fetchone()

        if not plg:
            tg_update.effective_message.reply_text("❌ Plugin existiert nicht.")
            return

        if not plg.enabled:
            tg_update.effective_message.reply_text("✅ Plugin ist nicht aktiv.")
            return

        try:
            self.pluginloader.unload_plugin(plg_name)
            tg_update.effective_message.reply_text("✅ Plugin deaktiviert.")
        except ValueError:
            tg_update.effective_message.reply_text("❌ Plugin ist nicht geladen.")

        with self.db.engine.begin() as conn:
            conn.execute(
                    update(self.db.tables.bot_plugins).where(
                            self.db.tables.bot_plugins.c.name == plg_name
                    ).values(
                            enabled=0
                    )
            )

    @Util.send_action(ChatAction.TYPING)
    def enable_plugin(self, tg_update: Update, context: CallbackContext) -> None:
        plg_name = context.match[1]

        if plg_name in nyanyabot.plugin.__all__:
            tg_update.effective_message.reply_text("✅ Dies ist ein Core-Plugin, welches schon aktiv ist.")
            return

        with self.db.engine.begin() as conn:
            plg = conn.execute(
                    select(self.db.tables.bot_plugins.c.enabled).where(
                            self.db.tables.bot_plugins.c.name == plg_name
                    )
            ).fetchone()

        if plg and plg.enabled:
            tg_update.effective_message.reply_text("✅ Plugin ist bereits aktiv.")
            return

        try:
            self.pluginloader.load_plugin(f"plugins.{plg_name}")
        except ModuleNotFoundError:
            tg_update.effective_message.reply_text("❌ Plugin existiert nicht.")
            return
        except Exception:
            self.logger.error("".join(traceback.format_exc()))
            tg_update.effective_message.reply_text("❌ Plugin konnte nicht geladen werden.")
            return

        with self.db.engine.begin() as conn:
            conn.execute(
                    insert(self.db.tables.bot_plugins).values(
                            name=plg_name,
                            enabled=1
                    ).on_duplicate_key_update(
                            enabled=1
                    )
            )

        tg_update.effective_message.reply_text("✅ Plugin wurde aktiviert.")


plugin = PluginManager
