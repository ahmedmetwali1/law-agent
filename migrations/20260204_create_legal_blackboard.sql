-- Migration: Create legal_blackboard table for General Counsel State Management
-- Date: 2026-02-04
-- Description: Stores the versioned state of legal cases handled by the AI agents.

CREATE TABLE IF NOT EXISTS legal_blackboard (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES ai_chat_sessions(id) ON DELETE CASCADE,
    version INTEGER NOT NULL DEFAULT 1,
    parent_id UUID REFERENCES legal_blackboard(id), -- Self-reference for version tree
    
    -- Agent-Specific Data Segments (JSONB for flexibility)
    facts_snapshot JSONB,       -- Investigator's Truth
    research_data JSONB,        -- Researcher's Findings
    debate_strategy JSONB,      -- Council's Strategy
    drafting_plan JSONB,        -- Drafter's Outline
    
    final_output TEXT,          -- The final compiled artifact
    workflow_status JSONB,      -- Flags for coordination (e.g. {"investigator": "DONE"})
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indices for Performance
CREATE INDEX IF NOT EXISTS idx_legal_blackboard_session_id ON legal_blackboard(session_id);
CREATE INDEX IF NOT EXISTS idx_legal_blackboard_version ON legal_blackboard(session_id, version DESC);

-- Enable RLS (Security Best Practice)
ALTER TABLE legal_blackboard ENABLE ROW LEVEL SECURITY;

-- Note: RLS Policies should match session ownership.
-- Example Policy (To be adjusted based on specific auth setup):
-- CREATE POLICY "Users can view their own case states" ON legal_blackboard
-- FOR ALL USING (
--   session_id IN (SELECT id FROM ai_chat_sessions WHERE lawyer_id = auth.uid())
-- );
