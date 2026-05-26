-- Migration: Add user_sessions table for concurrent-login prevention
-- Replaces the in-memory cache-based session tracking with a persistent DB store.
-- Every new login revokes previous active sessions and inserts a fresh row.
-- The session_id is embedded in the JWT jti claim and validated on every request.

CREATE TABLE IF NOT EXISTS `user_sessions` (
    `id`          INT          NOT NULL AUTO_INCREMENT,
    `UserId`      INT          NOT NULL,
    `session_id`  VARCHAR(36)  NOT NULL,
    `status`      VARCHAR(10)  NOT NULL DEFAULT 'active',
    `ip_address`  VARCHAR(45)  NULL,
    `user_agent`  TEXT         NULL,
    `created_at`  DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `expires_at`  DATETIME(6)  NOT NULL,
    `revoked_at`  DATETIME(6)  NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_session_id` (`session_id`),
    KEY `ix_user_status`    (`UserId`, `status`),
    KEY `ix_sid_status`     (`session_id`, `status`),
    CONSTRAINT `fk_usersession_user`
        FOREIGN KEY (`UserId`) REFERENCES `users` (`UserId`)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
