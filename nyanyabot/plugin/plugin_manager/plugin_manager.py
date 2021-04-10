import traceback
from operator import attrgetter

from sqlalchemy import select, update, delete
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
            RegexHandler(rf"^/reload(?:@{self.username})?$", callback=self.reload_all_plugins, privileged=True),
            RegexHandler(rf"^/reload(?:@{self.username})? (.+)$", callback=self.reload_plugin, privileged=True),
            RegexHandler(
                    rf"^/disablechat(?:@{self.username})? (.+)$",
                    callback=self.disable_plugin_for_chat,
                    group_only=True,
                    privileged=True
            ),
            RegexHandler(
                    rf"^/enablechat(?:@{self.username})? (.+)$",
                    callback=self.enable_plugin_for_chat,
                    group_only=True,
                    privileged=True
            ),
        ]
        self.commands = [
            BotCommand("list", "Listet aktive Plugins auf (nur Superuser)"),
            BotCommand("disable", "<Plugin> - Deaktiviert ein Plugin (nur Superuser)"),
            BotCommand("enable", "<Plugin> - Aktiviert ein Plugin (nur Superuser)"),
            BotCommand("reload", "[Plugin] - Lädt alle oder ein Plugin neu (nur Superuser)"),
            BotCommand("disablechat", "<Plugin> - Deaktiviert ein Plugin für den aktuellen Chat (nur Superuser)"),
            BotCommand("enablechat", "<Plugin> - Aktiviert ein Plugin für den aktuellen Chat (nur Superuser)"),
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

        try:
            self.pluginloader.unload_plugin(plg_name)
            tg_update.effective_message.reply_text("✅ Plugin deaktiviert.")
        except ValueError:
            tg_update.effective_message.reply_text("❌ Plugin ist nicht aktiv.")

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

    @Util.send_action(ChatAction.TYPING)
    def reload_all_plugins(self, tg_update: Update, context: CallbackContext) -> None:
        message = tg_update.effective_message.reply_text("Alle Plugins werden neu geladen...")
        self.pluginloader.reload_all_plugins()
        message.edit_text("✅ Plugins neu geladen!")

    @Util.send_action(ChatAction.TYPING)
    def reload_plugin(self, tg_update: Update, context: CallbackContext) -> None:
        plg_name = context.match[1]

        message = tg_update.effective_message.reply_text("Plugin wird neu geladen...")
        tg_update.effective_message.reply_chat_action(ChatAction.TYPING)

        try:
            self.pluginloader.unload_plugin(plg_name)
        except ValueError:
            message.edit_text("❌ Plugin ist nicht aktiv.")
            return

        if plg_name in nyanyabot.plugin.__all__:
            self.pluginloader.load_plugin(f"nyanyabot.plugin.{plg_name}")
        else:
            self.pluginloader.load_plugin(f"plugins.{plg_name}")

        message.edit_text("✅ Plugin neu geladen!")

    @Util.send_action(ChatAction.TYPING)
    def disable_plugin_for_chat(self, tg_update: Update, context: CallbackContext) -> None:
        plg_name = context.match[1]

        if plg_name in nyanyabot.plugin.__all__:
            tg_update.effective_message.reply_text("❌ Dies ist ein Core-Plugin und kann nicht deaktiviert werden.")
            return

        with self.db.engine.begin() as conn:
            res = conn.execute(
                    insert(self.db.tables.bot_plugins_chat_blacklist).values(
                            chat_id=tg_update.effective_message.chat_id,
                            disabled_plugin=plg_name
                    ).prefix_with('IGNORE')
            )

        if res.rowcount:
            tg_update.effective_message.reply_text("✅ Plugin wurde für diesen Chat deaktiviert.")
        else:
            tg_update.effective_message.reply_text("✅ Plugin ist für diesen Chat schon deaktiviert.")

    @Util.send_action(ChatAction.TYPING)
    def enable_plugin_for_chat(self, tg_update: Update, context: CallbackContext) -> None:
        plg_name = context.match[1]

        if plg_name in nyanyabot.plugin.__all__:
            tg_update.effective_message.reply_text("❌ Dies ist ein Core-Plugin und kann nicht deaktiviert werden.")
            return

        with self.db.engine.begin() as conn:
            res = conn.execute(
                    delete(self.db.tables.bot_plugins_chat_blacklist).where(
                            self.db.tables.bot_plugins_chat_blacklist.c.chat_id == tg_update.effective_message.chat_id,
                            self.db.tables.bot_plugins_chat_blacklist.c.disabled_plugin == plg_name
                    )
            )

        if res.rowcount:
            tg_update.effective_message.reply_text("✅ Plugin wurde für diesen Chat wieder aktiviert.")
        else:
            tg_update.effective_message.reply_text("✅ Plugin ist für diesen Chat nicht deaktiviert.")


plugin = PluginManager
