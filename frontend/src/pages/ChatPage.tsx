import { useState, useEffect, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
    Plus, Search, Filter, Send, Sparkles,
    MoreVertical, Trash2, Pin, X, Clock, Mic, MicOff, Loader2
} from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { getAuthenticatedSupabase } from '../supabaseClient'
import { toast } from 'sonner'
import { format } from 'date-fns'
import { arSA } from 'date-fns/locale'
import { useVoiceInput } from '../hooks/useVoiceInput'
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface ChatMessage {
    id: string
    session_id: string
    role: 'user' | 'assistant' | 'system'
    content: string
    created_at: string
    metadata?: any
}

interface ChatSession {
    id: string
    lawyer_id: string
    title: string
    created_at: string
    updated_at: string
    last_message_at: string | null
    is_pinned: boolean
    message_count: number
    messages?: ChatMessage[]
}

export function ChatPage() {
    const { getEffectiveLawyerId } = useAuth()

    // ✅ Use authenticated supabase client for all DB operations
    const supabase = getAuthenticatedSupabase()

    const [sessions, setSessions] = useState<ChatSession[]>([])
    const [selectedSession, setSelectedSession] = useState<ChatSession | null>(null)
    const [messages, setMessages] = useState<ChatMessage[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [showNewSessionModal, setShowNewSessionModal] = useState(false)
    const [newMessage, setNewMessage] = useState('')
    const [searchQuery, setSearchQuery] = useState('')
    const [sending, setSending] = useState(false)
    const messagesEndRef = useRef<HTMLDivElement>(null)
    const trashRef = useRef<HTMLDivElement>(null)

    // Voice Input - Simple Toggle System (like AINexus)
    const { isRecording, isProcessing, startRecording, stopRecording, cancelRecording } = useVoiceInput()

    // Form State
    const [newSessionTitle, setNewSessionTitle] = useState('')

    // Fetch Sessions
    const fetchSessions = async () => {
        try {
            const lawyerId = getEffectiveLawyerId()
            if (!lawyerId) return

            const { data, error } = await supabase
                .from('ai_chat_sessions')
                .select('*')
                .eq('lawyer_id', lawyerId)
                .order('last_message_at', { ascending: false, nullsFirst: false })
                .order('created_at', { ascending: false })

            if (error) throw error
            setSessions(data || [])

            // Auto-select first session if exists
            if (data && data.length > 0 && !selectedSession) {
                fetchSessionMessages(data[0].id)
            }
        } catch (error) {
            console.error(error)
            toast.error('فشل تحميل الجلسات')
        } finally {
            setIsLoading(false)
        }
    }

    // Fetch Session Messages
    const fetchSessionMessages = async (sessionId: string) => {
        try {
            const { data: sessionData, error: sessionError } = await supabase
                .from('ai_chat_sessions')
                .select('*')
                .eq('id', sessionId)
                .single()

            if (sessionError) throw sessionError

            const { data: messagesData, error: messagesError } = await supabase
                .from('ai_chat_messages')
                .select('*')
                .eq('session_id', sessionId)
                .order('created_at', { ascending: true })

            if (messagesError) throw messagesError

            setSelectedSession(sessionData)
            setMessages(messagesData || [])
        } catch (error) {
            console.error(error)
            toast.error('فشل تحميل الرسائل')
        }
    }

    // Auto-create session if needed and send message
    const handleSendMessage = async (e?: React.FormEvent, transcribedText?: string) => {
        if (e) e.preventDefault()

        const messageToSend = transcribedText || newMessage
        if (!messageToSend.trim() || sending) return

        setSending(true)
        const userMessageContent = messageToSend.trim()  // ✅ Fixed: use messageToSend
        setNewMessage('')

        try {
            let currentSession = selectedSession

            // Auto-create session if none exists
            if (!currentSession) {
                const lawyerId = getEffectiveLawyerId()
                if (!lawyerId) {
                    setSending(false)
                    return
                }

                const { data: newSession, error: sessionError } = await supabase
                    .from('ai_chat_sessions')
                    .insert({
                        lawyer_id: lawyerId,
                        title: 'محادثة جديدة...' // Temporary title
                    })
                    .select()
                    .single()

                if (sessionError) throw sessionError
                currentSession = newSession
                setSelectedSession(newSession)
                setSessions(prev => [newSession, ...prev])
            }

            // Ensure we have a session
            if (!currentSession) {
                setSending(false)
                return
            }

            // Save user message
            const { data: userMsg, error: userError } = await supabase
                .from('ai_chat_messages')
                .insert({
                    session_id: currentSession.id,
                    role: 'user',
                    content: userMessageContent
                })
                .select()
                .single()

            if (userError) throw userError
            setMessages(prev => [...prev, userMsg])

            // Check if this is the first message (to generate title)
            const isFirstMessage = messages.length === 0

            // Call AI backend - Non-streaming endpoint
            const token = localStorage.getItem('access_token')
            const response = await fetch('http://localhost:8000/api/ai/chat', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: userMessageContent,
                    session_id: currentSession.id,
                    generate_title: isFirstMessage,
                    lawyer_id: getEffectiveLawyerId()  // ✅ Pass lawyer_id for proper agent context
                })
            })

            if (!response.ok) throw new Error('AI request failed')

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
            setMessages(prev => [...prev, aiMsg])

            // Update session title if AI generated one
            if (isFirstMessage && aiResponse.suggested_title) {
                const { error: updateError } = await supabase
                    .from('ai_chat_sessions')
                    .update({ title: aiResponse.suggested_title })
                    .eq('id', currentSession.id)

                if (!updateError) {
                    setSelectedSession(prev => prev ? { ...prev, title: aiResponse.suggested_title } : null)
                    setSessions(prev => prev.map(s =>
                        s.id === currentSession!.id ? { ...s, title: aiResponse.suggested_title } : s
                    ))
                }
            }

            fetchSessions() // Refresh list to update last_message_at
        } catch (error) {
            console.error(error)
            toast.error('فشل إرسال الرسالة')
        } finally {
            setSending(false)
        }
    }

    // ✅ Voice Input - Simple Toggle (Click to Record, Click to Stop) - Like AINexus
    const handleVoiceToggle = async () => {
        if (isRecording) {
            // Stop recording and transcribe
            try {
                const transcribedText = await stopRecording()
                if (transcribedText && transcribedText.trim()) {
                    // Auto-send after transcription
                    toast.success('تم تحويل الصوت إلى نص بنجاح')
                    await handleSendMessage(undefined, transcribedText)
                } else {
                    toast.warning('لم يتم التعرف على أي صوت. حاول التحدث بوضوح.')
                }
            } catch (error: any) {
                console.error(error)
                toast.error(error.message || 'فشل في تحويل الصوت')
                cancelRecording()
            }
        } else {
            // Start recording
            try {
                await startRecording()
                toast.success('🎤 جاري التسجيل... اضغط مرة أخرى للإيقاف')
            } catch (error: any) {
                console.error(error)
                toast.error(error.message || 'فشل في بدء التسجيل')
            }
        }
    }

    /*
    // OLD VOICE SYSTEM - COMMENTED OUT (NOT USED ANYMORE)
    // Handle Voice Input - Press and Hold
    const handleVoiceStart = async () => {
        try {
            await startRecording()
            setIsDraggingToTrash(false)
            toast.info('🎤 جاري التسجيل... اسحب لسلة المهملات للإلغاء', { duration: 1500 })
        } catch (error: any) {
            console.error(error)
            toast.error(error.message || 'فشل بدء التسجيل')
        }
    }

    const handleVoiceCancel = () => {
        if (isRecording) {
            cancelRecording()
            setIsDraggingToTrash(false)
            toast.success('تم إلغاء التسجيل', {
                icon: '🗑️'
            })
        }
    }

    // ✅ Global mouse tracking for drag-to-trash
    const handleGlobalMouseMove = useCallback((e: MouseEvent) => {
        if (!isRecordingRef.current || !trashRef.current) return

        const trashRect = trashRef.current.getBoundingClientRect()
        const isOverTrash = (
            e.clientX >= trashRect.left &&
            e.clientX <= trashRect.right &&
            e.clientY >= trashRect.top &&
            e.clientY <= trashRect.bottom
        )

        setIsDraggingToTrash(isOverTrash)
    }, [])

    // ✅ Setup and cleanup global mouse listener
    useEffect(() => {
        isRecordingRef.current = isRecording

        if (isRecording) {
            // Add global listener when recording starts
            document.addEventListener('mousemove', handleGlobalMouseMove)
            document.addEventListener('touchmove', handleGlobalMouseMove as any)
        } else {
            // Clean up when recording stops
            document.removeEventListener('mousemove', handleGlobalMouseMove)
            document.removeEventListener('touchmove', handleGlobalMouseMove as any)
            setIsDraggingToTrash(false)
        }

        return () => {
            document.removeEventListener('mousemove', handleGlobalMouseMove)
            document.removeEventListener('touchmove', handleGlobalMouseMove as any)
        }
    }, [isRecording, handleGlobalMouseMove])

    const handleVoiceEnd = async () => {
        if (!isRecording) return

        try {
            const transcribedText = await stopRecording()
            if (transcribedText && transcribedText.trim()) {
                // Set the text first
                setNewMessage(transcribedText)
                toast.success('تم تحويل الصوت إلى نص')

                // Auto-send the message immediately
                setSending(true)
                try {
                    let currentSession = selectedSession

                    // Auto-create session if none exists
                    if (!currentSession) {
                        const lawyerId = getEffectiveLawyerId()
                        if (!lawyerId) {
                            setSending(false)
                            return
                        }

                        const { data: newSession, error: sessionError } = await supabase
                            .from('ai_chat_sessions')
                            .insert({
                                lawyer_id: lawyerId,
                                title: 'محادثة صوتية...'
                            })
                            .select()
                            .single()

                        if (sessionError) throw sessionError
                        currentSession = newSession
                        setSelectedSession(newSession)
                        setSessions(prev => [newSession, ...prev])
                    }

                    if (!currentSession) {
                        setSending(false)
                        return
                    }

                    // Save user message
                    const { data: userMsg, error: userError } = await supabase
                        .from('ai_chat_messages')
                        .insert({
                            session_id: currentSession.id,
                            role: 'user',
                            content: transcribedText
                        })
                        .select()
                        .single()

                    if (userError) throw userError
                    setMessages(prev => [...prev, userMsg])

                    const isFirstMessage = messages.length === 0

                    // Call AI backend
                    const token = localStorage.getItem('access_token')
                    const response = await fetch('http://localhost:8000/api/ai/chat', {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${token}`,
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            message: transcribedText,
                            session_id: currentSession.id,
                            generate_title: isFirstMessage
                        })
                    })

                    if (!response.ok) throw new Error('AI request failed')

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
                    setMessages(prev => [...prev, aiMsg])

                    // Update session title if AI generated one
                    if (isFirstMessage && aiResponse.suggested_title) {
                        const { error: updateError } = await supabase
                            .from('ai_chat_sessions')
                            .update({ title: aiResponse.suggested_title })
                            .eq('id', currentSession.id)

                        if (!updateError) {
                            setSelectedSession(prev => prev ? { ...prev, title: aiResponse.suggested_title } : null)
                            setSessions(prev => prev.map(s =>
                                s.id === currentSession!.id ? { ...s, title: aiResponse.suggested_title } : s
                            ))
                        }
                    }

                    fetchSessions()
                    setNewMessage('') // Clear input after successful send
                } catch (error) {
                    console.error(error)
                    toast.error('فشل إرسال الرسالة')
                } finally {
                    setSending(false)
                }
            } else {
                toast.warning('لم يتم التعرف على أي صوت. حاول التحدث بوضوح.')
            }
        } catch (error: any) {
            console.error(error)
            toast.error(error.message || 'فشل تحويل الصوت')
        }
    }
    */

    // Create New Session Manually (optional - for explicit new conversation)
    const handleCreateSession = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!newSessionTitle.trim()) {
            toast.error('يرجى إدخال عنوان للجلسة')
            return
        }

        try {
            const lawyerId = getEffectiveLawyerId()
            if (!lawyerId) return

            const { data, error } = await supabase
                .from('ai_chat_sessions')
                .insert({
                    lawyer_id: lawyerId,
                    title: newSessionTitle.trim()
                })
                .select()
                .single()

            if (error) throw error

            toast.success('تم إنشاء جلسة جديدة')
            setShowNewSessionModal(false)
            setNewSessionTitle('')
            fetchSessions()
            setSelectedSession(data)
            setMessages([])
        } catch (error) {
            console.error(error)
            toast.error('فشل إنشاء الجلسة')
        }
    }

    // Delete Session
    const handleDeleteSession = async (sessionId: string) => {
        if (!confirm('هل تريد حذف هذه الجلسة؟')) return

        try {
            const { error } = await supabase
                .from('ai_chat_sessions')
                .delete()
                .eq('id', sessionId)

            if (error) throw error

            toast.success('تم حذف الجلسة')
            setSessions(prev => prev.filter(s => s.id !== sessionId))
            if (selectedSession?.id === sessionId) {
                setSelectedSession(null)
                setMessages([])
            }
        } catch (error) {
            console.error(error)
            toast.error('فشل حذف الجلسة')
        }
    }

    useEffect(() => {
        fetchSessions()
    }, [])

    useEffect(() => {
        if (messages.length > 0) {
            messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
        }
    }, [messages])

    // Filter sessions by search
    const filteredSessions = sessions.filter(s =>
        s.title.toLowerCase().includes(searchQuery.toLowerCase())
    )

    return (
        <div className="flex h-[calc(100vh-8rem)] bg-obsidian-950 rounded-3xl overflow-hidden border border-gray-800 text-sm">
            {/* Sidebar - Sessions List */}
            <div className={`${selectedSession ? 'hidden md:flex' : 'flex'} w-full md:w-80 flex-col border-l border-gray-800 bg-obsidian-900`}>
                <div className="p-4 border-b border-gray-800">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-lg font-bold text-white flex items-center gap-2">
                            <Sparkles className="w-4 h-4 text-gold-500" />
                            جلسات الذكاء الاصطناعي
                        </h2>
                        <button
                            onClick={() => setShowNewSessionModal(true)}
                            className="p-1.5 bg-gold-500 rounded-lg text-black hover:bg-gold-400 transition-colors"
                        >
                            <Plus className="w-4 h-4" />
                        </button>
                    </div>

                    <div className="relative">
                        <Search className="absolute right-3 top-2.5 w-3 h-3 text-gray-500" />
                        <input
                            type="text"
                            placeholder="بحث في الجلسات..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="w-full bg-obsidian-800 border border-gray-700 rounded-lg py-2 pr-9 pl-3 text-xs text-white focus:border-gold-500/50"
                        />
                    </div>
                </div>

                <div className="flex-1 overflow-y-auto p-3 space-y-2 scrollbar-thin">
                    {isLoading ? (
                        <div className="text-center py-8 text-gray-500">جاري التحميل...</div>
                    ) : filteredSessions.length === 0 ? (
                        <div className="text-center py-8 text-gray-500">
                            {searchQuery ? 'لا توجد نتائج' : 'لا توجد جلسات'}
                        </div>
                    ) : (
                        filteredSessions.map(session => (
                            <motion.div
                                key={session.id}
                                onClick={() => fetchSessionMessages(session.id)}
                                className={`p-3 rounded-xl border cursor-pointer transition-all hover:bg-obsidian-800/50 ${selectedSession?.id === session.id
                                    ? 'bg-obsidian-800 border-gold-500/30'
                                    : 'bg-obsidian-900/50 border-gray-800'
                                    }`}
                            >
                                <div className="flex justify-between items-start mb-1">
                                    <h3 className="font-bold text-gray-300 text-xs line-clamp-1 flex-1">{session.title}</h3>
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation()
                                            handleDeleteSession(session.id)
                                        }}
                                        className="p-1 hover:bg-red-500/20 text-red-400 rounded transition-colors"
                                    >
                                        <Trash2 className="w-3 h-3" />
                                    </button>
                                </div>
                                <div className="flex items-center gap-2 text-[10px] text-gray-500">
                                    <Clock className="w-3 h-3" />
                                    {session.last_message_at
                                        ? format(new Date(session.last_message_at), 'dd MMM, HH:mm', { locale: arSA })
                                        : format(new Date(session.created_at), 'dd MMM', { locale: arSA })}
                                    <span className="mr-auto">{session.message_count} رسائل</span>
                                </div>
                            </motion.div>
                        ))
                    )}
                </div>
            </div>

            {/* Chat Area - Always visible */}
            <div className="flex-1 flex flex-col bg-obsidian-950/50">
                {/* Chat Header */}
                <div className="bg-obsidian-900 border-b border-gray-800 p-4 flex items-center justify-between h-16 shrink-0">
                    <div className="flex items-center gap-3">
                        <button
                            onClick={() => setSelectedSession(null)}
                            className="md:hidden p-1 hover:bg-white/5 rounded-lg"
                        >
                            <X className="w-5 h-5 text-gray-400" />
                        </button>
                        <div className="w-8 h-8 bg-gradient-to-br from-gold-500 to-gold-600 rounded-lg flex items-center justify-center">
                            <Sparkles className="w-4 h-4 text-white" />
                        </div>
                        <div>
                            <h2 className="text-base font-bold text-white">
                                {selectedSession ? selectedSession.title : 'محادثة جديدة'}
                            </h2>
                            {selectedSession && (
                                <p className="text-xs text-gray-500">
                                    {selectedSession.message_count} رسائل
                                </p>
                            )}
                        </div>
                    </div>
                    {selectedSession && (
                        <button
                            onClick={() => {
                                setSelectedSession(null)
                                setMessages([])
                            }}
                            className="hidden md:flex items-center gap-2 px-3 py-1.5 bg-gold-500/10 border border-gold-500/20 rounded-lg text-gold-500 hover:bg-gold-500/20 transition-colors text-xs"
                        >
                            <Plus className="w-3 h-3" />
                            محادثة جديدة
                        </button>
                    )}
                </div>

                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin">
                    {messages.length === 0 ? (
                        <div className="flex items-center justify-center h-full">
                            <div className="text-center space-y-4 max-w-2xl px-4">
                                <div className="w-20 h-20 bg-gradient-to-br from-gold-500/20 to-gold-600/20 rounded-2xl flex items-center justify-center mx-auto">
                                    <Sparkles className="w-10 h-10 text-gold-500" />
                                </div>
                                <h3 className="text-2xl font-bold text-white">مرحباً بك في المحامي الذكي</h3>
                                <p className="text-gray-400 text-sm leading-relaxed">
                                    أنا مساعدك القانوني المدعوم بالذكاء الاصطناعي. يمكنني مساعدتك في:
                                </p>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-xl mx-auto mt-6">
                                    <div className="bg-obsidian-800/50 border border-gray-700 rounded-xl p-3 text-right">
                                        <div className="text-gold-500 text-xs mb-1">⚖️ استشارات قانونية</div>
                                        <div className="text-gray-300 text-xs">تحليل القضايا وتقديم المشورة</div>
                                    </div>
                                    <div className="bg-obsidian-800/50 border border-gray-700 rounded-xl p-3 text-right">
                                        <div className="text-gold-500 text-xs mb-1">📝 صياغة العقود</div>
                                        <div className="text-gray-300 text-xs">إعداد ومراجعة المستندات</div>
                                    </div>
                                    <div className="bg-obsidian-800/50 border border-gray-700 rounded-xl p-3 text-right">
                                        <div className="text-gold-500 text-xs mb-1">🔍 البحث القانوني</div>
                                        <div className="text-gray-300 text-xs">الوصول لقاعدة المعرفة</div>
                                    </div>
                                    <div className="bg-obsidian-800/50 border border-gray-700 rounded-xl p-3 text-right">
                                        <div className="text-gold-500 text-xs mb-1">💡 إدارة القضايا</div>
                                        <div className="text-gray-300 text-xs">تنظيم ومتابعة الأعمال</div>
                                    </div>
                                </div>
                                <p className="text-gray-500 text-xs mt-6">
                                    ابدأ بكتابة سؤالك أو طلبك في الأسفل
                                </p>
                            </div>
                        </div>
                    ) : (
                        <>
                            {messages.map((msg) => (
                                <div
                                    key={msg.id}
                                    className={`flex gap-3 ${msg.role === 'assistant' ? 'flex-row' : 'flex-row-reverse'}`}
                                >
                                    <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${msg.role === 'assistant' ? 'bg-gold-500/20' : 'bg-blue-500/20'
                                        }`}>
                                        {msg.role === 'assistant' ? (
                                            <Sparkles className="w-4 h-4 text-gold-500" />
                                        ) : (
                                            <span className="text-blue-500 text-xs font-bold">أنت</span>
                                        )}
                                    </div>
                                    <div className="max-w-[75%]">
                                        <div className={`flex items-center gap-2 mb-1 text-[10px] text-gray-500 ${msg.role !== 'assistant' && 'flex-row-reverse'}`}>
                                            <span>{msg.role === 'assistant' ? 'المحامي الذكي' : 'أنت'}</span>
                                            <span>{format(new Date(msg.created_at), 'HH:mm', { locale: arSA })}</span>
                                        </div>
                                        <div className={`p-3 rounded-2xl text-sm ${msg.role === 'assistant'
                                            ? 'bg-obsidian-800 text-gray-200 rounded-tl-none border border-gray-700'
                                            : 'bg-gradient-to-br from-blue-500 to-blue-600 text-white rounded-tr-none shadow-lg'
                                            }`}>
                                            <div className="prose prose-sm prose-invert max-w-none">
                                                <Markdown
                                                    remarkPlugins={[remarkGfm]}
                                                    components={{
                                                        p: ({ children }) => <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>,
                                                        strong: ({ children }) => <strong className="text-gold-500 font-semibold">{children}</strong>,
                                                        ul: ({ children }) => <ul className="list-disc list-inside space-y-1">{children}</ul>,
                                                        ol: ({ children }) => <ol className="list-decimal list-inside space-y-1">{children}</ol>,
                                                        table: ({ children }) => <div className="overflow-x-auto my-4"><table className="w-full border-collapse border border-gold-500/20 rounded-lg overflow-hidden">{children}</table></div>,
                                                        th: ({ children }) => <th className="bg-gold-500/10 p-2 text-gold-500 font-semibold border border-gold-500/20 text-right">{children}</th>,
                                                        td: ({ children }) => <td className="p-2 border border-gold-500/20">{children}</td>,
                                                    }}
                                                >
                                                    {msg.content}
                                                </Markdown>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                            {sending && (
                                <div className="flex gap-3">
                                    <div className="w-8 h-8 rounded-full bg-gold-500/20 flex items-center justify-center">
                                        <Sparkles className="w-4 h-4 text-gold-500 animate-pulse" />
                                    </div>
                                    <div className="bg-obsidian-800 border border-gray-700 rounded-2xl rounded-tl-none p-3">
                                        <div className="flex gap-1">
                                            <div className="w-2 h-2 bg-gold-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                                            <div className="w-2 h-2 bg-gold-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                                            <div className="w-2 h-2 bg-gold-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                                        </div>
                                    </div>
                                </div>
                            )}
                            <div ref={messagesEndRef} />
                        </>
                    )}
                </div>

                {/* Input Area - Always visible */}
                <div className="p-4 bg-obsidian-900 border-t border-gray-800 shrink-0">
                    <form onSubmit={handleSendMessage} className="flex gap-2">
                        {/* Input Area or Waveform */}
                        {isRecording ? (
                            <div className="flex-1 bg-gradient-to-r from-red-900/20 to-red-800/20 border border-red-500/50 rounded-xl p-4 flex items-center justify-center gap-2">
                                <Mic className="w-5 h-5 text-red-500 animate-pulse" />
                                {/* Audio Waveform Animation */}
                                <div className="flex items-center gap-1 h-8">
                                    {[...Array(20)].map((_, i) => (
                                        <motion.div
                                            key={i}
                                            className="w-1 bg-red-500 rounded-full"
                                            animate={{
                                                height: [8, 24, 8],
                                            }}
                                            transition={{
                                                duration: 0.6,
                                                repeat: Infinity,
                                                delay: i * 0.05,
                                            }}
                                        />
                                    ))}
                                </div>
                                <span className="text-red-400 text-sm font-bold animate-pulse">جاري التسجيل...</span>
                            </div>
                        ) : (
                            <div className="flex-1 bg-obsidian-800 border border-gray-700 rounded-xl p-1 focus-within:border-gold-500/50 transition-colors">
                                <textarea
                                    value={newMessage}
                                    onChange={(e) => setNewMessage(e.target.value)}
                                    placeholder={selectedSession ? "اكتب رسالتك هنا..." : "ابدأ محادثة جديدة..."}
                                    className="w-full bg-transparent border-none focus:ring-0 text-white min-h-[60px] max-h-[150px] resize-none p-3 text-sm scrollbar-thin placeholder:text-gray-500"
                                    onKeyDown={(e) => {
                                        if (e.key === 'Enter' && !e.shiftKey) {
                                            e.preventDefault()
                                            handleSendMessage(e)
                                        }
                                    }}
                                    disabled={sending}
                                    autoFocus
                                />
                            </div>
                        )}

                        {/* Simple Toggle Mic Button - Like AINexus */}
                        <button
                            type="button"
                            onClick={handleVoiceToggle}
                            disabled={sending || isProcessing}
                            className={`px-4 py-3 rounded-xl transition-all flex items-center gap-2 ${isRecording
                                ? 'bg-red-600 hover:bg-red-500 text-white animate-pulse'
                                : isProcessing
                                    ? 'bg-gray-600 cursor-wait text-white'
                                    : 'bg-obsidian-700 hover:bg-obsidian-600 text-gray-300 active:scale-95'
                                }`}
                            title={isRecording ? 'إيقاف التسجيل' : 'تسجيل صوتي'}
                        >
                            {isProcessing ? (
                                <Loader2 className="w-5 h-5 animate-spin" />
                            ) : isRecording ? (
                                <MicOff className="w-5 h-5" />
                            ) : (
                                <Mic className="w-5 h-5" />
                            )}
                        </button>

                        <button
                            type="submit"
                            disabled={!newMessage.trim() || sending}
                            className="px-4 py-3 bg-gradient-to-br from-gold-500 to-gold-600 rounded-xl text-white hover:from-gold-400 hover:to-gold-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-gold-500/20 disabled:shadow-none flex items-center gap-2"
                        >
                            <Send className="w-4 h-4" />
                            <span className="text-sm font-bold hidden md:inline">إرسال</span>
                        </button>
                    </form>
                    <p className="text-xs text-gray-600 mt-2 text-center">
                        اضغط <kbd className="px-1.5 py-0.5 bg-obsidian-700 rounded text-gray-400">Enter</kbd> للإرسال •
                        <kbd className="px-1.5 py-0.5 bg-obsidian-700 rounded text-gray-400 mr-1">Shift + Enter</kbd> لسطر جديد •
                        أو استخدم 🎤 للإدخال الصوتي
                    </p>
                </div>
            </div>

            {/* New Session Modal */}
            {
                showNewSessionModal && (
                    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            className="bg-obsidian-800 border border-gray-700 rounded-2xl p-6 max-w-md w-full"
                        >
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-lg font-bold text-white">جلسة جديدة</h3>
                                <button
                                    onClick={() => {
                                        setShowNewSessionModal(false)
                                        setNewSessionTitle('')
                                    }}
                                    className="p-1 hover:bg-white/5 rounded-lg"
                                >
                                    <X className="w-5 h-5 text-gray-400" />
                                </button>
                            </div>
                            <form onSubmit={handleCreateSession} className="space-y-4">
                                <div>
                                    <label className="block text-sm text-gray-400 mb-2">عنوان الجلسة</label>
                                    <input
                                        type="text"
                                        value={newSessionTitle}
                                        onChange={(e) => setNewSessionTitle(e.target.value)}
                                        placeholder="مثال: قضية أحمد - استشارة عقود"
                                        className="w-full bg-obsidian-900 border border-gray-700 rounded-lg p-3 text-white focus:border-gold-500/50"
                                        autoFocus
                                    />
                                </div>
                                <div className="flex gap-2">
                                    <button
                                        type="submit"
                                        className="flex-1 bg-gold-500 text-black font-bold py-2 rounded-lg hover:bg-gold-400 transition-colors"
                                    >
                                        إنشاء
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => {
                                            setShowNewSessionModal(false)
                                            setNewSessionTitle('')
                                        }}
                                        className="flex-1 bg-obsidian-700 text-white py-2 rounded-lg hover:bg-obsidian-600 transition-colors"
                                    >
                                        إلغاء
                                    </button>
                                </div>
                            </form>
                        </motion.div>
                    </div>
                )
            }
        </div >
    )
}
