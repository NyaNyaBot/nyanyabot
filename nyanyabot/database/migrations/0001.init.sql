CREATE TABLE IF NOT EXISTS `bot_chats` (
  `id` bigint(20) NOT NULL,
  `title` VARCHAR(255),
  `whitelisted` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`)
) DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='NyaNyaBot chat data';
