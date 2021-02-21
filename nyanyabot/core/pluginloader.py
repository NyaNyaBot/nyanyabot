import logging
import operator
import sys
import traceback
from importlib import import_module
from typing import TYPE_CHECKING

from sqlalchemy import select

if TYPE_CHECKING:
    from nyanyabot.core.plugin import Plugin


class PluginLoader:
    def __init__(self, nyanyabot):
        self.nyanyabot = nyanyabot
        self.logger = logging.getLogger(__name__)
        self.plugins = []
        self.load_plugins()

    def load_plugins(self):
        plugins = []
        group = 0

        # Load enabled plugins from database
        with self.nyanyabot.database.engine.begin() as conn:
            for row in conn.execute(
                    select(self.nyanyabot.database.tables.bot_plugins.c.name).where(
                            self.nyanyabot.database.tables.bot_plugins.c.enabled == 1
                    )
            ):
                plugins.append(row.name)

        # Setup plugins
        for plugin_dir in self.nyanyabot.config.plugin_dirs:
            sys.path.append(plugin_dir)

        for num, plugin in enumerate(plugins):
            self.logger.info("(%s/%s) Loading plugin: %s", num + 1, len(plugins), plugin)
            try:
                module = import_module("nyanyabot.plugin." + plugin)
            except ModuleNotFoundError:
                try:
                    module = import_module("plugins." + plugin)
                except Exception:
                    self.logger.error("".join(traceback.format_exc()))
                    continue
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
