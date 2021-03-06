import logging
import os

import yoyo
from sqlalchemy import create_engine

from nyanyabot.database.tables import Tables


class Database:
    """
    Provides an interface to the database.

    Args:
        name (:obj:`str`): Name of the database
        user (:obj:`str`): Database user
        password (:obj:`str`): Database password
        host (:obj:`str`, optional): Database host (defaults to "localhost")
        port (:obj:`int`, optional): Database port (defaults to 3306)
    """

    def __init__(self,
                 name: str,
                 user: str,
                 password: str,
                 host: str = "localhost",
                 port: int = 3306):
        self.logger = logging.getLogger(__name__)
        self.connection_string = f"mysql+mysqldb://{user}:{password}@{host}:{port}/{name}?charset=utf8mb4"
        self.migrate()

        self.engine = create_engine(self.connection_string, echo=False, future=True)
        self.tables = Tables(self.engine)

    def migrate(self):
        """Starts yoyo-migrations."""
        backend = yoyo.get_backend(self.connection_string)
        migrations = yoyo.read_migrations(os.path.join("database", "migrations"))
        with backend.lock():
            backend.apply_migrations(backend.to_apply(migrations))
