import argparse

from nyanyabot.core.configuration import Configuration
from nyanyabot.core.nyanyabot import NyaNyaBot


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plugin-based Telegram bot")
    parser.add_argument(
            dest="configpath",
            type=str,
            metavar="<config.json>",
            help="Path to config.json"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()
    config = Configuration(args.configpath)
    bot = NyaNyaBot(config)
    bot.start()


if __name__ == "__main__":
    main()
