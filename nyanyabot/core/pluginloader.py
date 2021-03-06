import logging
import operator
import os
import sys
import traceback
from importlib import import_module
from typing import TYPE_CHECKING, List

from sqlalchemy import select, func

import nyanyabot.plugin

if TYPE_CHECKING:
    from nyanyabot.core.nyanyabot import NyaNyaBot
    from nyanyabot.core.plugin import Plugin


class PluginLoader:
    plugins: List['Plugin']

    def __init__(self, nyanyabot_instance: 'NyaNyaBot'):
        self.nyanyabot = nyanyabot_instance
        self.logger = logging.getLogger(__name__)
        self.plugins = []
        self.group = 0

    def load_plugin(self, path: str) -> None:
        module = import_module(path)

        # Setup handlers, jobs and commands
        if hasattr(module, "plugin"):  # Is Plugin?
            # Call the "plugin" variable which references the specific plugin class
            # pylint: disable=used-before-assignment
            plugin_module: Plugin = module.plugin(self.nyanyabot)  # type:ignore

            for handler in plugin_module.handlers:
                handler.name = plugin_module.name  # type: ignore
                handler.nyanyabot = self.nyanyabot  # type: ignore
                handler.group = self.group  # type: ignore
                self.nyanyabot.updater.dispatcher.add_handler(handler, group=self.group)
                self.group += 1

            self.plugins.append(plugin_module)

    def load_core_plugins(self):
        for num, plugin in enumerate(nyanyabot.plugin.__all__):
            self.logger.info("(%s/%s) Loading core plugin: %s", num + 1, len(nyanyabot.plugin.__all__), plugin)
            try:
                self.load_plugin(f"nyanyabot.plugin.{plugin}")
            except Exception:
                self.logger.error("".join(traceback.format_exc()))
                continue

    def load_user_plugins(self):
        plugins = []

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
                self.load_plugin(f"plugins.{plugin}")
            except Exception:
                self.logger.error("".join(traceback.format_exc()))
                continue

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

    def unload_plugin(self, name: str) -> None:
        for plg in self.plugins:
            if plg.name == name:
                plugin = plg
                break
        else:
            raise ValueError("Plugin not found.")

        # Unload handlers
        for handler in plugin.handlers:
            self.nyanyabot.updater.dispatcher.remove_handler(handler, group=handler.group)  # type: ignore

        # Unload module
        modules = {name: module for name, module in sys.modules.items()
                   if name.startswith(f"plugins.{plugin.name}") or name.startswith(f"nyanyabot.plugin.{plugin.name}")}
        for module_name, _ in modules.items():
            del sys.modules[module_name]

        # Remove from loaded plugin
        self.plugins.remove(plugin)

    def reload_all_plugins(self) -> None:
        # Remove all handlers
        self.logger.info("Removing handlers")
        for group in list(self.nyanyabot.updater.dispatcher.handlers.keys()):  # create a copy to avoid RuntimeErrors
            while (group in self.nyanyabot.updater.dispatcher.handlers.keys()) and \
                    self.nyanyabot.updater.dispatcher.handlers[group]:
                self.nyanyabot.updater.dispatcher.remove_handler(
                        self.nyanyabot.updater.dispatcher.handlers[group][0],
                        group=group
                )

        # Unload all Python modules
        self.logger.info("Unloading Python modules")
        modules = {name: module for name, module in sys.modules.items()
                   if name.startswith("nextbot.plugin.") or name.startswith("plugins.")}
        for name, _ in modules.items():
            del sys.modules[name]

        self.plugins = []
        self.group = 0
        self.load_core_plugins()
        self.load_user_plugins()

    def is_plugin_disabled_for_chat(self, chat_id: int, name: str) -> bool:
        with self.nyanyabot.database.engine.begin() as conn:
            # https://stackoverflow.com/a/12942437
            res = conn.execute(
                    select([func.count()]).select_from(self.nyanyabot.database.tables.bot_plugins_chat_blacklist).where(
                            self.nyanyabot.database.tables.bot_plugins_chat_blacklist.c.chat_id == chat_id,
                            self.nyanyabot.database.tables.bot_plugins_chat_blacklist.c.disabled_plugin == name
                    )
            ).fetchone()

        return res[0] == 1
