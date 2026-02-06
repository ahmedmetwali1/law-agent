import { useEffect, useRef, useState, useCallback } from 'react'
import { Send, Mic, MicOff, Sparkles, RotateCcw, WifiOff, Wifi } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useUnifiedChat } from '../../../hooks/useUnifiedChat'
import { useVoiceInput } from '../../../hooks/useVoiceInput'
import { useCaseStore } from '../../../store'
import { toast } from 'sonner'
import { ChatMessage } from '../../chat/ChatMessage'
import { GoldenReasoningBox } from '../../chat/GoldenReasoningBox'

export function AINexus({ isCollapsed = false }: { isCollapsed?: boolean }) {
    const [input, setInput] = useState('')
    const [lastTranscription, setLastTranscription] = useState<string>('')
    const [isOnline, setIsOnline] = useState(navigator.onLine)
    const [shouldAutoScroll, setShouldAutoScroll] = useState(true)

    const { messages, isSending, sendMessage, clearSession, progressStatus } = useUnifiedChat(null, 'sidebar')
    const messagesEndRef = useRef<HTMLDivElement>(null)
    const messagesContainerRef = useRef<HTMLDivElement>(null)
    const { isRecording, isProcessing, startRecording, stopRecording, cancelRecording } = useVoiceInput()

    // ✅ FIX: Cleanup recording عند unmount
    useEffect(() => {
        return () => {
            if (isRecording) {
                cancelRecording()
            }
        }
    }, [isRecording, cancelRecording])

    // ✅ FIX: مراقبة حالة الاتصال
    useEffect(() => {
        const handleOnline = () => {
            setIsOnline(true)
            toast.success('تم استعادة الاتصال')
        }

        const handleOffline = () => {
            setIsOnline(false)
            toast.error('انقطع الاتصال بالإنترنت')
        }

        window.addEventListener('online', handleOnline)
        window.addEventListener('offline', handleOffline)

        return () => {
            window.removeEventListener('online', handleOnline)
            window.removeEventListener('offline', handleOffline)
        }
    }, [])

    // ✅ FIX: Auto-scroll ذكي
    useEffect(() => {
        if (!shouldAutoScroll) return

        const timeoutId = setTimeout(() => {
            messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
        }, 100)

        return () => clearTimeout(timeoutId)
    }, [messages, shouldAutoScroll])

    // ✅ FIX: كشف التمرير اليدوي
    const handleScroll = useCallback(() => {
        if (!messagesContainerRef.current) return

        const { scrollTop, scrollHeight, clientHeight } = messagesContainerRef.current
        const isNearBottom = scrollHeight - scrollTop - clientHeight < 50

        setShouldAutoScroll(isNearBottom)
    }, [])

    // ✅ FIX: الحصول على Context بشكل آمن
    const getContextSummary = useCallback(() => {
        try {
            const currentCase = useCaseStore.getState().currentCase

            if (!currentCase) {
                return undefined
            }

            const caseId = currentCase.id || currentCase.case_id

            if (!caseId) {
                console.warn('Case ID is missing')
                return undefined
            }

            return `Current Case ID: ${caseId}\nTitle: ${currentCase.title || 'Untitled'}\nClient: ${currentCase.client?.full_name || 'Unknown'}`
        } catch (error) {
            console.error('Failed to get context:', error)
            return undefined
        }
    }, [])

    // ✅ FIX: معالجة الإرسال مع error handling محسّن
    const handleSend = async (text?: string) => {
        const messageToSend = text || input

        if (!messageToSend.trim() || isSending) {
            if (!messageToSend.trim()) {
                toast.warning('الرجاء كتابة رسالة')
            }
            return
        }

        if (!isOnline) {
            toast.error('لا يوجد اتصال بالإنترنت')
            return
        }

        // مسح الإدخال فوراً
        setInput('')
        setShouldAutoScroll(true)

        const contextSummary = getContextSummary()

        try {
            await sendMessage(messageToSend, {
                mode: 'auto',
                context_summary: contextSummary,
                stream: true // ✅ Re-enabled for Radar UI
            })
        } catch (error: any) {
            console.error('Send error:', error)

            // إعادة النص للـ input في حالة الفشل
            setInput(messageToSend)

            toast.error(error.message || 'فشل في إرسال الرسالة')
        }
    }

    // ✅ FIX: مسح الجلسة مع تأكيد
    const handleClearSession = async () => {
        if (messages.length === 0) {
            toast.info('لا توجد رسائل لحذفها')
            return
        }

        if (!confirm('هل تريد حذف جميع الرسائل وبدء جلسة جديدة؟')) {
            return
        }

        try {
            await clearSession()
            toast.success('تم إنشاء جلسة جديدة')
            setShouldAutoScroll(true)
        } catch (error) {
            console.error('Clear session error:', error)
            toast.error('فشل في إنشاء جلسة جديدة')
        }
    }

    // ✅ FIX: معالجة Voice Input محسّنة
    const handleVoiceInput = async () => {
        if (isRecording) {
            // إيقاف التسجيل والتحويل
            try {
                const transcribedText = await stopRecording()

                if (!transcribedText || !transcribedText.trim()) {
                    toast.warning('لم يتم التعرف على أي صوت. حاول التحدث بوضوح.')
                    return
                }

                setLastTranscription(transcribedText)
                toast.success('تم تحويل الصوت إلى نص بنجاح')

                try {
                    await handleSend(transcribedText)
                } catch (sendError: any) {
                    // احتفظ بالنص في الـ input عند فشل الإرسال
                    setInput(transcribedText)
                    toast.error('فشل الإرسال، النص محفوظ في حقل الإدخال')
                }
            } catch (error: any) {
                console.error('Voice transcription error:', error)
                toast.error(error.message || 'فشل في تحويل الصوت')
                cancelRecording()
            }
        } else {
            // بدء التسجيل
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                toast.error('المتصفح لا يدعم التسجيل الصوتي')
                return
            }

            try {
                await startRecording()
                toast.success('جاري التسجيل... اضغط مرة أخرى للإيقاف')
            } catch (error: any) {
                console.error('Voice recording error:', error)

                if (error.name === 'NotAllowedError') {
                    toast.error('يرجى السماح بالوصول للميكروفون')
                } else if (error.name === 'NotFoundError') {
                    toast.error('لم يتم العثور على ميكروفون')
                } else {
                    toast.error(error.message || 'فشل في بدء التسجيل')
                }
            }
        }
    }

    // معالجة Enter key
    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            handleSend()
        }
    }

    if (isCollapsed) {
        return (
            <div className="flex flex-col h-full glass-light border-r border-gold-500/10 items-center py-4">
                <Sparkles className="w-6 h-6 text-gold-500 mb-4" />
                <span className="text-xs text-gray-400 writing-mode-vertical">AI</span>
            </div>
        )
    }

    return (
        <div className="flex flex-col h-full glass-light border-r border-gold-500/10">
            {/* Header */}
            <div className="flex flex-col gap-2 px-4 py-3 border-b border-gold-500/10">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cobalt-600 to-cobalt-500 flex items-center justify-center">
                            <Sparkles className="w-4 h-4 text-white" />
                        </div>
                        <div>
                            <h2 className="text-sm font-semibold text-gold-500">مارد</h2>
                            <div className="flex items-center gap-1.5 mt-0.5">
                                {isOnline ? (
                                    <>
                                        <Wifi className="w-3 h-3 text-green-500" />
                                        <span className="text-[10px] text-green-500">متصل</span>
                                    </>
                                ) : (
                                    <>
                                        <WifiOff className="w-3 h-3 text-red-500" />
                                        <span className="text-[10px] text-red-500">غير متصل</span>
                                    </>
                                )}
                            </div>
                        </div>
                    </div>

                    <div className="flex gap-1">
                        <button
                            onClick={handleClearSession}
                            disabled={isSending || messages.length === 0}
                            className="p-1.5 hover:bg-obsidian-700 rounded-lg transition text-gray-400 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
                            title="مسح الجلسة"
                            aria-label="مسح الجلسة"
                        >
                            <RotateCcw className="w-4 h-4" />
                        </button>
                    </div>
                </div>
            </div>

            {/* Messages */}
            <div
                ref={messagesContainerRef}
                onScroll={handleScroll}
                className="flex-1 overflow-y-auto p-4 scrollbar-thin scrollbar-track-transparent scrollbar-thumb-gray-700"
            >
                {/* Messages */}
                {messages.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-center px-4">
                        <div className="w-12 h-12 rounded-full bg-gradient-to-br from-cobalt-600 to-cobalt-500 flex items-center justify-center mb-3">
                            <Sparkles className="w-6 h-6 text-white" />
                        </div>
                        <h3 className="text-sm font-semibold text-gray-300 mb-1">مرحباً بك!</h3>
                        <p className="text-xs text-gray-500 leading-relaxed">
                            أنا هنا لمساعدتك في أي استفسار قانوني
                        </p>
                    </div>
                ) : (
                    <AnimatePresence mode="popLayout">
                        {messages.map((msg: any) => (
                            <motion.div
                                key={msg.id}
                                initial={msg.role === 'user' ? { opacity: 1 } : { opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, scale: 0.95 }}
                                transition={{ duration: 0.2 }}
                            >
                                <ChatMessage
                                    role={msg.role}
                                    content={msg.content}
                                    reasoning={msg.reasoning}
                                    timestamp={msg.created_at}
                                    variant="compact"
                                    failed={msg.metadata?.failed}
                                />
                            </motion.div>
                        ))}
                    </AnimatePresence>
                )}

                {/* 🌟 VITAL: Global Radar Indicator for Sidebar */}
                <div className="my-2">
                    <GoldenReasoningBox />
                </div>

                <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="p-4 border-t border-gold-500/10">
                <div className="flex gap-2">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder={isOnline ? "اكتب رسالتك..." : "لا يوجد اتصال..."}
                        className="flex-1 bg-obsidian-700 text-white rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gold-500/50 disabled:opacity-50 disabled:cursor-not-allowed"
                        disabled={isSending || !isOnline}
                        aria-label="حقل الرسالة"
                    />

                    {/* Voice Button */}
                    <button
                        onClick={handleVoiceInput}
                        disabled={isProcessing || isSending || !isOnline}
                        className={cn(
                            "p-2 rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed",
                            isRecording
                                ? 'bg-red-500 text-white hover:bg-red-600 animate-pulse'
                                : 'bg-obsidian-700 text-gray-400 hover:bg-obsidian-600 hover:text-white'
                        )}
                        title={isRecording ? 'إيقاف التسجيل' : 'بدء التسجيل'}
                        aria-label={isRecording ? 'إيقاف التسجيل' : 'بدء التسجيل'}
                    >
                        {isRecording ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
                    </button>

                    {/* Send Button */}
                    <button
                        onClick={() => handleSend()}
                        disabled={!input.trim() || isSending || !isOnline}
                        className="px-4 py-2 bg-gradient-to-r from-cobalt-600 to-cobalt-500 text-white rounded-lg hover:from-cobalt-500 hover:to-cobalt-400 transition disabled:opacity-50 disabled:cursor-not-allowed"
                        aria-label="إرسال الرسالة"
                    >
                        <Send className="w-5 h-5" />
                    </button>
                </div>

                {/* Helper Text */}
                {isRecording && (
                    <motion.p
                        initial={{ opacity: 0, y: -5 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="text-xs text-red-400 mt-2 animate-pulse"
                    >
                        جاري التسجيل... اضغط على الميكروفون للإيقاف
                    </motion.p>
                )}

                {lastTranscription && (
                    <motion.p
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="text-xs text-gray-500 mt-2"
                    >
                        آخر تسجيل: {lastTranscription.slice(0, 50)}...
                    </motion.p>
                )}
            </div>
        </div>
    )
}

// ✅ Helper: cn utility (إذا لم يكن موجود)
function cn(...classes: (string | boolean | undefined)[]) {
    return classes.filter(Boolean).join(' ')
}