import re
from typing import Union, Pattern, Optional, Any

import telegram.ext
from telegram import Update
from telegram.bot import RT
from telegram.ext.utils.promise import Promise

from nyanyabot.core.util import TimeUtil
from nyanyabot.handler.handler import Handler


class CallbackQueryHandler(Handler, telegram.ext.CallbackQueryHandler):
    """
    Extends telegram.ext.callbackqueryhandler.CallbackQueryHandler
    Added arguments:
        case_sensitive (optional[bool]): Be case sensitive when matching. Default: ``True``
        cooldown (optional[float]): Time between message and when the query should pe processed. Default: ``0.0``
        delete_button (optional[bool]): Delete original callback query button. Default: ``True``
    """
    pattern: re.Pattern

    def __init__(self,
                 *args: Any,
                 pattern: Union[str, Pattern] = None,
                 case_sensitive: bool = True,
                 cooldown: float = 0.0,
                 delete_button: bool = True,
                 log_to_debug: bool = False,
                 **kwargs: Any):
        if isinstance(pattern, str):
            if not case_sensitive:
                self.pattern = re.compile(pattern, re.IGNORECASE)
            else:
                self.pattern = re.compile(pattern)
        elif isinstance(pattern, Pattern):
            if case_sensitive:
                raise ValueError("case_sensitive can't be set when pattern is already a compiled regex.")
            self.pattern = pattern

        self.cooldown = cooldown
        self.delete_button = delete_button
        super(CallbackQueryHandler, self).__init__(*args,
                                                   pattern=self.pattern,
                                                   log_to_debug=log_to_debug,
                                                   **kwargs)

    def handle_update(self, update: Update, *args: Any, **kwargs: Any) \
            -> Union[RT, Promise]:  # pylint: disable=arguments-differ
        if self.delete_button:
            try:
                if update.callback_query:
                    update.callback_query.edit_message_reply_markup(reply_markup="")
            except telegram.TelegramError:
                pass
        return super(CallbackQueryHandler, self).handle_update(update, *args, **kwargs)

    def check_update(self, update: object) -> Optional[Union[bool, object]]:
        return_arg = super(CallbackQueryHandler, self).check_update(update)

        if return_arg and isinstance(update, Update):  # Matched, will be handled by plugin
            if super(CallbackQueryHandler, self).check_update(update):  # Whitelist check
                if update.callback_query.message and self.cooldown > 0.0:
                    callback_time = update.callback_query.message.date
                    current_time = TimeUtil.utcnow()
                    time_dur = (current_time - callback_time).total_seconds()
                    if time_dur < self.cooldown:
                        time_to_wait = str(round(self.cooldown - time_dur, 1)).replace(".", ",")
                        update.callback_query.answer(
                                text=f"🕒 Bitte warte noch {time_to_wait} Sekunden.",
                                show_alert=True
                        )
                        return None
                return return_arg
            update.callback_query.answer(
                    text="Dieses Plugin kann nicht genutzt werden.",
                    show_alert=True
            )
        return None

    def __repr__(self):
        output = f"CallbackQueryHandler for {self.name}"
        if self.pattern:
            output += f": {self.pattern.pattern}"
        return output
