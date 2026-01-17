-- Migration: AI Chat Sessions and Messages
-- Description: Creates tables for persistent AI chat sessions with messages

-- ============================================
-- Table: ai_chat_sessions
-- ============================================
CREATE TABLE IF NOT EXISTS ai_chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lawyer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_message_at TIMESTAMP,
    is_pinned BOOLEAN DEFAULT FALSE,
    message_count INTEGER DEFAULT 0,
    session_type VARCHAR(20) DEFAULT 'main' CHECK (session_type IN ('main', 'sidebar'))
);

-- Indexes for performance
CREATE INDEX idx_ai_chat_sessions_lawyer_id ON ai_chat_sessions(lawyer_id);
CREATE INDEX idx_ai_chat_sessions_updated_at ON ai_chat_sessions(updated_at DESC);
CREATE INDEX idx_ai_chat_sessions_last_message ON ai_chat_sessions(last_message_at DESC);

-- ============================================
-- Table: ai_chat_messages
-- ============================================
CREATE TABLE IF NOT EXISTS ai_chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES ai_chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Indexes for performance
CREATE INDEX idx_ai_chat_messages_session_id ON ai_chat_messages(session_id);
CREATE INDEX idx_ai_chat_messages_created_at ON ai_chat_messages(created_at);

-- ============================================
-- Function: Update session timestamp on new message
-- ============================================
CREATE OR REPLACE FUNCTION update_session_on_message()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE ai_chat_sessions
    SET 
        last_message_at = NEW.created_at,
        updated_at = NEW.created_at,
        message_count = message_count + 1
    WHERE id = NEW.session_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update session
CREATE TRIGGER trigger_update_session_on_message
    AFTER INSERT ON ai_chat_messages
    FOR EACH ROW
    EXECUTE FUNCTION update_session_on_message();

-- ============================================
-- Row Level Security Policies
-- ============================================

-- Enable RLS
ALTER TABLE ai_chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_chat_messages ENABLE ROW LEVEL SECURITY;

-- ai_chat_sessions policies
CREATE POLICY "Lawyers can view own sessions"
    ON ai_chat_sessions FOR SELECT
    USING (lawyer_id = auth.uid());

CREATE POLICY "Lawyers can create own sessions"
    ON ai_chat_sessions FOR INSERT
    WITH CHECK (lawyer_id = auth.uid());

CREATE POLICY "Lawyers can update own sessions"
    ON ai_chat_sessions FOR UPDATE
    USING (lawyer_id = auth.uid());

CREATE POLICY "Lawyers can delete own sessions"
    ON ai_chat_sessions FOR DELETE
    USING (lawyer_id = auth.uid());

-- ai_chat_messages policies
CREATE POLICY "Lawyers can view messages in own sessions"
    ON ai_chat_messages FOR SELECT
    USING (
        session_id IN (
            SELECT id FROM ai_chat_sessions WHERE lawyer_id = auth.uid()
        )
    );

CREATE POLICY "Lawyers can create messages in own sessions"
    ON ai_chat_messages FOR INSERT
    WITH CHECK (
        session_id IN (
            SELECT id FROM ai_chat_sessions WHERE lawyer_id = auth.uid()
        )
    );

CREATE POLICY "Lawyers can delete messages in own sessions"
    ON ai_chat_messages FOR DELETE
    USING (
        session_id IN (
            SELECT id FROM ai_chat_sessions WHERE lawyer_id = auth.uid()
        )
    );

-- ============================================
-- Comments
-- ============================================
COMMENT ON TABLE ai_chat_sessions IS 'Stores AI chat sessions for lawyers';
COMMENT ON TABLE ai_chat_messages IS 'Stores individual messages within chat sessions';
COMMENT ON COLUMN ai_chat_sessions.title IS 'User-defined name for the chat session';
COMMENT ON COLUMN ai_chat_sessions.is_pinned IS 'Whether the session is pinned to top of list';
COMMENT ON COLUMN ai_chat_messages.role IS 'Message sender: user, assistant, or system';
COMMENT ON COLUMN ai_chat_messages.metadata IS 'Additional metadata like model used, tokens, etc';
