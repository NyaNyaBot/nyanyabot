from typing import Union

from sqlalchemy.dialects.mysql import insert
from telegram import Update, TelegramError
from telegram.ext import dispatcher

from nyanyabot.database.database import Database


class Dispatcher(dispatcher.Dispatcher):
    """
    Extends telegram.ext.dispatcher.Dispatcher. It sits between arriving updates and plugin handlers.
    It saves additional data to the database before running through any handler checks.
    """

    def __init__(self, database: Database, *args, **kwargs):  # type: ignore
        super().__init__(*args, **kwargs)
        self.database = database

    # TODO: Remove pylint ignore when Pylint supports Python 3.9:
    #       https://github.com/PyCQA/pylint/issues/3882#issuecomment-745148724
    def process_update(self,
                       update: Union[str, Update, TelegramError]) -> None:  # pylint: disable=unsubscriptable-object
        if isinstance(update, Update):
            if update.effective_chat:
                with self.database.engine.begin() as conn:
                    # Save chat
                    conn.execute(
                            insert(self.database.tables.bot_chats).values(
                                    id=update.effective_chat.id,
                                    title=update.effective_chat.title
                            ).on_duplicate_key_update(
                                    title=update.effective_chat.title,
                            )
                    )

        super().process_update(update)
