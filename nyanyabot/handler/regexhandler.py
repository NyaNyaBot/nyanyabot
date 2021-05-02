import logging
import re
from typing import Pattern, Any, Union

from telegram.ext import Filters

from nyanyabot.handler.messagehandler import MessageHandler


class RegexHandler(MessageHandler):
    """
    Reintroduces telegram.ext.regexhandler.RegexHandler
    Added arguments:
        case_sensitive (optional[bool]): Be case sensitive when matching. Default: ``False``
    """
    logger = logging.getLogger(__name__)

    def __init__(
            self,
            pattern: Union[str, Pattern],
            *args: Any,
            case_sensitive: bool = False,
            log_to_debug: bool = False,
            **kwargs: Any,
    ):
        if isinstance(pattern, str):
            if case_sensitive:
                self.pattern = re.compile(pattern)
            else:
                self.pattern = re.compile(pattern, re.IGNORECASE)
        else:
            if case_sensitive:
                raise ValueError("case_sensitive can't be set when pattern is already a compiled regex.")
            self.pattern = pattern
        super().__init__(
                Filters.regex(self.pattern),
                *args,
                log_to_debug=log_to_debug,
                **kwargs
        )

    def __repr__(self):
        return f"RegexHandler for {self.name}: {self.pattern.pattern}"
