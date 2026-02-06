-- Blackboard Pattern Table for Legal Cognitive Engine (LCE v1.0)
-- Stores the thinking process (private) and opinions (public) of agents.

CREATE TABLE IF NOT EXISTS agent_deliberations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES ai_chat_sessions(id) ON DELETE CASCADE,
    round_number INT NOT NULL, -- 1: Opening, 2: Challenge
    agent_role VARCHAR(50) NOT NULL, -- 'strategist', 'auditor', 'challenger', 'pragmatist'
    
    -- Private Memory: The internal monologue/research process (Visible to User/Admin, Hidden from Peers)
    internal_monologue TEXT, 
    
    -- Public Memory: The concise opinion (Visible to Peers and Judge)
    public_opinion TEXT NOT NULL, 
    
    -- Verification Keys: Evidence used (Visible to Challenger/Judge for verification)
    -- Format: [{"doc_id": "uuid", "ref": "Article 80", "quote": "...", "source_id": "...", "sequence_number": 12}]
    cited_evidence JSONB DEFAULT '[]'::JSONB, 
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast retrieval during deliberation rounds
CREATE INDEX idx_agent_deliberations_session_round ON agent_deliberations(session_id, round_number);
