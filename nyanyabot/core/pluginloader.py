import logging
import operator
import os
import sys
import traceback
from importlib import import_module
from typing import TYPE_CHECKING, List

from sqlalchemy import select

import nyanyabot.plugin

if TYPE_CHECKING:
    from nyanyabot.core.nyanyabot import NyaNyaBot
    from nyanyabot.core.plugin import Plugin


class PluginLoader:
    core_plugins: List['Plugin']
    plugins: List['Plugin']

    def __init__(self, nyanyabot_instance: 'NyaNyaBot'):
        self.nyanyabot = nyanyabot_instance
        self.logger = logging.getLogger(__name__)
        self.core_plugins = []
        self.plugins = []
        self.load_core_plugins()
        self.load_user_plugins()

    def load_core_plugins(self):
        group = 0

        for num, plugin in enumerate(nyanyabot.plugin.__all__):
            self.logger.info("(%s/%s) Loading core plugin: %s", num + 1, len(nyanyabot.plugin.__all__), plugin)
            module = import_module("nyanyabot.plugin." + plugin)
            if hasattr(module, "plugin"):  # Is Plugin?
                # Call the "plugin" variable which references the specific plugin class
                # pylint: disable=used-before-assignment
                plugin_module: Plugin = module.plugin(self.nyanyabot)  # type:ignore

                for handler in plugin_module.handlers:
                    handler.name = plugin_module.name  # type: ignore
                    handler.nyanyabot = self.nyanyabot  # type: ignore
                    self.nyanyabot.updater.dispatcher.add_handler(handler, group=group)
                    group += 1

                self.core_plugins.append(plugin_module)

    def load_user_plugins(self):
        plugins = []
        group = len(self.core_plugins)

        # Load enabled plugins from database
        with self.nyanyabot.database.engine.begin() as conn:
            for row in conn.execute(
                    select(self.nyanyabot.database.tables.bot_plugins.c.name).where(
                            self.nyanyabot.database.tables.bot_plugins.c.enabled == 1
                    )
            ):
                plugins.append(row.name)

        # Setup plugins
        for plugin_dir in self.nyanyabot.config.plugin_modules:
            sys.path.append(os.path.join("..", "user_plugins", plugin_dir))

        for num, plugin in enumerate(plugins):
            self.logger.info("(%s/%s) Loading plugin: %s", num + 1, len(plugins), plugin)
            try:
                module = import_module("plugins." + plugin)
            except Exception:
                self.logger.error("".join(traceback.format_exc()))
                continue

            # Setup handlers, jobs and commands
            if hasattr(module, "plugin"):  # Is Plugin?
                try:
                    # Call the "plugin" variable which references the specific plugin class
                    # pylint: disable=used-before-assignment
                    plugin_module: Plugin = module.plugin(self.nyanyabot)  # type:ignore
                except Exception:
                    self.logger.error("".join(traceback.format_exc()))
                    continue

                for handler in plugin_module.handlers:
                    handler.name = plugin_module.name  # type: ignore
                    handler.nyanyabot = self.nyanyabot  # type: ignore
                    self.nyanyabot.updater.dispatcher.add_handler(handler, group=group)
                    group += 1

                self.plugins.append(plugin_module)

    def setup_commands(self):
        commands = []
        for plugin in self.plugins:
            for command in plugin.commands:
                commands.append(command)

        self.logger.info("Setting commands...")
        if len(commands) > 100:
            self.logger.warning("More than 100 commands detected, skipping")
        else:
            commands.sort(key=operator.attrgetter("command"))
            self.nyanyabot.updater.bot.set_my_commands(commands)
