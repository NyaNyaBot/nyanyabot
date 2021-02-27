from telegram import Update
from telegram.ext import CallbackContext

from nyanyabot.core.nyanyabot import NyaNyaBot
from nyanyabot.core.plugin import Plugin
from nyanyabot.handler.regexhandler import RegexHandler


class PluginManager(Plugin):
    def __init__(self, nyanyabot: NyaNyaBot):
        super().__init__(nyanyabot)
        self.name = "plugin_manager"
        self.handlers = [
            RegexHandler(rf"^test$", callback=self.run, run_async=True)
        ]

    def run(self, update: Update, context: CallbackContext) -> None:
        pass


plugin = PluginManager
