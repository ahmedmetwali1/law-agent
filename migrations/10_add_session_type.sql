-- Migration: Add session_type to ai_chat_sessions
-- Description: Adds session_type column to distinguish between main and sidebar chats

-- Add session_type column
ALTER TABLE ai_chat_sessions 
ADD COLUMN IF NOT EXISTS session_type VARCHAR(20) DEFAULT 'main' 
CHECK (session_type IN ('main', 'sidebar'));

-- Create index for faster filtering
CREATE INDEX IF NOT EXISTS idx_ai_chat_sessions_type ON ai_chat_sessions(session_type);

-- Update existing sessions to 'main' type
UPDATE ai_chat_sessions SET session_type = 'main' WHERE session_type IS NULL;

COMMENT ON COLUMN ai_chat_sessions.session_type IS 'Type of chat session: main (ChatPage) or sidebar (AINexus)';
