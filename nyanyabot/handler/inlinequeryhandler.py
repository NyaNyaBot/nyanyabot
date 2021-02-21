import logging
import re
from typing import Any, Union, Pattern, Optional, Match

from telegram import Update
from telegram.bot import RT
from telegram.ext import inlinequeryhandler
from telegram.ext.utils.promise import Promise


class InlineQueryHandler(inlinequeryhandler.InlineQueryHandler):
    """
    Extends telegram.ext.inlinequeryhandler.InlineQueryHandler
    Added arguments:
        case_sensitive (optional[bool]): Be case sensitive when matching. Default: ``False``
        privileged (optional[bool]): Shall this only match when sender is an admin? Default: ``False``
        log_to_debug (optional[bool]): Logs to DEBUG instead of INFO. Default: ``False``
    """
    logger = logging.getLogger(__name__)

    def __init__(
            self,
            *args: Any,
            pattern: Union[str, Pattern] = None,
            case_sensitive: bool = False,
            privileged: bool = False,
            log_to_debug: bool = False,
            **kwargs: Any
    ):
        super().__init__(*args, **kwargs)
        if isinstance(pattern, str):
            if case_sensitive:
                self.pattern = re.compile(pattern)
            else:
                self.pattern = re.compile(pattern, re.IGNORECASE)
        else:
            if case_sensitive:
                raise ValueError("case_sensitive can't be set when pattern is already a compiled regex.")
            self.pattern = pattern
        self.privileged = privileged
        self.log_to_debug = log_to_debug
        self.name = ""
        self.nyanyabot = None  # type: Any

    def check_update(self, update: object) -> Optional[Union[bool, Match]]:
        return_args = super().check_update(update)

        if return_args and isinstance(update, Update) and update.inline_query:  # Will be handled by plugin
            if self.privileged:
                self.logger.debug("Superuser check")
                if not update.effective_user or update.effective_user.id not in self.nyanyabot.config.superuser:
                    self.logger.debug("Privileged handler and user not a superuser")
                    update.inline_query.answer(results=[], cache_time=5, is_personal=True)
                    return False
            return return_args

        return False

    # pylint: disable=signature-differs
    def handle_update(
            self,
            *args: Any,
            **kwargs: Any,
    ) -> Union[RT, Promise]:
        if self.log_to_debug:
            self.logger.debug(self)
        else:
            self.logger.info(self)

        return super().handle_update(*args, **kwargs)

    def __repr__(self):
        output = f"InlineQueryHandler for {self.name}"
        if self.pattern:
            output += f": {self.pattern.pattern}"
        return output
