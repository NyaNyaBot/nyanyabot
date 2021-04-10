import logging
import re
from typing import Any, Union, Pattern, Optional

from telegram import Update, TelegramError
from telegram.ext import callbackqueryhandler
from telegram.ext.handler import RT
from telegram.ext.utils.promise import Promise

from nyanyabot.core.util import Util, TimeUtil


class CallbackQueryHandler(callbackqueryhandler.CallbackQueryHandler):
    """
    Extends telegram.ext.callbackqueryhandler.CallbackQueryHandler
    Added arguments:
        case_sensitive (optional[bool]): Be case sensitive when matching. Default: ``True``
        cooldown (optional[float]): Time between message and when the query should pe processed. Default: ``0.0``
        delete_button (optional[bool]): Delete original callback query button. Default: ``True``
        group_only (optional[bool]): Only run this handler in chat groups. Default: ``False``
        privileged (optional[bool]): Shall this only match when sender is an admin? Default: ``False``
        log_to_debug (optional[bool]): Logs to DEBUG instead of INFO. Default: ``False``
    """
    logger = logging.getLogger(__name__)

    def __init__(
            self,
            *args: Any,
            pattern: Union[str, Pattern] = None,
            case_sensitive: bool = True,
            cooldown: float = 0.0,
            delete_button: bool = True,
            group_only: bool = False,
            privileged: bool = False,
            log_to_debug: bool = False,
            **kwargs: Any,
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
        self.group_only = group_only
        self.privileged = privileged
        self.cooldown = cooldown
        self.delete_button = delete_button
        self.log_to_debug = log_to_debug
        self.name = ""
        self.nyanyabot = None  # type: Any
        self.group = 0  # Is set at runtime

    def check_update(self, update: object) -> Optional[Union[bool, object]]:
        return_args = super().check_update(update)

        if return_args and isinstance(update, Update) and update.callback_query:  # Will be handled by plugin
            if self.group_only and not Util.is_group(update):
                self.logger.debug("group_only set to True and not in a group")
                update.callback_query.answer(
                        text="Dieses Plugin kann nicht genutzt werden.",
                        show_alert=True
                )
                return False

            if self.privileged:
                self.logger.debug("Superuser check")
                if not update.effective_user or update.effective_user.id not in self.nyanyabot.config.superuser:
                    self.logger.debug("Privileged handler and user not a superuser")
                    update.callback_query.answer(
                            text="Du kannst dieses Plugin nicht nutzen, da es nur für Superuser zugelassen ist.",
                            show_alert=True
                    )
                    return False

            if update.effective_message and update.effective_message.date and self.cooldown > 0.0:
                self.logger.debug("Cooldown check")
                callback_time = update.effective_message.date
                current_time = TimeUtil.utcnow()
                time_passed = (current_time - callback_time).total_seconds()
                if time_passed < self.cooldown:
                    time_to_wait = str(round(self.cooldown - time_passed, 1)).replace(".", ",")
                    update.callback_query.answer(
                            text=f"🕒 Bitte warte noch {time_to_wait} Sekunden.",
                            show_alert=True
                    )
                    return False

            if Util.is_group(update):
                self.logger.debug("Plugin-per-chat blacklist check")
                if self.nyanyabot.plugin_loader.is_plugin_disabled_for_chat(
                        update.effective_chat.id,
                        self.name
                ):
                    update.callback_query.answer(
                            text="Dieses Plugin ist für diese Gruppe deaktiviert worden.",
                            show_alert=True
                    )
                    return False

            return return_args

        return False

    # pylint: disable=signature-differs
    def handle_update(
            self,
            update: Update,
            *args: Any,
            **kwargs: Any
    ) -> Union[RT, Promise]:
        if self.log_to_debug:
            self.logger.debug(self)
        else:
            self.logger.info(self)

        if self.delete_button and isinstance(update, Update):
            try:
                if update.callback_query:
                    update.callback_query.edit_message_reply_markup(reply_markup=None)
            except TelegramError:
                pass

        return super().handle_update(update, *args, **kwargs)

    def __repr__(self):
        output = f"CallbackQueryHandler for {self.name}"
        if self.pattern:
            output += f": {self.pattern.pattern}"
        return output
