-- depends: 0001.init

create TABLE IF NOT EXISTS `bot_plugins` (
  `name` VARCHAR(50) NOT NULL,
  `enabled` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`name`)
) DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='NyaNyaBot plugins';

create TABLE IF NOT EXISTS `bot_plugins_chat_blacklist` (
  `chat_id` bigint(20) NOT NULL,
  `disabled_plugin` varchar(50) NOT NULL,
  PRIMARY KEY (`chat_id`,`disabled_plugin`),
  CONSTRAINT `FK_bot_plugins_chat_blacklist_bot_chats` FOREIGN KEY (`chat_id`) REFERENCES `bot_chats` (`id`) ON delete CASCADE
) DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Disabled plugins for a chat';
