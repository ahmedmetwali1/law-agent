import React from 'react';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Sparkles, User, Brain, ChevronDown } from 'lucide-react';
import { format } from 'date-fns';
import { arSA } from 'date-fns/locale';
import { CognitiveInsightsBadge } from './CognitiveInsightsBadge';
import { CognitivePlanDisplay } from './CognitivePlanDisplay';
import { ExecutionResultsDisplay } from './ExecutionResultsDisplay';
import { WorkbenchProgress, ProgressItem } from './WorkbenchProgress';
import { ThinkingBubble } from './ThinkingBubble';

interface ChatBubbleProps {
    role: 'user' | 'assistant' | 'system';
    content: string;
    createdAt?: string;
    metadata?: any;
    isNew?: boolean; // Controls typewriter animation
}

export const ChatBubble: React.FC<ChatBubbleProps> = ({ role, content, createdAt, metadata, isNew }) => {
    const isUser = role === 'user';
    const isSystem = role === 'system';

    if (isSystem) return null; // Don't render system messages as bubbles

    // Helper to parse internal artifacts (JSON plan, <thought>)
    const parseContent = (text: string) => {
        let cleanText = text;
        let thought = null;
        let jsonPlan = null;

        // 1. Extract JSON Plan (Robust Nested Match)
        const startJson = cleanText.search(/^\s*\{/);
        if (startJson !== -1) {
            let endIndex = startJson;
            // Iterate to find the correct closing brace (handling nested objects)
            while (true) {
                endIndex = cleanText.indexOf('}', endIndex + 1);
                if (endIndex === -1) break; // No more closing braces

                const potentialJson = cleanText.slice(startJson, endIndex + 1);
                try {
                    JSON.parse(potentialJson);
                    jsonPlan = potentialJson;
                    cleanText = cleanText.replace(potentialJson, '').trim();
                    break;
                } catch (e) { }
            }
        }

        // 2. Extract <thought> tags
        const thoughtMatch = cleanText.match(/<thought>([\s\S]*?)<\/thought>/i);
        if (thoughtMatch) {
            thought = thoughtMatch[1].trim();
            cleanText = cleanText.replace(thoughtMatch[0], '').trim();
        }

        return { cleanText, thought, jsonPlan };
    };

    const { cleanText, thought, jsonPlan } = isUser ? { cleanText: content, thought: null, jsonPlan: null } : parseContent(content);

    // ✅ Typewriter Effect
    const [displayedText, setDisplayedText] = React.useState(isUser || !isNew ? cleanText : '');
    const [isTyping, setIsTyping] = React.useState(!isUser && !!isNew);

    React.useEffect(() => {
        if (isUser || !cleanText || !isNew) {
            setDisplayedText(cleanText);
            setIsTyping(false);
            return;
        }
        setDisplayedText('');
        setIsTyping(true);
        let i = 0;
        const interval = setInterval(() => {
            setDisplayedText(cleanText.slice(0, i + 6));
            i += 6;
            if (i >= cleanText.length) {
                clearInterval(interval);
                setIsTyping(false);
                setDisplayedText(cleanText);
            }
        }, 8);
        return () => clearInterval(interval);
    }, [cleanText, isUser, isNew]);

    // ✅ Phase 6: Thinking Bubble Integration
    const isTechnicalNode = metadata?.node === 'analyze' || metadata?.node === 'plan' || metadata?.node === 'execute';

    if (isTechnicalNode) {
        return <ThinkingBubble content={content} metadata={metadata} />;
    }

    return (
        <div className={`flex gap-3 w-full ${!isUser ? 'animate-fade-in-up' : ''} ${isUser ? 'flex-row-reverse' : 'flex-row'} mb-4`}>
            {/* Avatar */}
            <div className={`
                w-8 h-8 rounded-lg flex items-center justify-center shrink-0 border shadow-sm mt-1
                ${isUser
                    ? 'bg-blue-600/10 border-blue-500/20 text-blue-500'
                    : 'bg-gold-500/10 border-gold-500/20 text-gold-500'
                }
            `}>
                {isUser ? <User className="w-4 h-4" /> : <Sparkles className="w-4 h-4" />}
            </div>

            {/* Content Body */}
            <div className={`flex flex-col max-w-[85%] md:max-w-[75%] ${isUser ? 'items-end' : 'items-start'}`}>
                {/* Meta Header */}
                <div className={`flex items-center gap-2 mb-1.5 text-[10px] text-gray-500 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
                    <span className="font-semibold text-gray-400">
                        {isUser ? 'أنت' : 'المحامي الذكي'}
                    </span>
                    {createdAt && (
                        <span>{format(new Date(createdAt), 'HH:mm', { locale: arSA })}</span>
                    )}
                </div>

                {/* ✅ Insights, Plans, Results (Optional Metadata Displays) */}
                {!isUser && metadata?.cognitive_decision && (
                    <div className="mb-2 w-full"><CognitiveInsightsBadge decision={metadata.cognitive_decision} /></div>
                )}
                {!isUser && metadata?.execution_plan && (
                    <div className="mb-2 w-full"><CognitivePlanDisplay plan={metadata.execution_plan} executionResults={metadata?.execution_results} /></div>
                )}
                {!isUser && metadata?.execution_results && metadata.execution_results.length > 0 && (
                    <div className="mb-2 w-full"><ExecutionResultsDisplay results={metadata.execution_results} /></div>
                )}

                {/* Bubble */}
                <div className={`
                    p-4 rounded-2xl text-sm leading-relaxed shadow-sm w-full
                    ${isUser
                        ? 'bg-blue-600 text-white rounded-tr-sm'
                        : 'bg-obsidian-800 border border-gray-700 text-gray-100 rounded-tl-sm'
                    }
                `}>
                    <div className="prose prose-sm prose-invert max-w-none break-words" dir="auto">
                        <Markdown
                            remarkPlugins={[remarkGfm]}
                            components={{
                                p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                                code: ({ children }) => <code className="bg-black/30 px-1 py-0.5 rounded text-gold-300 font-mono text-xs">{children}</code>
                            }}
                        >
                            {displayedText || (thought || jsonPlan ? "..." : "")}
                        </Markdown>
                        {isTyping && <span className="inline-block w-1.5 h-4 bg-gold-400 align-middle ml-1 animate-pulse" />}
                    </div>
                </div>
            </div>
        </div>
    );
};
