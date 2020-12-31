CREATE TABLE IF NOT EXISTS `bot_chats` (
  `id` bigint(20) NOT NULL,
  `title` VARCHAR(255),
  `whitelisted` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`)
) DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='NyaNyaBot chat data';

CREATE TABLE IF NOT EXISTS `bot_users` (
  `id` INT NOT NULL,
  `first_name` VARCHAR(255) DEFAULT NULL,
  `last_name` VARCHAR(255) DEFAULT NULL,
  `username` VARCHAR(50) DEFAULT NULL,
  `whitelisted` tinyint(1) NOT NULL DEFAULT 0,
  `blocked` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `username` (`username`)
) DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='NyaNyaBot user data';

CREATE TABLE IF NOT EXISTS `lnk_bot_chats_id__bot_users_id` (
  `chat_id` bigint(20) NOT NULL,
  `user_id` INT NOT NULL,
  PRIMARY KEY (`chat_id`,`user_id`),
  CONSTRAINT `FK_chats_users_chats` FOREIGN KEY (`chat_id`) REFERENCES `bot_chats` (`id`),
  CONSTRAINT `FK_chats_users_users` FOREIGN KEY (`user_id`) REFERENCES `bot_users` (`id`)
) DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Link table for bot_chats-id and bot_users-id';
