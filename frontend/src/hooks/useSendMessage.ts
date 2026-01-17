import { useCallback } from 'react'
import { toast } from 'sonner'
import { supabase } from '../supabaseClient'

interface SendMessageParams {
    message: string
    sessionId: string | null
    getEffectiveLawyerId: () => string | null
    onSuccess: (data: {
        userMsg: any
        aiMsg: any
        currentSession: any
    }) => void
    onError?: (error: Error) => void
}

/**
 * Custom hook لإزالة تكرار كود إرسال الرسائل
 * يدعم النص العادي والصوت
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
            let currentSession: any = null

            // Auto-create session if needed
            if (!sessionId) {
                const lawyerId = getEffectiveLawyerId()
                if (!lawyerId) {
                    throw new Error('يجب تسجيل الدخول أولاً')
                }

                const { data: newSession, error: sessionError } = await supabase
                    .from('ai_chat_sessions')
                    .insert({
                        lawyer_id: lawyerId,
                        title: 'محادثة جديدة...'
                    })
                    .select()
                    .single()

                if (sessionError) throw sessionError
                currentSession = newSession
            } else {
                // Load existing session
                const { data, error } = await supabase
                    .from('ai_chat_sessions')
                    .select('*')
                    .eq('id', sessionId)
                    .single()

                if (error) throw error
                currentSession = data
            }

            if (!currentSession) {
                throw new Error('فشل في إنشاء/تحميل الجلسة')
            }

            // Save user message
            const { data: userMsg, error: userError } = await supabase
                .from('ai_chat_messages')
                .insert({
                    session_id: currentSession.id,
                    role: 'user',
                    content: message
                })
                .select()
                .single()

            if (userError) throw userError

            // Check if first message (for title generation)
            const { count } = await supabase
                .from('ai_chat_messages')
                .select('*', { count: 'exact', head: true })
                .eq('session_id', currentSession.id)

            const isFirstMessage = (count || 0) <= 1

            // Call AI backend
            const token = localStorage.getItem('access_token')
            const response = await fetch('http://localhost:8000/api/ai/chat', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message,
                    session_id: currentSession.id,
                    generate_title: isFirstMessage
                })
            })

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}))
                throw new Error(errorData.detail || 'فشل طلب الذكاء الاصطناعي')
            }

            const aiResponse = await response.json()

            // Save AI response
            const { data: aiMsg, error: aiError } = await supabase
                .from('ai_chat_messages')
                .insert({
                    session_id: currentSession.id,
                    role: 'assistant',
                    content: aiResponse.message || aiResponse.response,
                    metadata: aiResponse.metadata || {}
                })
                .select()
                .single()

            if (aiError) throw aiError

            // Update session title if generated
            if (isFirstMessage && aiResponse.suggested_title) {
                await supabase
                    .from('ai_chat_sessions')
                    .update({ title: aiResponse.suggested_title })
                    .eq('id', currentSession.id)

                currentSession.title = aiResponse.suggested_title
            }

            // Success callback
            onSuccess({
                userMsg,
                aiMsg,
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

