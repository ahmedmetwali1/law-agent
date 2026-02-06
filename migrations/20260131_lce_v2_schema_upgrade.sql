-- LCE v2.0 Upgrade
-- Adds support for 'Reasoning Chains' (Structured JSON) and 'Step Types' (Monologue vs Vote)

ALTER TABLE agent_deliberations 
ADD COLUMN IF NOT EXISTS step_type VARCHAR(50) DEFAULT 'opinion', -- 'monologue', 'opinion', 'vote'
ADD COLUMN IF NOT EXISTS reasoning_chain JSONB DEFAULT '{}'::JSONB; -- Structured steps: [{premise: "...", conclusion: "..."}]

CREATE INDEX IF NOT EXISTS idx_deliberations_step_type ON agent_deliberations(step_type);
