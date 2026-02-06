export interface ChatMessage {
    id: string;
    session_id: string;
    role: 'user' | 'assistant' | 'tool' | 'system';
    content: string;
    reasoning?: string;
    created_at: string;
    metadata?: any;
    isOptimistic?: boolean;
    isNew?: boolean;
}

export interface ChatSession {
    id: string;
    title: string;
    created_at: string;
    session_type?: 'sidebar' | 'main' | 'n8n';
}

export type ChatMode = "auto" | "admin_assistant" | "legal_researcher" | "n8n";

export interface SendMessageOptions {
    mode?: ChatMode;
    context_summary?: string;
    stream?: boolean;
}

export interface StreamEvent {
    type: 'token' | 'tool_start' | 'user_message_saved' | 'ai_message_saved' | 'error' | 'status' | 'step_update' | 'reasoning_chunk' | 'stage_change';
    content?: string;
    message?: ChatMessage;
    name?: string;
    detail?: string;
    payload?: any;
    stage?: string;
}
