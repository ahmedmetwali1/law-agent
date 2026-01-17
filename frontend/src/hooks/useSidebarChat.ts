import { useState, useEffect, useCallback } from 'react'
import { getAuthenticatedSupabase } from '../supabaseClient'
import { useAuth } from '../contexts/AuthContext'

interface SidebarMessage {
    id: string
    session_id: string
    role: 'user' | 'assistant'
    content: string
    created_at: string
}

interface SidebarSession {
    id: string
    title: string
    created_at: string
}

/**
 * Hook for managing AINexus sidebar chat with database persistence
 * Replaces useChatStore (Zustand) with Supabase storage
 */
export function useSidebarChat() {
    const { getEffectiveLawyerId } = useAuth()
    const supabase = getAuthenticatedSupabase()

    const [currentSession, setCurrentSession] = useState<SidebarSession | null>(null)
    const [messages, setMessages] = useState<SidebarMessage[]>([])
    const [isLoading, setIsLoading] = useState(false)
    const [isSending, setIsSending] = useState(false)

    /**
     * Load or create sidebar session on mount
     */
    useEffect(() => {
        loadOrCreateSession()
    }, [])

    /**
     * Load latest sidebar session or create new one
     */
    const loadOrCreateSession = async () => {
        try {
            setIsLoading(true)
            const lawyerId = getEffectiveLawyerId()
            if (!lawyerId) return

            // Try to load latest sidebar session
            const { data: sessions, error } = await supabase
                .from('ai_chat_sessions')
                .select('id, title, created_at')
                .eq('lawyer_id', lawyerId)
                .eq('session_type', 'sidebar')
                .order('created_at', { ascending: false })
                .limit(1)

            if (error) throw error

            if (sessions && sessions.length > 0) {
                // Load existing session
                const session = sessions[0]
                setCurrentSession(session)
                await loadMessages(session.id)
            } else {
                // Create new session
                await createNewSession()
            }
        } catch (error) {
            console.error('Error loading sidebar session:', error)
        } finally {
            setIsLoading(false)
        }
    }

    /**
     * Load messages for a session
     */
    const loadMessages = async (sessionId: string) => {
        try {
            const { data, error } = await supabase
                .from('ai_chat_messages')
                .select('*')
                .eq('session_id', sessionId)
                .order('created_at', { ascending: true })

            if (error) throw error
            setMessages(data || [])
        } catch (error) {
            console.error('Error loading messages:', error)
        }
    }

    /**
     * Create new sidebar session
     */
    const createNewSession = async () => {
        try {
            const lawyerId = getEffectiveLawyerId()
            if (!lawyerId) {
                throw new Error('يجب تسجيل الدخول أولاً')
            }

            const { data: newSession, error } = await supabase
                .from('ai_chat_sessions')
                .insert({
                    lawyer_id: lawyerId,
                    title: 'محادثة جانبية',
                    session_type: 'sidebar'
                })
                .select('id, title, created_at')
                .single()

            if (error) throw error

            setCurrentSession(newSession)
            setMessages([])
            return newSession
        } catch (error) {
            console.error('Error creating session:', error)
            throw error
        }
    }

    /**
     * Send message and get AI response
     */
    const sendMessage = async (content: string) => {
        if (!content.trim() || isSending) return

        try {
            setIsSending(true)

            // Ensure we have a session
            let session = currentSession
            if (!session) {
                session = await createNewSession()
            }

            if (!session) {
                throw new Error('Failed to create session')
            }

            // Add user message to UI immediately
            const userMessage: SidebarMessage = {
                id: crypto.randomUUID(),
                session_id: session.id,
                role: 'user',
                content,
                created_at: new Date().toISOString()
            }
            setMessages(prev => [...prev, userMessage])

            // Save user message to database
            const { data: savedUserMsg, error: userError } = await supabase
                .from('ai_chat_messages')
                .insert({
                    session_id: session.id,
                    role: 'user',
                    content
                })
                .select()
                .single()

            if (userError) throw userError

            // Update UI with saved message
            setMessages(prev => prev.map(m =>
                m.id === userMessage.id ? savedUserMsg : m
            ))

            // Call AI backend
            const token = localStorage.getItem('access_token')
            const response = await fetch('http://localhost:8000/api/ai/chat', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: content,
                    session_id: session.id,
                    generate_title: messages.length === 0, // First message
                    lawyer_id: getEffectiveLawyerId()
                })
            })

            if (!response.ok) {
                throw new Error('فشل طلب الذكاء الاصطناعي')
            }

            const aiResponse = await response.json()

            // Save AI message to database
            const { data: aiMsg, error: aiError } = await supabase
                .from('ai_chat_messages')
                .insert({
                    session_id: session.id,
                    role: 'assistant',
                    content: aiResponse.message,
                    metadata: aiResponse.metadata || {}
                })
                .select()
                .single()

            if (aiError) throw aiError

            // Add AI message to UI
            setMessages(prev => [...prev, aiMsg])

            // Update session title if suggested
            if (aiResponse.suggested_title && messages.length === 0) {
                await supabase
                    .from('ai_chat_sessions')
                    .update({ title: aiResponse.suggested_title })
                    .eq('id', session.id)

                setCurrentSession(prev => prev ? {
                    ...prev,
                    title: aiResponse.suggested_title
                } : null)
            }

        } catch (error: any) {
            console.error('Error sending message:', error)
            throw error
        } finally {
            setIsSending(false)
        }
    }

    /**
     * Clear current session and create new one
     */
    const clearSession = async () => {
        try {
            setMessages([])
            await createNewSession()
        } catch (error) {
            console.error('Error clearing session:', error)
            throw error
        }
    }

    return {
        messages,
        currentSession,
        isLoading,
        isSending,
        sendMessage,
        clearSession
    }
}
