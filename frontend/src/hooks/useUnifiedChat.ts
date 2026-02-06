import { useState, useEffect, useCallback, useRef } from 'react';
import { toast } from 'sonner';
import { apiClient } from '../api/client';
import { useAuth } from '../contexts/AuthContext';
import { deduplicateMessages, markAsOptimistic } from '../utils/messageDedup';
import { ChatMessage, ChatSession, ChatMode, SendMessageOptions, StreamEvent } from '../types/chat';
import { useChatStore } from '../stores/chatStore';

const MAX_BUFFER_SIZE = 1024 * 1024; // 1MB
const MAX_RECONNECT_ATTEMPTS = 3;
const CONNECTION_TIMEOUT = 300000; // 5 minutes

/**
 * ✅ FIX: Helper لاستخراج thought tags بشكل آمن
 */
function parseMessageContent(msg: any): ChatMessage {
    if (!msg) {
        return {
            id: `err-${Date.now()}`,
            role: 'system',
            content: '',
            created_at: new Date().toISOString()
        } as ChatMessage;
    }

    const rawContent = msg.content || "";
    let cleanContent = rawContent;
    let reasoning = "";

    try {
        const match = rawContent.match(/<thought>([\s\S]*?)<\/thought>/);
        if (match) {
            reasoning = match[1].trim();
            cleanContent = rawContent.replace(/<thought>[\s\S]*?<\/thought>/g, '').trim();
        }
    } catch (error) {
        console.error('Error parsing message content:', error);
    }

    return {
        ...msg,
        content: cleanContent,
        reasoning: reasoning || undefined
    };
}

export function useUnifiedChat(initialSessionId: string | null = null, sessionType: 'sidebar' | 'main' | 'n8n' = 'main') {
    const { getEffectiveLawyerId } = useAuth();
    // ✅ Bridge: Access Global Store
    const store = useChatStore();

    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [sessions, setSessions] = useState<ChatSession[]>([]);
    const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [isThinking, setIsThinking] = useState(false);
    const [isSending, setIsSending] = useState(false);
    const [progressStatus, setProgressStatus] = useState<string | null>(null);
    const [reconnectAttempts, setReconnectAttempts] = useState(0);

    // ✅ FIX: Refs لمنع Race Conditions
    const sendingRef = useRef(false);
    const isMounted = useRef(false);
    const initializationDone = useRef(false);
    const abortControllerRef = useRef<AbortController | null>(null);

    // ✅ FIX: Track mounted state
    useEffect(() => {
        isMounted.current = true;

        return () => {
            isMounted.current = false;
            // Cancel any pending requests
            if (abortControllerRef.current) {
                abortControllerRef.current.abort();
            }
        };
    }, []);

    /**
     * ✅ FIX: Load sessions list بشكل آمن
     */
    const loadSessionsList = useCallback(async () => {
        try {
            const data = await apiClient.get<ChatSession[]>('/api/chat/sessions');
            if (isMounted.current) {
                setSessions(data || []);
            }
        } catch (error) {
            console.error('Error loading sessions list:', error);
            if (isMounted.current) {
                toast.error('فشل في تحميل قائمة الجلسات');
            }
        }
    }, []);

    /**
     * ✅ FIX: Load messages بشكل آمن
     */
    const loadMessages = useCallback(async (sessionId: string) => {
        if (!sessionId) {
            console.warn('Cannot load messages: sessionId is empty');
            return;
        }

        try {
            const data = await apiClient.get<any[]>(`/api/chat/sessions/${sessionId}/messages`);

            if (!isMounted.current) return;

            const parsedData = (data || []).map(parseMessageContent);
            setMessages((existing) => {
                // If we are loading for a new session (detected by check or if existing is empty), 
                // we might want to replace. But here we rely on the caller clearing first.
                // However, deduplication is good for pagination.
                return deduplicateMessages(existing, parsedData);
            });
        } catch (error: any) {
            console.error('Error loading messages:', error);
            if (isMounted.current) {
                toast.error('فشل تحميل الرسائل');
            }
        }
    }, []);

    /**
     * ✅ FIX: Create new session بشكل آمن
     */
    const createNewSession = useCallback(async (title = 'محادثة جديدة') => {
        try {
            const lawyerId = getEffectiveLawyerId();

            if (!lawyerId) {
                throw new Error('يجب تسجيل الدخول أولاً');
            }

            const newSession = await apiClient.post<ChatSession>('/api/chat/sessions', {
                title,
                session_type: sessionType
            });

            if (!isMounted.current) return null;

            setCurrentSession(newSession);
            setMessages([]);

            return newSession;
        } catch (error: any) {
            console.error('Error creating session:', error);
            if (isMounted.current) {
                toast.error(error.message || 'فشل في إنشاء جلسة جديدة');
            }
            throw error;
        }
    }, [getEffectiveLawyerId, sessionType]);

    /**
     * ✅ FIX: Initialize بدون race conditions
     */
    useEffect(() => {
        if (initializationDone.current) return;

        const initialize = async () => {
            if (!isMounted.current) return;

            try {
                setIsLoading(true);
                initializationDone.current = true;

                await loadSessionsList();

                if (!isMounted.current) return;

                if (initialSessionId) {
                    const session = await apiClient.get<ChatSession>(`/api/chat/sessions/${initialSessionId}`);

                    if (!isMounted.current) return;

                    setCurrentSession(session);
                    await loadMessages(initialSessionId);
                } else if (sessionType === 'sidebar') {
                    // Sidebar Only shows sidebar chats
                    const sessions = await apiClient.get<ChatSession[]>('/api/chat/sessions?session_type=sidebar');

                    if (!isMounted.current) return;

                    if (sessions && sessions.length > 0) {
                        setCurrentSession(sessions[0]);
                        await loadMessages(sessions[0].id);
                    } else {
                        await createNewSession('محادثة جانبية');
                    }
                } else {
                    // Main Mode: Fetch all (default behavior of loadSessionsList which calls /sessions without params)
                    // Does not auto-select a session, leaves it to user or creates new empty state
                }
            } catch (error: any) {
                console.error('Error initializing chat:', error);
                if (isMounted.current) {
                    toast.error('فشل في تهيئة المحادثة');
                }
            } finally {
                if (isMounted.current) {
                    setIsLoading(false);
                }
            }
        };

        initialize();
    }, []); // Empty deps - run once

    /**
     * ✅ FIX: React to session ID changes (Navigation/Sidebar Click)
     */
    useEffect(() => {
        // Prevent running if not mounted or same session
        if (!initialSessionId || currentSession?.id === initialSessionId) return;

        const switchSession = async () => {
            if (!isMounted.current) return;

            try {
                // Don't set loading true if we are just verifying, 
                // but here we are fetching new data so maybe brief loading?
                // Better UX: keep old messages until new ones load? Or clear?
                // Let's clear to prevent confusion and merging issues
                setMessages([]);
                setIsLoading(true);

                // Fetch full session details
                const session = await apiClient.get<ChatSession>(`/api/chat/sessions/${initialSessionId}`);

                if (!isMounted.current) return;

                setCurrentSession(session);
                await loadMessages(initialSessionId);

            } catch (error) {
                console.error('Error switching session:', error);
                if (isMounted.current) {
                    toast.error('فشل في تحميل الجلسة المختارة');
                }
            } finally {
                if (isMounted.current) {
                    setIsLoading(false);
                }
            }
        };

        switchSession();
    }, [initialSessionId]); // ✅ Depend on initialSessionId


    /**
     * ✅ FIX: Handle streaming response بشكل آمن وكامل (Viva Protocol)
     */
    const handleStreamingResponse = async (
        content: string,
        sessionId: string,
        userTempId: string,
        mode: ChatMode,
        context_summary?: string
    ) => {
        const aiTempId = `ai-stream-${Date.now()}`;
        let aiContentAccumulator = "";

        // ✅ Bridge: Start Thinking
        useChatStore.setState(s => ({
            currentActivity: {
                stage: 'ROUTING',
                actor: 'النظام',
                action: 'جاري بدء المعالجة...',
                isThinking: true
            }
        }));

        // ✅ GENIUS TWEAK: Buffer for split chunks
        let buffer = "";

        try {
            const token = localStorage.getItem('auth_token') || localStorage.getItem('access_token');

            if (!token) {
                throw new Error('غير مصرح - يرجى تسجيل الدخول');
            }

            // ✅ Create abort controller for timeout
            const controller = new AbortController();
            abortControllerRef.current = controller;

            const timeoutId = setTimeout(() => {
                controller.abort();
            }, CONNECTION_TIMEOUT);

            const response = await fetch(
                `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/chat/stream`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`,
                    },
                    body: JSON.stringify({
                        session_id: sessionId,
                        message: content,
                        mode,
                        context_summary
                    }),
                    signal: controller.signal
                }
            );

            clearTimeout(timeoutId);

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`خطأ في الخادم: ${response.status} - ${errorText}`);
            }

            if (!response.body) {
                throw new Error("لا يوجد body في الاستجابة");
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            while (true) {
                if (!isMounted.current) {
                    reader.cancel();
                    break;
                }

                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                buffer += chunk;

                // ✅ GENIUS TWEAK: Split only on event boundaries
                const parts = buffer.split('\n\n');

                // Keep the last part in buffer (it might be incomplete)
                buffer = parts.pop() || "";

                for (const part of parts) {
                    const cleanPart = part.trim();
                    if (!cleanPart) continue;

                    if (!cleanPart.startsWith('data: ')) {
                        // Skip noise or keep processing if it's a weird format?
                        // Ideally we only care about data: lines
                        continue;
                    }

                    const dataStr = cleanPart.replace('data: ', '').trim();

                    if (dataStr === '[DONE]') {
                        if (isMounted.current) {
                            setIsThinking(false);
                            // Ensure stage is marked complete
                            setProgressStatus(null);
                        }
                        continue;
                    }

                    try {
                        const event = JSON.parse(dataStr) as StreamEvent;

                        // ✅ Protocol Validation
                        if (!event || !event.type) continue;
                        if (!isMounted.current) continue;

                        switch (event.type) {
                            case 'stage_change': {
                                // ✅ Bridge: Update Global Store for Stepper
                                if (event.stage) {
                                    useChatStore.setState(s => ({
                                        currentActivity: { ...s.currentActivity, stage: event.stage as any }
                                    }));
                                }
                                break;
                            }
                            case 'step_update': {
                                if (event.payload) {
                                    // Dispatch to "Status Bar"
                                    const statusMsg = event.payload.message || event.payload.status;
                                    setProgressStatus(statusMsg);

                                    // ✅ Bridge: Update Golden Box
                                    useChatStore.setState(s => ({
                                        currentActivity: {
                                            ...s.currentActivity,
                                            actor: event.payload.actor || s.currentActivity.actor,
                                            action: statusMsg,
                                            isThinking: true
                                        }
                                    }));
                                }
                                break;
                            }

                            case 'reasoning_chunk': {
                                // Dispatch to "Sidebar" (Reasoning)

                                setMessages(prev => {
                                    const exists = prev.find(m => m.id === aiTempId);
                                    if (exists) {
                                        return prev.map(m => m.id === aiTempId ? {
                                            ...m,
                                            reasoning: (m.reasoning || "") + event.content
                                        } : m);
                                    } else {
                                        // Create early placeholder
                                        return [...prev, {
                                            id: aiTempId,
                                            session_id: sessionId,
                                            role: 'assistant',
                                            content: "", // No content yet
                                            reasoning: event.content,
                                            created_at: new Date().toISOString(),
                                            metadata: { streamed: true }
                                        }];
                                    }
                                });
                                break;
                            }

                            case 'token': {
                                // The Public Content
                                aiContentAccumulator += event.content;

                                // ✅ Bridge: Switch to VERDICT if getting tokens (implying thought done)
                                useChatStore.setState(s => {
                                    if (s.currentActivity.stage !== 'VERDICT' && s.currentActivity.stage !== 'IDLE') {
                                        return {
                                            currentActivity: {
                                                ...s.currentActivity,
                                                stage: 'VERDICT',
                                                action: 'جاري كتابة الرد...',
                                                isThinking: false
                                            }
                                        };
                                    }
                                    return s;
                                });

                                setMessages(prev => {
                                    const exists = prev.find(m => m.id === aiTempId);
                                    if (exists) {
                                        return prev.map(m => m.id === aiTempId ? {
                                            ...m,
                                            content: aiContentAccumulator
                                        } : m);
                                    } else {
                                        return [...prev, {
                                            id: aiTempId,
                                            session_id: sessionId,
                                            role: 'assistant',
                                            content: aiContentAccumulator,
                                            created_at: new Date().toISOString(),
                                            metadata: { streamed: true }
                                        }];
                                    }
                                });
                                break;
                            }

                            case 'user_message_saved': {
                                // Update temp ID to real? No, just unmark optimistic
                                setMessages(prev => prev.map(m =>
                                    m.id === userTempId
                                        ? { ...m, isOptimistic: false }
                                        : m
                                ));
                                break;
                            }

                            case 'ai_message_saved': {
                                // Finalize
                                setMessages(prev => prev.map(m =>
                                    m.id === aiTempId
                                        ? { ...m, isOptimistic: false }
                                        : m
                                ));
                                break;
                            }

                            case 'error': {
                                toast.error(event.content);
                                break;
                            }
                        }

                    } catch (parseError) {
                        console.warn('⚠️ Malformed JSON in chunk (buffered):', dataStr, parseError);
                        // Continue processing next chunk
                    }
                }
            }

            // ✅ Reset reconnect attempts on success
            setReconnectAttempts(0);

        } catch (error: any) {
            console.error('Streaming error:', error);

            if (!isMounted.current) return;

            // ✅ FIX: Handle different error types
            if (error.name === 'AbortError') {
                toast.error('انتهت مهلة الاتصال');
            } else if (error.name === 'TypeError' && !navigator.onLine) {
                // Network error - attempt reconnect
                if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                    toast.info(`محاولة إعادة الاتصال (${reconnectAttempts + 1}/${MAX_RECONNECT_ATTEMPTS})`);

                    await new Promise(resolve => setTimeout(resolve, 2000));

                    if (!isMounted.current) return;

                    setReconnectAttempts(prev => prev + 1);

                    // Retry
                    return await handleStreamingResponse(content, sessionId, userTempId, mode, context_summary);
                } else {
                    toast.error('فشلت جميع محاولات إعادة الاتصال');
                    setReconnectAttempts(0);
                }
            } else {
                toast.error(error.message || 'حدث خطأ أثناء استقبال الرد');
            }
        } finally {
            if (isMounted.current) {
                setIsThinking(false);
                setIsSending(false);
                setProgressStatus(null);

                // ✅ Bridge: Reset Activity
                useChatStore.setState(s => ({
                    currentActivity: { ...s.currentActivity, isThinking: false, action: 'Complete' }
                }));
            }
            abortControllerRef.current = null;
        }
    };

    /**
     * ✅ FIX: Handle simple POST response
     */
    const handleSimpleResponse = async (
        content: string,
        sessionId: string,
        userTempId: string,
        mode: ChatMode,
        context_summary?: string
    ) => {
        try {
            const response = await apiClient.post<any>('/api/chat/send', {
                session_id: sessionId,
                message: content,
                mode,
                context_summary
            });

            if (!isMounted.current) return;

            const userMsg = parseMessageContent(response.user_message);
            const aiMsg = parseMessageContent(response.ai_message);

            setMessages(prev => {
                const filtered = prev.filter(m => m.id !== userTempId);
                return deduplicateMessages(filtered, [userMsg, aiMsg]);
            });

            if (response.suggested_title && messages.length <= 2) {
                setCurrentSession(prev => prev ? { ...prev, title: response.suggested_title } : null);
            }
        } catch (error: any) {
            console.error('Send error:', error);

            if (isMounted.current) {
                toast.error(error.message || 'فشل إرسال الرسالة');

                // Mark message as failed
                setMessages(prev => prev.map(m =>
                    m.id === userTempId
                        ? { ...m, metadata: { ...m.metadata, failed: true } }
                        : m
                ));
            }
        } finally {
            if (isMounted.current) {
                setIsThinking(false);
                setIsSending(false);
                setProgressStatus(null);
            }
        }
    };

    /**
     * ✅ FIX: Send message مع معالجة كاملة
     */
    const sendMessage = async (content: string, options: SendMessageOptions = {}) => {
        const { mode = "auto", context_summary, stream = false } = options;

        // ✅ Validation
        if (!content.trim()) {
            toast.warning('الرجاء كتابة رسالة');
            return;
        }

        if (sendingRef.current) {
            console.warn('Message blocked: already sending');
            return;
        }

        if (!navigator.onLine) {
            toast.error('لا يوجد اتصال بالإنترنت');
            return;
        }

        sendingRef.current = true;
        setIsSending(true);
        setIsThinking(true);
        setProgressStatus("جاري الاتصال...");

        const tempId = `temp-${Date.now()}`;

        try {
            // Ensure we have a session
            let session = currentSession;
            if (!session) {
                try {
                    session = await createNewSession();
                    if (!session) {
                        throw new Error('فشل في إنشاء جلسة');
                    }
                } catch (e: any) {
                    throw new Error(e.message || 'فشل في إنشاء جلسة');
                }
            }

            // ✅ Optimistic User Message
            const optimisticMsg = markAsOptimistic({
                id: tempId,
                session_id: session.id,
                role: 'user',
                content: content,
                created_at: new Date().toISOString()
            }) as ChatMessage;

            setMessages(prev => [...prev, optimisticMsg]);

            // Choose streaming or simple
            if (stream) {
                await handleStreamingResponse(content, session.id, tempId, mode, context_summary);
            } else {
                await handleSimpleResponse(content, session.id, tempId, mode, context_summary);
            }
        } catch (error: any) {
            console.error('Send message error:', error);

            if (isMounted.current) {
                toast.error(error.message || 'فشل في إرسال الرسالة');

                // Mark as failed
                setMessages(prev => prev.map(m =>
                    m.id === tempId
                        ? { ...m, metadata: { ...m.metadata, failed: true, error: error.message } }
                        : m
                ));
            }
        } finally {
            sendingRef.current = false;

            if (isMounted.current) {
                setIsSending(false);
                setIsThinking(false);
                setProgressStatus(null);
            }
        }
    };

    /**
     * ✅ Clear and reset
     */
    const clearSession = useCallback(async () => {
        setMessages([]);
        setCurrentSession(null);

        // Reset store
        store.resetActivity();

        if (sessionType === 'sidebar') {
            await createNewSession('محادثة جانبية');
        }
    }, [sessionType, createNewSession]);

    return {
        messages,
        sessions,
        currentSession,
        isLoading,
        isThinking,
        isSending,
        sendMessage,
        clearSession,
        loadMessages,
        loadSessionsList,
        setCurrentSession,
        progressStatus
    };
}
