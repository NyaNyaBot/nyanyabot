from telegram import BotCommand, Update
from telegram.ext import CallbackContext

from nyanyabot.core.nyanyabot import NyaNyaBot
from nyanyabot.core.plugin import Plugin
from nyanyabot.handler.regexhandler import RegexHandler


class EchoPlugin(Plugin):
    def __init__(self, nyanyabot: NyaNyaBot):
        super().__init__(nyanyabot)
        self.name = "echo"
        self.handlers = [
            RegexHandler(rf"^/e(?:cho)?(?:@{self.username})? (.*)$", callback=self.run, run_async=True)
        ]
        self.commands = [
            BotCommand("echo", "<Text> - Text über Bot ausgeben")
        ]

    def run(self, update: Update, context: CallbackContext) -> None:
        text = context.match[1]
        update.effective_message.reply_text(
                text=text,
                quote=False,
                disable_web_page_preview=True
        )


plugin = EchoPlugin
