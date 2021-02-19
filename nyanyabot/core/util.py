import datetime

from telegram import Update
from telegram.ext import Filters

from nyanyabot.core.constants import Constants


class Util:
    def __init__(self):
        raise Exception("This is a static class which can't be instantiated.")

    @staticmethod
    def is_group(update: Update) -> bool:
        """Returns True if message has been send into group."""
        return Filters.chat_type.groups(update)


class TimeUtil:
    def __init__(self):
        raise Exception("This is a static class which can't be instantiated.")

    @staticmethod
    def as_timezone(dt: datetime.datetime,
                    timezone: datetime.datetime.tzinfo = Constants.GERMAN_TIMEZONE) -> datetime.datetime:
        """Converts timezone-aware UTC time to timezone (default: CE(S)T)"""
        return dt.astimezone(timezone)

    @staticmethod
    def timezone_naive_to_aware(dt: datetime.datetime,
                                timezone: datetime.datetime.tzinfo = Constants.UTC_TIMEZONE) -> datetime.datetime:
        """Convers timezone-naive datetime to an aware datetime (default: UTC).
           NOTE: This simply adds the tzinfo and does no other conversion!"""
        return timezone.localize(dt)

    @staticmethod
    def utcnow() -> datetime.datetime:
        """Returns current UTC time as timezone-aware datetime. Convenience function."""
        return TimeUtil.timezone_naive_to_aware(datetime.datetime.utcnow())
