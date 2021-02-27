import json
import logging
import os


class Configuration:
    """
    This class holds the configuration of the bot.

    Args:
        configpath (:obj:`str`): Path to a JSON config file

    Raises:
        FileNotFoundError: If the config file is not found
    """

    def __init__(self, configpath: str):
        # Load config
        if not os.path.isfile(configpath):
            raise FileNotFoundError("Config could not be loaded")

        with open(configpath, "rb") as _config_file:
            config = json.loads(_config_file.read())

        # Logging
        self.logger = logging.getLogger(__name__)
        if config.get("logging"):
            self.setup_logging(config.get("logging").get("level", "WARNING"))
        else:
            self.setup_logging()

        # Webhook config
        self.bot_token = config.get("token")
        self.webhook_enabled = False
        if config.get("webhook"):
            self.webhook_enabled = True
            self.webhook_url = config.get("webhook").get("url")
            self.webhook_interface = config.get("webhook").get("interface", "127.0.0.1")
            self.webhook_path = config.get("webhook").get("path", self.bot_token)
            self.webhook_certificate = config.get("webhook").get("certificate")
            self.webhook_private_key = config.get("webhook").get("key")
            self.webhook_port = config.get("webhook").get("port", 443)

        # Database config
        self.database_name = config.get("database").get("name")
        self.database_user = config.get("database").get("user")
        self.database_password = config.get("database").get("password")
        self.database_host = config.get("database").get("host", "localhost")
        self.database_port = config.get("database").get("port", 3306)

        # Rest of the config
        self.superuser = set(config.get("superuser", []))
        self.set_commands_enabled = config.get("set_commands", False)
        self.error_channel = config.get("error_channel")
        self.plugin_modules = config.get("plugin_modules", ["main"])

    def setup_logging(self, logging_level: str = "WARNING") -> None:
        logging.basicConfig(format="%(asctime)s - %(levelname)-8s - %(name)s - %(message)s", level=logging.DEBUG)
        logging_level = logging_level.upper()
        if logging_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            self.logger.warning("Invalid logging level, using WARNING")
            logging_level = "WARNING"
        logging.getLogger().setLevel(logging_level)
