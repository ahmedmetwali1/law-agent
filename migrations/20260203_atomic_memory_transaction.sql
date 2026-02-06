-- Atomic Transaction for Agent Step
-- Prevents data inconsistency between message insertion and session state update

CREATE OR REPLACE FUNCTION atomic_step_transaction(
    p_session_id UUID,
    p_role TEXT,
    p_content TEXT,
    p_metadata JSONB,
    p_agent_state JSONB
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_message_id UUID;
    v_result JSONB;
BEGIN
    -- 1. Insert Message
    INSERT INTO ai_chat_messages (
        session_id,
        role,
        content,
        metadata,
        created_at
    ) VALUES (
        p_session_id,
        p_role,
        p_content,
        p_metadata,
        NOW()
    )
    RETURNING id INTO v_message_id;

    -- 2. Update Session State
    UPDATE ai_chat_sessions
    SET 
        agent_state = p_agent_state,
        last_message_at = NOW()
    WHERE id = p_session_id;

    -- 3. Return Success
    v_result := jsonb_build_object(
        'success', true,
        'message_id', v_message_id
    );

    RETURN v_result;

EXCEPTION WHEN OTHERS THEN
    RAISE EXCEPTION 'Atomic transaction failed: %', SQLERRM;
END;
$$;
