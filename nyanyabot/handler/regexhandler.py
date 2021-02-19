import re
from typing import Union, Pattern

from telegram.ext import Filters

from nyanyabot.handler.messagehandler import MessageHandler


class RegexHandler(MessageHandler):
    """
    Reintroduces telegram.ext.regexhandler.RegexHandler
    Added arguments:
        case_sensitive (optional[bool]): Be case sensitive when matching. Default: ``False``
    """
    pattern: re.Pattern

    def __init__(self,
                 pattern: Union[str, Pattern],
                 *args,
                 case_sensitive: bool = False,
                 log_to_debug: bool = False,
                 **kwargs):
        if isinstance(pattern, str):
            if not case_sensitive:
                self.pattern = re.compile(pattern, re.IGNORECASE)
            else:
                self.pattern = re.compile(pattern)
        else:
            if case_sensitive:
                raise ValueError("case_sensitive can't be set when pattern is already a compiled regex.")
            self.pattern = pattern

        super(RegexHandler, self).__init__(Filters.regex(self.pattern),
                                           *args,
                                           log_to_debug=log_to_debug,
                                           **kwargs)

    def __repr__(self):
        return f"RegexHandler for {self.name}: {self.pattern.pattern}"
