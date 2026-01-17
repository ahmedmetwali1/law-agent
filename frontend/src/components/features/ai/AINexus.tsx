import { useEffect, useRef, useState } from 'react'
import { Send, Mic, MicOff, Sparkles, RotateCcw, Loader2 } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import Markdown from 'react-markdown'
import { useSidebarChat } from '../../../hooks/useSidebarChat'
import { useVoiceInput } from '../../../hooks/useVoiceInput'
import { toast } from 'sonner'
import remarkGfm from 'remark-gfm'

interface MessageBubbleProps {
    message: {
        id: string
        role: 'user' | 'assistant'
        content: string
        created_at: string
    }
}

// ✅ Simplified Message Bubble - Shows instantly (no streaming/typewriter)
function MessageBubble({ message }: MessageBubbleProps) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`flex ${message.role === 'user' ? 'justify-start' : 'justify-end'} mb-4`}
        >
            <div className={`max-w-[80%] ${message.role === 'user' ? 'order-1' : 'order-2'}`}>
                <div
                    className={`
            px-4 py-3 rounded-2xl
            ${message.role === 'user'
                            ? 'bg-cobalt-600 text-white'
                            : 'glass-dark text-gray-100'
                        }
          `}
                >
                    <div className="prose prose-sm prose-invert max-w-none">
                        <Markdown
                            remarkPlugins={[remarkGfm]}
                            components={{
                                p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                                strong: ({ children }) => <strong className="text-gold-500 font-semibold">{children}</strong>,
                                ul: ({ children }) => <ul className="list-disc list-inside space-y-1">{children}</ul>,
                                ol: ({ children }) => <ol className="list-decimal list-inside space-y-1">{children}</ol>,
                                table: ({ children }) => <div className="overflow-x-auto my-4"><table className="w-full border-collapse border border-gold-500/20 rounded-lg overflow-hidden">{children}</table></div>,
                                th: ({ children }) => <th className="bg-gold-500/10 p-2 text-gold-500 font-semibold border border-gold-500/20 text-right">{children}</th>,
                                td: ({ children }) => <td className="p-2 border border-gold-500/20">{children}</td>,
                            }}
                        >
                            {message.content}
                        </Markdown>
                    </div>
                </div>

                <p className="text-xs text-gray-500 mt-1 px-2">
                    {new Date(message.created_at).toLocaleTimeString('ar-SA', {
                        hour: '2-digit',
                        minute: '2-digit'
                    })}
                </p>
            </div>
        </motion.div>
    )
}

export function AINexus({ isCollapsed = false }: { isCollapsed?: boolean }) {
    const [input, setInput] = useState('')

    // ✅ Database-backed chat (replaces useChatStore)
    const { messages, isSending, sendMessage, clearSession } = useSidebarChat()

    const messagesEndRef = useRef<HTMLDivElement>(null)
    const { isRecording, isProcessing, startRecording, stopRecording, cancelRecording } = useVoiceInput()

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages])

    const handleSend = async (text?: string) => {
        const messageToSend = text || input
        if (!messageToSend.trim() || isSending) return

        try {
            await sendMessage(messageToSend)
            setInput('')
        } catch (error: any) {
            toast.error(error.message || 'فشل في إرسال الرسالة')
        }
    }

    const handleClearSession = async () => {
        if (confirm('هل تريد حذف جميع الرسائل وبدء جلسة جديدة؟')) {
            try {
                await clearSession()
                toast.success('تم إنشاء جلسة جديدة')
            } catch (error) {
                toast.error('فشل في إنشاء جلسة جديدة')
            }
        }
    }

    const handleVoiceInput = async () => {
        if (isRecording) {
            // Stop recording and transcribe
            try {
                const transcribedText = await stopRecording()
                if (transcribedText && transcribedText.trim()) {
                    toast.success('تم تحويل الصوت إلى نص بنجاح')
                    await handleSend(transcribedText)
                } else {
                    toast.warning('لم يتم التعرف على أي صوت. حاول التحدث بوضوح.')
                }
            } catch (error: any) {
                toast.error(error.message || 'فشل في تحويل الصوت')
                cancelRecording()
            }
        } else {
            // Start recording
            try {
                await startRecording()
                toast.success('جاري التسجيل... اضغط مرة أخرى للإيقاف')
            } catch (error: any) {
                toast.error(error.message || 'فشل في بدء التسجيل')
            }
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
            <div className="flex items-center justify-between px-4 py-3 border-b border-gold-500/10">
                <div>
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cobalt-600 to-cobalt-500 flex items-center justify-center">
                            <Sparkles className="w-4 h-4 text-white" />
                        </div>
                        <div>
                            <h2 className="text-sm font-semibold text-gold-500">المساعد الذكي</h2>
                            <p className="text-xs text-gray-400">شريكك في العمل</p>
                        </div>
                    </div>
                </div>

                <div className="flex gap-1">
                    {/* Clear Session Button */}
                    <button
                        onClick={handleClearSession}
                        className="p-2 hover:bg-obsidian-700 rounded-lg transition text-gray-400 hover:text-white"
                        title="مسح الجلسة"
                    >
                        <RotateCcw className="w-4 h-4" />
                    </button>
                </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 scrollbar-thin">
                <AnimatePresence mode="popLayout">
                    {messages.map((msg) => (
                        <MessageBubble key={msg.id} message={msg} />
                    ))}
                </AnimatePresence>

                {/* Loading Indicator */}
                {isSending && (
                    <div className="flex justify-end mb-4">
                        <div className="glass-dark px-4 py-3 rounded-2xl">
                            <Loader2 className="w-4 h-4 text-gold-500 animate-spin" />
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="p-4 border-t border-gold-500/10">
                <div className="flex gap-2">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault()
                                handleSend()
                            }
                        }}
                        placeholder="اكتب رسالتك..."
                        className="flex-1 bg-obsidian-700 text-white rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gold-500/50"
                        disabled={isSending}
                    />

                    {/* Voice Button */}
                    <button
                        onClick={handleVoiceInput}
                        disabled={isProcessing || isSending}
                        className={`p-2 rounded-lg transition ${isRecording
                                ? 'bg-red-500 text-white hover:bg-red-600'
                                : 'bg-obsidian-700 text-gray-400 hover:bg-obsidian-600 hover:text-white'
                            }`}
                        title={isRecording ? 'إيقاف التسجيل' : 'بدء التسجيل'}
                    >
                        {isRecording ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
                    </button>

                    {/* Send Button */}
                    <button
                        onClick={() => handleSend()}
                        disabled={!input.trim() || isSending}
                        className="px-4 py-2 bg-gradient-to-r from-cobalt-600 to-cobalt-500 text-white rounded-lg hover:from-cobalt-500 hover:to-cobalt-400 transition disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <Send className="w-5 h-5" />
                    </button>
                </div>
            </div>
        </div>
    )
}
