import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles } from 'lucide-react';
import { useChatStore, useCaseStore } from '@/store';
import { caseApi } from '@/api/client';
import { Timeline } from './genui/Timeline';
import { ComparisonTable } from './genui/ComparisonTable';
import { InfoCards } from './genui/InfoCards';
import { RichMessage } from './chat/RichMessage';
import { ToolExecutionProgress } from './chat/ToolExecutionProgress';
import {
    LiveThinkingStream,
    ConfidenceMeter,
    TypingIndicator,
    RippleButton,
    type ThinkingStatus
} from './ui/EnhancedComponents';

interface GenUIComponent {
    type: 'timeline' | 'comparison' | 'cards';
    data: any;
}

interface MessageWithThinking {
    id: string;
    role: 'user' | 'assistant' | 'system';  // Added 'system'
    content: string;
    thinking?: string;
    showThinking?: boolean;
    genUI?: GenUIComponent;
    confidence?: number;
    progressSteps?: Array<{
        id: string;
        status: 'pending' | 'running' | 'success' | 'error';
        message: string;
    }>;
}

const parseMessageContent = (content: string): { text: string; genUI?: GenUIComponent } => {
    const genUIRegex = /```genui\n([\s\S]*?)\n```/;
    const match = content.match(genUIRegex);

    if (match) {
        try {
            const genUIData = JSON.parse(match[1]);
            const textWithoutUI = content.replace(match[0], '').trim();
            return {
                text: textWithoutUI,
                genUI: genUIData
            };
        } catch (e) {
            console.error("Failed to parse GenUI payload", e);
        }
    }
    return { text: content };
};

export const ChatInterface: React.FC = () => {
    const { messages, isTyping, addMessage, setTyping } = useChatStore();
    const { setCurrentCase, setProcessing } = useCaseStore();
    const [input, setInput] = useState('');
    const [sessionId, setSessionId] = useState<string | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, isTyping]);

    useEffect(() => {
        if (!sessionId) {
            initSession();
        }
    }, []);

    const initSession = async () => {
        try {
            const response = await caseApi.startChat();
            setSessionId(response.session_id);
        } catch (error) {
            console.error('Failed to start chat:', error);
        }
    };

    const handleSend = async () => {
        if (!input.trim() || !sessionId) return;

        const userMessage = input.trim();
        setInput('');
        addMessage('user', userMessage);
        setTyping(true);

        try {
            const response = await caseApi.sendChatMessage(sessionId, userMessage);

            setTyping(false);
            const parsed = parseMessageContent(response.message);
            addMessage('assistant', parsed.text);

            if (response.case_data) {
                setCurrentCase(response.case_data);
            }
        } catch (error) {
            console.error('Failed to send message:', error);
            setTyping(false);
            addMessage('assistant', 'عذراً، حدث خطأ. يرجى المحاولة مرة أخرى.');
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <div className="flex flex-col h-full bg-background">
            {/* Header - ✅ مصغر */}
            <div className="px-3 py-2 border-b border-border bg-surface/50 backdrop-blur-sm">
                <div className="flex items-center gap-2">
                    <div className="w-7 h-7 bg-gradient-to-br from-primary to-success rounded-lg flex items-center justify-center">
                        <Sparkles className="h-3.5 w-3.5 text-white" />
                    </div>
                    <div>
                        <h2 className="text-sm font-bold text-gradient">المحامي الذكي</h2>
                        <p className="text-xs text-muted-foreground hidden">AI Assistant</p>
                    </div>
                </div>
            </div>

            {/* Messages Area - ✅ مصغر */}
            <div className="flex-1 overflow-y-auto px-3 py-2 space-y-2">
                {messages.length === 0 && (
                    <div className="flex items-center justify-center h-full">
                        <div className="text-center space-y-4 max-w-md">
                            <div className="w-20 h-20 bg-gradient-to-br from-primary/20 to-success/20 rounded-2xl flex items-center justify-center mx-auto">
                                <Sparkles className="h-10 w-10 text-primary" />
                            </div>
                            <h3 className="text-xl font-bold">مرحباً بك!</h3>
                            <p className="text-muted-foreground">
                                أنا محاميك الذكي المدعوم بالذكاء الاصطناعي المتقدم.
                                كيف يمكنني مساعدتك اليوم؟
                            </p>
                        </div>
                    </div>
                )}

                {messages.map((msg) => (
                    <MessageBubble key={msg.id} message={msg} />
                ))}

                {isTyping && <TypingIndicator />}

                <div ref={messagesEndRef} />
            </div>

            {/* Input Area - ✅ مصغر */}
            <div className="px-3 py-2 border-t border-border bg-surface/30 backdrop-blur-sm">
                <div className="flex gap-2 items-end">
                    <div className="flex-1 relative">
                        <textarea
                            ref={inputRef}
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyPress={handleKeyPress}
                            placeholder="اكتب سؤالك..."
                            className="w-full px-3 py-2 text-sm bg-background border border-border rounded-lg
                                     resize-none focus:ring-2 focus:ring-primary/50 focus:border-primary
                                     transition-all duration-200 min-h-[40px] max-h-[120px]"
                            rows={1}
                            style={{
                                fontFamily: 'Cairo, sans-serif',
                                lineHeight: '1.4'
                            }}
                        />
                    </div>
                    <RippleButton
                        onClick={handleSend}
                        disabled={!input.trim() || isTyping}
                        variant="primary"
                        className="h-[40px] px-3"
                    >
                        <Send className="h-4 w-4" />
                    </RippleButton>
                </div>
                <p className="text-xs text-muted-foreground mt-1 text-center hidden">
                    Enter للإرسال
                </p>
            </div>
        </div>
    );
};

// Message Bubble Component
interface MessageBubbleProps {
    message: MessageWithThinking;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
    const isUser = message.role === 'user';

    return (
        <div className={`flex ${isUser ? 'justify-start' : 'justify-end'} animate-fade-in`}>
            <div className={`
                max-w-[85%] rounded-lg px-3 py-2 space-y-1 text-sm
                ${isUser
                    ? 'message-user'
                    : 'message-assistant'
                }
            `}>
                {/* Show progress steps if executing tools */}
                {message.progressSteps && message.progressSteps.length > 0 && (
                    <ToolExecutionProgress steps={message.progressSteps} />
                )}

                {/* Use RichMessage for intelligent rendering */}
                <RichMessage content={message.content} isUser={isUser} />

                {message.confidence && !isUser && (
                    <ConfidenceMeter confidence={message.confidence} />
                )}

                {message.genUI && (
                    <div className="mt-3">
                        {message.genUI.type === 'timeline' && <Timeline data={message.genUI.data} />}
                        {message.genUI.type === 'comparison' && <ComparisonTable data={message.genUI.data} />}
                        {message.genUI.type === 'cards' && <InfoCards data={message.genUI.data} />}
                    </div>
                )}
            </div>
        </div>
    );
};
