import logging
from abc import ABC
from typing import List

from telegram import BotCommand, Update
from telegram.ext import Handler, CallbackContext

from nyanyabot.core.nyanyabot import NyaNyaBot


class Plugin(ABC):
    """
    Abstract plugin-class for NyaNyaBot. Every plugin must inherit from this.

    Args:
        nyanyabot (:obj:`NyaNyaBot`): NyaNyaBot instance
    """

    commands: List[BotCommand]
    handlers: List[Handler]
    name: str

    def __init__(self, nyanyabot: NyaNyaBot):
        self.commands = []
        self.handlers = []
        self.name = "SETME"

        # Convenience properties
        self.updater = nyanyabot.updater
        self.dispatcher = self.updater.dispatcher
        self.job_queue = self.updater.job_queue
        self.bot_name = self.updater.bot.name
        self.username = self.updater.bot.username
        self.db = nyanyabot.database
        self.logger = logging.getLogger(self.__class__.__name__)

    def run(self, update: Update, context: CallbackContext) -> None:
        pass
