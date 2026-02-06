import React, { useState, useRef, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { ChatMessage } from '@/components/chat/ChatMessage';
import { ChatInput } from '@/components/chat/ChatInput';
import { ChatSidebar } from '@/components/chat/ChatSidebar';
import { toast } from 'sonner';
import { motion, AnimatePresence } from 'framer-motion';
import { Menu, X, Scale, Webhook } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useUnifiedChat } from '@/hooks/useUnifiedChat';
import { useVoiceInput } from '@/hooks/useVoiceInput';
import { useSearchParams } from 'react-router-dom';
import { GoldenReasoningBox } from '@/components/chat/GoldenReasoningBox';

const WelcomeScreen = ({ onSuggestionClick }: { onSuggestionClick: (text: string) => void }) => {
    return (
        <div className="flex-1 flex flex-col items-center justify-center p-8 overflow-y-auto w-full max-w-4xl mx-auto">
            <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4 }}
                className="text-center mb-10"
            >
                <div className="w-16 h-16 bg-obsidian-800 rounded-2xl mx-auto mb-5 flex items-center justify-center border border-gray-700 shadow-sm">
                    <Webhook className="w-8 h-8 text-blue-500" />
                </div>
                <h2 className="text-2xl font-bold text-white mb-3">
                    مساعد N8N الذكي
                </h2>
                <p className="text-gray-400 max-w-lg mx-auto text-sm leading-relaxed">
                    نظام متصل مباشرة مع سير العمليات الخاص بك في N8N.
                </p>
            </motion.div>
        </div>
    );
};

const N8NChatPage: React.FC = () => {
    const { user } = useAuth();
    const [searchParams, setSearchParams] = useSearchParams();
    const sessionFromUrl = searchParams.get('session');

    // Use Unified Chat Hook with 'n8n' mode (though the hook argument is for session_type filtering on fetch if supported)
    // We will manually filter sessions or backend will need to support it. 
    // Ideally backend /sessions endpoint supports ?session_type=n8n
    // Our hook supports passing sessionFromUrl.
    const {
        messages,
        sessions,
        currentSession,
        isLoading,
        isThinking,
        isSending,
        sendMessage,
        clearSession,
        loadSessionsList,
        progressStatus
    } = useUnifiedChat(sessionFromUrl, 'main');

    // Voice Input State
    const { isRecording, startRecording, stopRecording, cancelRecording } = useVoiceInput();

    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Filter sessions - currently showing 'main' sessions as DB constraint prevents custom type
    const n8nSessions = sessions.filter(s => s.session_type === 'main');

    useEffect(() => {
        return () => {
            if (isRecording) {
                cancelRecording();
            }
        };
    }, [isRecording, cancelRecording]);

    useEffect(() => {
        if (currentSession?.id && currentSession.id !== sessionFromUrl) {
            setSearchParams({ session: currentSession.id });
        }
    }, [currentSession?.id, sessionFromUrl, setSearchParams]);

    const handleSessionSelect = (sessionId: string) => {
        setSearchParams({ session: sessionId });
    };

    const handleSendMessage = async (content: string) => {
        // Force mode to 'n8n'
        await sendMessage(content, { stream: true, mode: 'n8n' });
        loadSessionsList();
    };

    const handleVoiceInput = async () => {
        if (isRecording) {
            try {
                const transcribedText = await stopRecording();
                if (transcribedText?.trim()) {
                    toast.success('تم تحويل الصوت إلى نص');
                    handleSendMessage(transcribedText);
                } else {
                    toast.warning('لم يتم التعرف على الصوت');
                }
            } catch (error: any) {
                console.error('Voice Error:', error);
                toast.error('فشل تحويل الصوت');
                cancelRecording();
            }
        } else {
            try {
                await startRecording();
                toast.success('جاري التسجيل...');
            } catch (error) {
                toast.error('فشل بدء التسجيل');
            }
        }
    };

    const handleNewChat = async () => {
        await clearSession();
        setSearchParams({});
        if (window.innerWidth < 768) {
            setIsSidebarOpen(false);
        }
    };

    const scrollToBottom = () => {
        setTimeout(() => {
            messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
        }, 100);
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, isThinking]);

    return (
        <div className="flex h-[calc(100vh-64px)] bg-obsidian-950 overflow-hidden font-sans text-right" dir="rtl">
            {/* Sidebar */}
            <div className={`hidden md:block transition-all duration-300 border-l border-gray-800 ${isSidebarOpen ? 'w-72' : 'w-0 overflow-hidden'}`}>
                <ChatSidebar
                    sessions={sessions as any}
                    activeSessionId={currentSession?.id || ''}
                    onSelectSession={handleSessionSelect}
                    onNewChat={handleNewChat}
                    onRefresh={loadSessionsList}
                    onDelete={() => { }} // TODO: Implement delete if needed
                />
            </div>

            {/* Main Chat Area */}
            <div className="flex-1 flex flex-col relative h-full bg-obsidian-950 overflow-hidden">
                <header className="shrink-0 h-16 bg-obsidian-950 border-b border-gray-800 flex items-center justify-between px-4 z-30">
                    <div className="flex items-center gap-3">
                        <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} className="p-2 hover:bg-obsidian-900 rounded-lg text-gray-500 hover:text-white transition-colors">
                            {isSidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
                        </button>
                        <div className="h-6 w-px bg-gray-800"></div>
                        <div className="flex items-center gap-2">
                            <Webhook className="w-5 h-5 text-blue-500" />
                            <span className="text-white font-semibold">N8N Assistant</span>
                        </div>
                    </div>
                </header>

                <main className="flex-1 overflow-y-auto w-full relative scroll-smooth scrollbar-thin scrollbar-track-transparent scrollbar-thumb-gray-800">
                    {messages.length === 0 ? (
                        isLoading ? (
                            <div className="h-full flex flex-col items-center justify-center space-y-4">
                                <div className="w-12 h-12 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin"></div>
                                <p className="text-gray-500 text-xs animate-pulse">جاري التحميل...</p>
                            </div>
                        ) : (
                            <div className="h-full flex flex-col items-center justify-center min-h-[400px]">
                                <WelcomeScreen onSuggestionClick={handleSendMessage} />
                            </div>
                        )
                    ) : (
                        <div className="max-w-5xl mx-auto w-full px-2 md:px-6 py-8">
                            <AnimatePresence initial={false} mode="popLayout">
                                {messages.map((msg: any) => (
                                    <motion.div
                                        key={msg.id}
                                        initial={msg.role === 'user' ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0, scale: 0.95 }}
                                        transition={{ duration: 0.3, ease: "easeOut" }}
                                    >
                                        <ChatMessage
                                            role={msg.role}
                                            content={msg.content}
                                            reasoning={msg.reasoning}
                                        />
                                    </motion.div>
                                ))}
                            </AnimatePresence>

                            {isSending && (
                                <motion.div
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    className="max-w-5xl mx-auto"
                                >
                                    <ChatMessage
                                        role="assistant"
                                        content=""
                                        isThinking={true}
                                        statusText={progressStatus || undefined}
                                    />
                                </motion.div>
                            )}
                            <div ref={messagesEndRef} className="h-8" />
                        </div>
                    )}
                </main>

                <div className="shrink-0 relative z-40 bg-obsidian-950">
                    {/* Golden Thinking Box */}
                    <GoldenReasoningBox />

                    <ChatInput
                        onSend={handleSendMessage}
                        isLoading={isSending}
                        onVoiceClick={handleVoiceInput}
                        isRecording={isRecording}
                    />
                </div>
            </div>
        </div>
    );
};

export default N8NChatPage;
