-- AI Usage Tracking Table (Aligned with db.md)
CREATE TABLE IF NOT EXISTS ai_usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lawyer_id UUID REFERENCES users(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL, -- Added
    session_id UUID REFERENCES ai_chat_sessions(id) ON DELETE SET NULL,
    request_id UUID, -- Added
    request_type TEXT NOT NULL, -- Matched db.md
    model_name TEXT,
    provider TEXT, -- Added
    words_input INTEGER DEFAULT 0, -- Matched db.md
    words_output INTEGER DEFAULT 0, -- Matched db.md
    total_words INTEGER DEFAULT 0, -- Matched db.md
    cost_calculated NUMERIC(10, 6) DEFAULT 0, -- Added
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- Index for analytics
CREATE INDEX IF NOT EXISTS idx_ai_usage_lawyer ON ai_usage_logs(lawyer_id);
CREATE INDEX IF NOT EXISTS idx_ai_usage_created_at ON ai_usage_logs(created_at);

-- Function to increment subscription usage atomically
CREATE OR REPLACE FUNCTION increment_ai_usage(
    p_lawyer_id UUID,
    p_words INTEGER
) RETURNS VOID AS $$
BEGIN
    UPDATE lawyer_subscriptions
    SET words_used_this_month = COALESCE(words_used_this_month, 0) + p_words,
        updated_at = NOW()
    WHERE lawyer_id = p_lawyer_id;
END;
$$ LANGUAGE plpgsql;
