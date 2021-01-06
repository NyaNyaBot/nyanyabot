from sqlalchemy import MetaData, Table
from sqlalchemy import engine


class Tables:
    """
    Describes the database tables.

    Args:
        db_engine (:obj:`engine.Engine`): SQLAlchemy database engine
    """

    def __init__(self, db_engine: engine.Engine):
        metadata = MetaData()

        self.bot_chats = Table("bot_chats", metadata, autoload_with=db_engine)
        self.bot_users = Table("bot_users", metadata, autoload_with=db_engine)
        self.link_bot_chats_id__bot_users_id = Table("lnk_bot_chats_id__bot_users_id", metadata,
                                                     autoload_with=db_engine)
