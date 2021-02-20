from typing import Union, Optional, Any, Dict

import telegram.ext
from telegram import Update

from nyanyabot.core.util import Util
from nyanyabot.handler.handler import Handler


class MessageHandler(Handler, telegram.ext.MessageHandler):
    """
    Extends telegram.ext.messagehandler.MessageHandler
    Added arguments:
        group_only (optional[bool]): Only run this handler in chat groups. Default: ``False``
        handle_edits (optional[bool]): Processes edited message if set to True. Default: ``False``
    """

    def __init__(self,
                 *args: Any,
                 group_only: bool = False,
                 handle_edits: bool = False,
                 log_to_debug: bool = True,
                 **kwargs: Any):
        self.handle_edits = handle_edits
        self.group_only = group_only
        super(MessageHandler, self).__init__(
                *args,
                log_to_debug=log_to_debug,
                **kwargs)

    def check_update(self, update: object) -> Optional[Union[bool, Dict[str, object]]]:
        if isinstance(update, Update) and (update.message or update.edited_message) and update.effective_message:
            # Edited message
            if update.edited_message:
                if not self.handle_edits:
                    return None

            # Add caption as text
            if update.effective_message.caption:
                update.effective_message.text = update.effective_message.caption

            if self.group_only and not Util.is_group(update):
                self.logger.debug("group_only set to True and not in a group")
                return None

            return_arg = self.filters(update)
        else:
            return None

        if return_arg:  # Matched, will be handled by plugin
            if super(MessageHandler, self).check_update(update):  # Whitelist checks
                return return_arg
        return None

    def __repr__(self):
        return f"MessageHandler for {self.name}: {self.filters}"
