from sqlalchemy import delete
from sqlalchemy.dialects.mysql import insert
from telegram import Update
from telegram.ext import dispatcher, Filters

from nyanyabot.database.database import Database


class Dispatcher(dispatcher.Dispatcher):
    """
    Extends telegram.ext.dispatcher.Dispatcher. It sits between arriving updates and plugin handlers.
    It saves additional data to the database before running through any handler checks.
    """

    def __init__(self, database: Database, *args, **kwargs):  # type: ignore
        super().__init__(*args, **kwargs)
        self.database = database

    def process_update(self, update: object) -> None:
        if isinstance(update, Update) and update.effective_message:
            if update.effective_chat and Filters.chat_type.groups(update):
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

                    if not Filters.status_update(update) and update.effective_user:
                        # Save user
                        conn.execute(
                                insert(self.database.tables.bot_users).values(
                                        id=update.effective_user.id,
                                        first_name=update.effective_user.first_name,
                                        last_name=update.effective_user.last_name,
                                        username=update.effective_user.username
                                ).on_duplicate_key_update(
                                        first_name=update.effective_user.first_name,
                                        last_name=update.effective_user.last_name,
                                        username=update.effective_user.username
                                )
                        )

                        # Save user-chat-relationship
                        conn.execute(
                                insert(self.database.tables.link_bot_chats_id__bot_users_id).values(
                                        chat_id=update.effective_chat.id,
                                        user_id=update.effective_user.id
                                ).prefix_with('IGNORE')
                        )
                    else:
                        if update.effective_message.new_chat_members:
                            user_data = []
                            relationship_data = []
                            for user in update.effective_message.new_chat_members:
                                user_data.append({
                                    "id":         user.id,
                                    "first_name": user.first_name,
                                    "last_name":  user.last_name,
                                    "username":   user.username
                                })
                                relationship_data.append({
                                    "chat_id": update.effective_chat.id,
                                    "user_id": user.id
                                })

                            # Save new users, construct on_duplicate_key for multiple values
                            insert_stmt = insert(self.database.tables.bot_users).values(user_data)
                            dup_stmt = insert_stmt.on_duplicate_key_update(
                                    first_name=insert_stmt.inserted.first_name,
                                    last_name=insert_stmt.inserted.last_name,
                                    username=insert_stmt.inserted.username
                            )
                            conn.execute(dup_stmt)

                            # Save user-chat-relationship
                            conn.execute(
                                    insert(self.database.tables.link_bot_chats_id__bot_users_id).values(
                                            relationship_data
                                    ).prefix_with('IGNORE')
                            )
                        elif update.effective_message.left_chat_member:
                            conn.execute(
                                    delete(self.database.tables.link_bot_chats_id__bot_users_id).where(
                                            self.database.tables.link_bot_chats_id__bot_users_id.c.chat_id ==
                                            update.effective_chat.id,
                                            self.database.tables.link_bot_chats_id__bot_users_id.c.user_id ==
                                            update.effective_message.left_chat_member.id
                                    )
                            )

        super().process_update(update)
