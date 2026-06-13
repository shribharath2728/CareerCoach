-- SkillLens Tier 1 Migration
-- Run this against your PostgreSQL database to add Tier 1 feature columns

-- Add coaching style preference
ALTER TABLE users ADD COLUMN IF NOT EXISTS coaching_style VARCHAR DEFAULT 'supportive';

-- Add streak tracking columns
ALTER TABLE users ADD COLUMN IF NOT EXISTS streak_count INTEGER NOT NULL DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_practice_date DATE;

-- Ensure existing users have defaults
UPDATE users SET coaching_style = 'supportive' WHERE coaching_style IS NULL;
UPDATE users SET streak_count = 0 WHERE streak_count IS NULL;
