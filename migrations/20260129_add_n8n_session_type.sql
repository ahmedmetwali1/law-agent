-- Add 'n8n' to ai_chat_sessions session_type check constraint

ALTER TABLE ai_chat_sessions 
DROP CONSTRAINT IF EXISTS ai_chat_sessions_session_type_check;

ALTER TABLE ai_chat_sessions 
ADD CONSTRAINT ai_chat_sessions_session_type_check 
CHECK (session_type IN ('main', 'sidebar', 'n8n', 'admin_assistant', 'legal_researcher'));
