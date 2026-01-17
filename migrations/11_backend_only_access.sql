-- Migration: Backend-only access for chat tables
-- Description: Revoke anon access, backend handles all authorization

-- Revoke all permissions from anonymous users
REVOKE ALL ON ai_chat_sessions FROM anon;
REVOKE ALL ON ai_chat_messages FROM anon;

-- Grant permissions to authenticated role (if using service role)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ai_chat_sessions TO authenticated;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ai_chat_messages TO authenticated;

-- Add comments
COMMENT ON TABLE ai_chat_sessions IS 'Chat sessions - Backend-only access, authorization handled by API';
COMMENT ON TABLE ai_chat_messages IS 'Chat messages - Backend-only access, authorization handled by API';

-- Note: With this setup, all database access MUST go through backend API
-- Frontend cannot directly access these tables
-- Backend uses service role key for database operations
