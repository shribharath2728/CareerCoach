-- Run in psql against career_assistant_db if chat_messages predates the current ORM model.
-- Model expects: id, session_id, role, content, timestamp

ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS role VARCHAR NOT NULL DEFAULT 'user';

-- If you had a legacy "sender" column, map it to role:
-- UPDATE chat_messages SET role = CASE
--   WHEN lower(CAST(sender AS TEXT)) IN ('assistant', 'ai', 'system') THEN 'assistant'
--   ELSE 'user' END;

ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS content TEXT NOT NULL DEFAULT '';

-- If you had a legacy "message" column:
-- UPDATE chat_messages SET content = message WHERE message IS NOT NULL AND (content IS NULL OR TRIM(content) = '');

ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS timestamp TIMESTAMP DEFAULT NOW();

UPDATE chat_messages SET content = '.' WHERE content IS NULL OR TRIM(content) = '';
