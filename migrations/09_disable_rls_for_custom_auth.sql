-- Migration: Disable RLS for Custom Authentication
-- Description: Since we use custom JWT authentication (not Supabase Auth),
--              we need to disable RLS or modify policies to work with custom auth

-- ============================================
-- Option 1: Disable RLS completely (Quick Fix)
-- ============================================
ALTER TABLE ai_chat_sessions DISABLE ROW LEVEL SECURITY;
ALTER TABLE ai_chat_messages DISABLE ROW LEVEL SECURITY;

-- ============================================
-- Drop existing policies (they use auth.uid() which won't work)
-- ============================================
DROP POLICY IF EXISTS "Lawyers can view own sessions" ON ai_chat_sessions;
DROP POLICY IF EXISTS "Lawyers can create own sessions" ON ai_chat_sessions;
DROP POLICY IF EXISTS "Lawyers can update own sessions" ON ai_chat_sessions;
DROP POLICY IF EXISTS "Lawyers can delete own sessions" ON ai_chat_sessions;

DROP POLICY IF EXISTS "Lawyers can view messages in own sessions" ON ai_chat_messages;
DROP POLICY IF EXISTS "Lawyers can create messages in own sessions" ON ai_chat_messages;
DROP POLICY IF EXISTS "Lawyers can delete messages in own sessions" ON ai_chat_messages;

-- ============================================
-- Grant permissions to authenticated users
-- ============================================
-- Note: With RLS disabled, access control should be handled at the application level
-- or via backend API endpoints

COMMENT ON TABLE ai_chat_sessions IS 'Stores AI chat sessions - RLS disabled, access controlled by backend';
COMMENT ON TABLE ai_chat_messages IS 'Stores chat messages - RLS disabled, access controlled by backend';
