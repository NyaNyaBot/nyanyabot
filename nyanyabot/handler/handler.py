import logging
from abc import ABC
from typing import Union, Optional, Any

import telegram.ext
from telegram import Update
from telegram.ext.handler import RT
from telegram.ext.utils.promise import Promise

from nyanyabot.core.nyanyabot import NyaNyaBot


class Handler(telegram.ext.Handler, ABC):
    """
    Extends telegram.ext.handler.Handler and is the basis for NyaNyaBot handlers.
    Added arguments:
        privileged (optional[bool]): Shall this only match when sender is an admin? Default: ``False``
        log_to_debug (optional[bool]): Logs to DEBUG instead of INFO. Default: ``True``
    """
    nyanyabot: Optional[NyaNyaBot]

    def __init__(self,
                 *args: Any,
                 privileged: bool = False,
                 log_to_debug: bool = True,
                 **kwargs):
        super(Handler, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.privileged = privileged
        self.log_to_debug = log_to_debug
        self.name = ""  # Will be set to the plugin's name at runtime
        self.nyanyabot = None  # Will be set to the NyaNyaBot instance at runtime

    def handle_update(self, *args, **kwargs) -> Union[RT, Promise]:  # pylint: disable=signature-differs
        if self.log_to_debug:
            self.logger.debug(self)
        else:
            self.logger.info(self)
        return super(Handler, self).handle_update(*args, **kwargs)

    def check_update(self, update: object) -> Optional[Union[bool, object]]:
        if isinstance(update, Update):
            self.logger.debug("Superuser Check")
            if update.effective_user.id in self.nyanyabot.config.superuser:
                self.logger.debug("= Is superuser")
                return True

            if self.privileged and update.effective_user.id not in self.nyanyabot.config.superuser:
                self.logger.debug("= Privileged handler and user not a superuser")
                return False

        self.logger.debug("check_update() passed")
        return True
