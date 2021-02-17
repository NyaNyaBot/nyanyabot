CREATE TABLE IF NOT EXISTS `bot_plugins` (
  `name` VARCHAR(50) NOT NULL,
  `enabled` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`name`)
) DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='NyaNyaBot plugins';