import { useCallback } from 'react'
import { toast } from 'sonner'
import { apiClient } from '../api/client'

interface ChatSession {
    id: string
    lawyer_id: string
    title: string
    created_at: string
    updated_at: string
    last_message_at: string | null
    is_pinned: boolean
    message_count: number
}

interface ChatMessage {
    id: string
    session_id: string
    role: 'user' | 'assistant' | 'system'
    content: string
    created_at: string
    metadata?: any
}

interface SendMessageParams {
    message: string
    sessionId: string | null
    getEffectiveLawyerId: () => string | null
    onSuccess: (data: {
        userMsg: ChatMessage
        aiMsg: ChatMessage
        currentSession: ChatSession
    }) => void
    onError?: (error: Error) => void
}

/**
 * Custom hook لإزالة تكرار كود إرسال الرسائل
 * ✅ BFF Pattern: يستخدم apiClient بدلاً من supabase مباشرة
 * Backend يتولى: حفظ رسالة المستخدم، استدعاء AI، حفظ رد AI، تحديث العنوان
 */
export function useSendMessage() {
    const sendMessage = useCallback(async ({
        message,
        sessionId,
        getEffectiveLawyerId,
        onSuccess,
        onError
    }: SendMessageParams) => {
        try {
            let currentSession: ChatSession

            // ✅ BFF Pattern: Auto-create session via apiClient
            if (!sessionId) {
                const lawyerId = getEffectiveLawyerId()
                if (!lawyerId) {
                    throw new Error('يجب تسجيل الدخول أولاً')
                }

                currentSession = await apiClient.post<ChatSession>('/api/chat/sessions', {
                    title: 'محادثة جديدة...',
                    session_type: 'sidebar'
                })
            } else {
                // For existing session, we'll get it from the send response
                currentSession = { id: sessionId } as ChatSession
            }

            // ✅ BFF Pattern: Send message via unified endpoint
            // Backend handles: save user msg, call AI, save AI msg, update title
            const result = await apiClient.post<{
                user_message: ChatMessage
                ai_message: ChatMessage
                suggested_title?: string
            }>('/api/chat/send', {
                session_id: currentSession.id,
                content: message,
                generate_title: !sessionId // Generate title for new sessions
            })

            // Update session title if generated
            if (result.suggested_title) {
                currentSession.title = result.suggested_title
            }

            // Success callback
            onSuccess({
                userMsg: result.user_message,
                aiMsg: result.ai_message,
                currentSession
            })

        } catch (error: any) {
            console.error('Send message error:', error)

            if (onError) {
                onError(error)
            } else {
                toast.error(error.message || 'فشل إرسال الرسالة')
            }

            throw error
        }
    }, [])

    return { sendMessage }
}
