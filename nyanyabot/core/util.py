import datetime
from functools import wraps
from types import FunctionType
from typing import TYPE_CHECKING, Any

from pytz.tzinfo import DstTzInfo
from telegram import Update
from telegram.ext import Filters, CallbackContext

from nyanyabot.core.constants import Constants

if TYPE_CHECKING:
    from nyanyabot.core.plugin import Plugin


class Util:
    def __init__(self):
        raise Exception("This is a static class which can't be instantiated.")

    @staticmethod
    def send_action(action: str) -> Any:
        def send_action_real(function: FunctionType) -> Any:
            @wraps(function)
            def wrapper(plugin: 'Plugin', update: Update, context: CallbackContext, *args: Any, **kwargs: Any) -> Any:
                if update.effective_message:
                    update.effective_message.reply_chat_action(action=action)
                return function(plugin, update, context, *args, **kwargs)

            return wrapper

        return send_action_real

    @staticmethod
    def is_group(update: Update) -> bool:
        """Returns True if message has been send into group."""
        return Filters.chat_type.groups(update)  # type: ignore


class TimeUtil:
    def __init__(self):
        raise Exception("This is a static class which can't be instantiated.")

    @staticmethod
    def as_timezone(dtime: datetime.datetime,
                    timezone: DstTzInfo = Constants.GERMAN_TIMEZONE) -> datetime.datetime:
        """Converts timezone-aware UTC time to timezone (default: CE(S)T)"""
        return dtime.astimezone(timezone)

    @staticmethod
    def timezone_naive_to_aware(dtime: datetime.datetime,
                                timezone: DstTzInfo = Constants.UTC_TIMEZONE) -> datetime.datetime:
        """Convers timezone-naive datetime to an aware datetime (default: UTC).
           NOTE: This simply adds the tzinfo and does no other conversion!"""
        return timezone.localize(dtime)

    @staticmethod
    def utcnow() -> datetime.datetime:
        """Returns current UTC time as timezone-aware datetime. Convenience function."""
        return TimeUtil.timezone_naive_to_aware(datetime.datetime.utcnow())
