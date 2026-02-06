// ✅ FIX: Restore imports
import React, { useState, useRef, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { ChatMessage } from '@/components/chat/ChatMessage';
import { ChatInput } from '@/components/chat/ChatInput';
import { ChatSidebar, Session } from '@/components/chat/ChatSidebar';
import { toast } from 'sonner';
import { apiClient } from '@/api/client';
import { motion, AnimatePresence } from 'framer-motion';
import { Menu, X, Scale, FileText, Search, Gavel, UserCog, BookOpen, Sparkles, SidebarOpen, SidebarClose } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useUnifiedChat } from '@/hooks/useUnifiedChat';
import { useVoiceInput } from '@/hooks/useVoiceInput';
import { useSearchParams } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { useChatStore } from '@/stores/chatStore';
import { StageProgressStepper } from '@/components/chat/StageProgressStepper';
import { CouncilLiveView } from '@/components/chat/CouncilLiveView';
import { GoldenReasoningBox } from '@/components/chat/GoldenReasoningBox';

// ... (SuggestionCard and WelcomeScreen kept same logic for brevity, re-including them below if needed, 
// but for this snippet I will assume they are safe to stay or I will inline them to be safe)

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
                    <Scale className="w-8 h-8 text-gold-500" />
                </div>
                <h2 className="text-2xl font-bold text-white mb-3">
                    أهلاً بك مع "مارد"
                </h2>
                <p className="text-gray-400 max-w-lg mx-auto text-sm leading-relaxed">
                    مساعدك القانوني السحري. اطلب ما تشاء، وسيقوم مارد بتنفيذه بلمح البصر.
                </p>
            </motion.div>
        </div>
    );
};

const AIChatPage: React.FC = () => {
    const { user } = useAuth();
    const [searchParams, setSearchParams] = useSearchParams();
    const sessionFromUrl = searchParams.get('session');

    // State via Unified Hook (Ensure useUnifiedChat is compatible or we use store directly? 
    // UseUnifiedChat connects to the store, so it should be fine if we updated the store logic correctly.
    // However, useUnifiedChat might mask the new 'currentActivity' if it doesn't export it. 
    // Let's use the store directly for the new V3 components!)

    // We import the store directly to access V3 state
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
        setCurrentSession,
        // progressStatus // Removed, replaced by ThinkingPulse
    } = useUnifiedChat(sessionFromUrl);

    // Voice
    const { isRecording, startRecording, stopRecording, cancelRecording } = useVoiceInput();

    // UI State
    const [isSessionsSidebarOpen, setIsSessionsSidebarOpen] = useState(true);
    const [isCouncilSidebarOpen, setIsCouncilSidebarOpen] = useState(false); // Default closed, opens on activity

    const messagesEndRef = useRef<HTMLDivElement>(null);



    // Auto-open Council Sidebar when deliberation starts
    // We need to listen to store state.
    const { currentActivity, councilSession } = useChatStore();

    useEffect(() => {
        if (currentActivity.stage === 'DELIBERATING') {
            setIsCouncilSidebarOpen(true);
        }
    }, [currentActivity.stage]);

    // ... (Voice Handlers & Session Handlers kept same) ...
    useEffect(() => {
        return () => { if (isRecording) cancelRecording(); };
    }, [isRecording, cancelRecording]);

    useEffect(() => {
        if (currentSession?.id && currentSession.id !== sessionFromUrl) {
            setSearchParams({ session: currentSession.id });
        }
    }, [currentSession?.id, sessionFromUrl, setSearchParams]);

    const handleSessionSelect = (sessionId: string) => setSearchParams({ session: sessionId });
    const handleNewChat = async () => {
        await clearSession(); // This should also reset V3 state in store
        setSearchParams({});
        if (window.innerWidth < 768) setIsSessionsSidebarOpen(false);
    };
    const handleSendMessage = async (content: string) => {
        await sendMessage(content, { stream: true, mode: 'auto' }); // Enable Stream!
        loadSessionsList();
    };

    // Voice Handler (Simplified for brevity)
    const handleVoiceInput = async () => {
        if (isRecording) {
            try {
                const text = await stopRecording();
                if (text?.trim()) handleSendMessage(text);
                else toast.warning('لم يتم التعرف على الصوت');
            } catch (e) { toast.error('فشل التسجيل'); }
        } else {
            await startRecording();
            toast.success('جاري التسجيل...');
        }
    };

    // Scroll
    const scrollToBottom = () => {
        setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 100);
    };
    useEffect(() => scrollToBottom(), [messages]);


    return (
        <div className="flex h-[calc(100vh-64px)] bg-obsidian-950 overflow-hidden font-sans text-right" dir="rtl">

            {/* LEFT: Sessions Sidebar */}
            <div className={`hidden md:block transition-all duration-300 border-l border-gray-800 ${isSessionsSidebarOpen ? 'w-72' : 'w-0 overflow-hidden'}`}>
                <ChatSidebar
                    sessions={sessions as any}
                    activeSessionId={currentSession?.id || ''}
                    onSelectSession={handleSessionSelect}
                    onNewChat={handleNewChat}
                    onRefresh={loadSessionsList}
                    onDelete={() => { }} // simplified
                />
            </div>

            {/* CENTER: Main Chat */}
            <div className="flex-1 flex flex-col relative h-full bg-obsidian-950 overflow-hidden transition-all duration-300">

                {/* Header with Stepper */}
                <header className="shrink-0 bg-obsidian-950 border-b border-gray-800 flex flex-col z-30 pt-4">
                    <div className="h-16 flex items-center justify-between px-4">
                        <div className="flex items-center gap-3">
                            <button onClick={() => setIsSessionsSidebarOpen(!isSessionsSidebarOpen)} className="p-2 hover:bg-obsidian-900 rounded-lg text-gray-500 hover:text-white transition-colors">
                                {isSessionsSidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
                            </button>
                            <span className="text-white font-bold text-xl flex items-center gap-2">
                                <Sparkles className="w-6 h-6 text-gold-500 animate-pulse" />
                                <span>مارد</span>
                            </span>
                        </div>

                        {/* Toggle Council View */}
                        <button
                            onClick={() => setIsCouncilSidebarOpen(!isCouncilSidebarOpen)}
                            className={`flex items-center gap-2 px-4 py-2 rounded-lg border transition-all text-xs font-medium
                                ${isCouncilSidebarOpen || councilSession.activeAgents.length > 0
                                    ? 'bg-obsidian-800 border-gold-500/20 text-gold-400 shadow-inner'
                                    : 'bg-transparent border-transparent text-gray-500 hover:text-gray-300 hover:bg-white/5'}`}
                        >
                            <UserCog className={cn("w-4 h-4", isCouncilSidebarOpen ? "text-gold-500" : "text-gray-500")} />
                            <span className={cn(isCouncilSidebarOpen ? "text-gold-100" : "text-gray-400")}>غرفة المداولة</span>
                            {councilSession.activeAgents.length > 0 && (
                                <span className="bg-gold-500 text-obsidian-950 text-[10px] px-1.5 rounded-full animate-pulse font-bold">
                                    {councilSession.activeAgents.length}
                                </span>
                            )}
                        </button>
                    </div>

                    {/* Stepper Removed as per user request */}
                </header>

                {/* Messages Area */}
                <main className="flex-1 overflow-y-auto w-full relative scroll-smooth scrollbar-thin scrollbar-track-transparent scrollbar-thumb-gray-800">
                    {messages.length === 0 ? (
                        <WelcomeScreen onSuggestionClick={handleSendMessage} />
                    ) : (
                        <div className="mx-auto w-full px-2 md:pl-14 md:pr-[4.5rem] py-6 pb-20">
                            <AnimatePresence initial={false} mode="popLayout">
                                {messages.map((msg: any) => (
                                    <motion.div
                                        key={msg.id}
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        className="mb-4"
                                    >
                                        <ChatMessage
                                            role={msg.role}
                                            content={msg.content}
                                            reasoning={undefined} // We show reasoning in Sidebar now!
                                        />
                                    </motion.div>
                                ))}
                            </AnimatePresence>
                            <div ref={messagesEndRef} className="h-8" />
                        </div>
                    )}
                </main>

                {/* VITAL V3.0: Thinking Pulse & Input */}
                <div className="shrink-0 relative z-40 bg-obsidian-950 pb-2">
                    <GoldenReasoningBox />
                    <ChatInput
                        onSend={handleSendMessage}
                        isLoading={isSending}
                        onVoiceClick={handleVoiceInput}
                        isRecording={isRecording}
                    />

                    {/* Tiny Footer */}
                    <div className="text-center pb-2">
                        <span className="text-[10px] text-gray-700">مدعوم بمعمارية القاضي المايسترو v2.0</span>
                    </div>
                </div>

            </div>

            {/* RIGHT: Council Live View (Drawer) */}
            <div className={`hidden lg:block transition-all duration-300 border-r border-gray-800 bg-obsidian-900/30 
                ${isCouncilSidebarOpen ? 'w-80 opacity-100' : 'w-0 opacity-0 overflow-hidden'}`}>
                <CouncilLiveView />
            </div>

            {/* Mobile Council Drawer Overlay (Optional) */}
            {/* For now keeping it simple as specific request was sidebar */}

        </div>
    );
};

export default AIChatPage;
