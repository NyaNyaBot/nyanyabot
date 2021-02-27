from telegram import Update, BotCommand, ChatAction
from telegram.ext import CallbackContext

from nyanyabot.core.nyanyabot import NyaNyaBot
from nyanyabot.core.plugin import Plugin
from nyanyabot.core.util import Util
from nyanyabot.handler.regexhandler import RegexHandler


class PluginManager(Plugin):
    def __init__(self, nyanyabot: NyaNyaBot):
        super().__init__(nyanyabot)
        self.name = "plugin_manager"
        self.handlers = [
            RegexHandler(rf"^/list(?:@{self.username})?$", callback=self.list_plugins, privileged=True)
        ]
        self.commands = [
            BotCommand("list", "Listet aktive Plugins auf (nur Superuser)")
        ]
        self.pluginloader = nyanyabot.plugin_loader

    @Util.send_action(ChatAction.TYPING)
    def list_plugins(self, update: Update, context: CallbackContext) -> None:
        text = "<strong>Core-Plugins:</strong>\n"
        text += ", ".join(o.name for o in self.pluginloader.core_plugins)

        text += "\n\n<strong>User-Plugins:</strong>\n"
        if self.pluginloader.plugins:
            text += ", ".join(o.name for o in self.pluginloader.plugins)
        else:
            text += "<i>Keine aktiv</i>"

        update.effective_message.reply_html(text)


plugin = PluginManager
