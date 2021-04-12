import logging
from typing import Any, Optional, Union, Dict

from telegram import Update
from telegram.ext import messagehandler
from telegram.ext.handler import RT
from telegram.ext.utils.promise import Promise

from nyanyabot.core.util import Util


class MessageHandler(messagehandler.MessageHandler):
    """
    Extends telegram.ext.messagehandler.MessageHandler
    Added arguments:
        group_only (optional[bool]): Only run this handler in chat groups. Default: ``False``
        handle_edits (optional[bool]): Processes edited message if set to True. Default: ``False``
        privileged (optional[bool]): Shall this only match when sender is an admin? Default: ``False``
        log_to_debug (optional[bool]): Logs to DEBUG instead of INFO. Default: ``True``
    """
    logger = logging.getLogger(__name__)

    def __init__(
            self,
            *args: Any,
            group_only: bool = False,
            handle_edits: bool = False,
            privileged: bool = False,
            log_to_debug: bool = True,
            **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.handle_edits = handle_edits
        self.group_only = group_only
        self.privileged = privileged
        self.log_to_debug = log_to_debug
        self.name = ""
        self.nyanyabot = None  # type: Any
        self.group = 0  # Is set at runtime

    def check_update(self, update: object) -> Optional[Union[bool, Dict[str, object]]]:
        if isinstance(update, Update) and update.effective_message:
            if self.group_only and not Util.is_group(update):
                self.logger.debug("group_only set to True and not in a group")
                return False

            if update.edited_message and not self.handle_edits:
                self.logger.debug("Edited message, but shouldn't be handled")
                return False

            # Add caption as text
            if update.effective_message.caption:
                update.effective_message.text = update.effective_message.caption

            return_args = super().check_update(update)
            if return_args:  # Will be handled by plugin
                if self.privileged and update.effective_user:
                    self.logger.debug("Superuser Check")
                    if update.effective_user.id not in self.nyanyabot.config.superuser:
                        self.logger.debug("Privileged handler and user not a superuser")
                        return False

                if Util.is_group(update):
                    self.logger.debug("Plugin-per-chat blacklist check")
                    if self.nyanyabot.plugin_loader.is_plugin_disabled_for_chat(
                            update.effective_chat.id,  # type: ignore
                            self.name
                    ):
                        return False

                return return_args
        return False

    # pylint: disable=signature-differs
    def handle_update(
            self,
            *args: Any,
            **kwargs: Any
    ) -> Union[RT, Promise]:
        if self.log_to_debug:
            self.logger.debug(self)
        else:
            self.logger.info(self)
        return super().handle_update(*args, **kwargs)

    def __repr__(self):
        return f"MessageHandler for {self.name}: {self.filters}"
