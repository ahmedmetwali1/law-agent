import React, { useState, useMemo, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeSanitize from 'rehype-sanitize'; // تأكد من الاستيراد الصحيح
import { Copy, Check, Sparkles, BrainCircuit, ChevronDown, ChevronUp, Bot, User, Clock, AlertCircle, RotateCcw, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';
import { formatDistanceToNow } from 'date-fns';
import { ar } from 'date-fns/locale';
import { toast } from 'sonner';

import { useAuth } from '@/contexts/AuthContext';

// ✅ FIX 1: نقل ThinkingProcess للخارج للحفاظ على الحالة (State)
const ThinkingProcess = ({ reasoning }: { reasoning: string }) => {
    const [isOpen, setIsOpen] = useState(true); // لن يتم تصفيرها الآن
    const contentRef = useRef<HTMLDivElement>(null);
    const [contentHeight, setContentHeight] = useState(0);

    const steps = useMemo(() => {
        return reasoning.split('\n').filter(line => line.trim().length > 0);
    }, [reasoning]);

    useEffect(() => {
        if (contentRef.current && isOpen) {
            setContentHeight(contentRef.current.scrollHeight);
        } else if (!isOpen) {
            setContentHeight(0);
        }
    }, [isOpen, reasoning]);

    return (
        <div className="w-full max-w-3xl mx-auto mb-6 bg-obsidian-900/50 rounded-xl border border-gold-500/10 overflow-hidden" dir="rtl">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="w-full flex items-center justify-between p-3 px-4 bg-obsidian-900 border-b border-gold-500/5 hover:bg-obsidian-800 transition-colors"
            >
                <div className="flex items-center gap-2 text-gold-500">
                    <BrainCircuit className="w-4 h-4 animate-pulse" />
                    <span className="text-xs font-bold tracking-wider uppercase">سجل التفكير والتحليل</span>
                </div>
                <div className="flex items-center gap-2">
                    <span className="text-[10px] text-gray-500 font-mono">{steps.length} خطوة</span>
                    {isOpen ? <ChevronUp className="w-3.5 h-3.5 text-gray-500" /> : <ChevronDown className="w-3.5 h-3.5 text-gray-500" />}
                </div>
            </button>

            <AnimatePresence initial={false}>
                {isOpen && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: contentHeight, opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2, ease: "easeInOut" }}
                        className="overflow-hidden"
                    >
                        <div ref={contentRef} className="p-4 space-y-3 bg-obsidian-950/30 max-h-96 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700">
                            {steps.length > 0 ? (
                                steps.map((step, idx) => {
                                    const isHeader = step.includes('---') || step.includes('📍 Node:') || step.match(/^[A-Z\s]+:$/);
                                    return (
                                        <motion.div
                                            key={`${idx}-${step.slice(0, 20)}`}
                                            initial={{ opacity: 0, x: -10 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            transition={{ delay: idx * 0.05 }}
                                            className={cn("flex items-start gap-3", isHeader && "mt-4 mb-2 pb-1 border-b border-gray-800")}
                                        >
                                            {isHeader ? (
                                                <div className="flex items-center gap-2 w-full text-gold-400">
                                                    <div className="w-1.5 h-1.5 rounded-full bg-gold-500 shrink-0" />
                                                    <span className="text-xs font-bold uppercase tracking-wider">
                                                        {step.replace(/[-]/g, '').replace('📍 Node:', '').trim()}
                                                    </span>
                                                </div>
                                            ) : (
                                                <>
                                                    <div className="w-1.5 h-1.5 rounded-full bg-gold-500/30 mt-1.5 shrink-0" />
                                                    <p className="text-xs text-gray-400 font-mono leading-relaxed">{step}</p>
                                                </>
                                            )}
                                        </motion.div>
                                    );
                                })
                            ) : (
                                <div className="flex items-center gap-2 text-xs text-gray-500 animate-pulse">
                                    <span className="w-1.5 h-1.5 rounded-full bg-gold-500/50" />
                                    جاري تحليل الطلب...
                                </div>
                            )}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

interface ChatMessageProps {
    role: 'user' | 'assistant' | 'system';
    content: string;
    isThinking?: boolean;
    timestamp?: string;
    reasoning?: string;
    variant?: 'full' | 'compact';
    statusText?: string;
    failed?: boolean;
    onRetry?: () => void;
}

const isJsonLeak = (text: string) => {
    if (!text) return false;
    const trimmed = text.trim();
    // منطق اكتشاف التسريب الحالي جيد، لكن يجب أن يكون حذراً من الأكواد البرمجية الشرعية
    if (trimmed.startsWith('```json')) return true;
    if (trimmed.startsWith('[') || trimmed.startsWith('{')) {
        if (trimmed.includes('"name"') || trimmed.includes('"args"') || trimmed.includes('query_') || trimmed.includes('insert_')) {
            return true;
        }
    }
    if (trimmed.includes('"action": "ADMIN_QUERY"') || trimmed.includes('"action": "ADMIN_DISTRIBUTOR"')) {
        return true;
    }
    return false;
};

const cleanLeakedJson = (text: string): string => {
    let cleaned = text;
    cleaned = cleaned.replace(/```json[\s\S]*?```/g, '');
    cleaned = cleaned.replace(/```[\s\S]*?```/g, '');
    cleaned = cleaned.replace(/^\s*\[[\s\S]*?\]/, '');
    cleaned = cleaned.replace(/^\s*\{[\s\S]*?\}/, '');
    return cleaned.trim();
};

const formatTimestamp = (timestamp?: string): string => {
    if (!timestamp) return 'منذ لحظات';
    try {
        const date = new Date(timestamp);
        if (isNaN(date.getTime())) return 'منذ لحظات';
        return formatDistanceToNow(date, { addSuffix: true, locale: ar });
    } catch (error) {
        return 'منذ لحظات';
    }
};

export const ChatMessage: React.FC<ChatMessageProps> = ({
    role,
    content,
    isThinking,
    reasoning,
    variant = 'full',
    statusText,
    timestamp,
    failed,
    onRetry
}) => {
    const { user } = useAuth();
    const isUser = role === 'user';
    const [copied, setCopied] = useState(false);
    const isCompact = variant === 'compact';
    const [isExpanded, setIsExpanded] = useState(false);

    // ✅ Dynamic Agent Info
    const getAgentInfo = () => {
        if (isUser) return { name: 'المحامي', color: 'text-indigo-400', bg: 'bg-indigo-950/30' };

        // ✅ FIX: Check metadata for explicit agent name/avatar
        // You'll need to pass metadata prop or extract from reasoning if embedded
        // For now, let's use a heuristic based on content or if explicitly passed in props (we need to update props)

        // Note: Ideally, pass `agentName` prop.
        // Assuming we rely on hard defaults unless we parse it.
        // Let's look at the reasoning text? 
        // Or if we updated the backend to send metadata.

        if (reasoning?.includes('Judge') || reasoning?.includes('القاضي')) return { name: 'القاضي', color: 'text-red-400', bg: 'bg-red-950/20' };
        if (reasoning?.includes('Investigator') || reasoning?.includes('المحقق')) return { name: 'المحقق', color: 'text-amber-400', bg: 'bg-amber-950/20' };

        return {
            name: 'مارد',
            color: 'text-gold-500',
            bg: 'bg-gold-500/10'
        };
    };

    const agentInfo = getAgentInfo();

    let displayContentText = content;
    let isProcessing = false;

    // ✅ FIX: Enhanced Leak Detection & State Logic (Viva Protocol Adaptation)
    // If we detect a JSON leak, we do NOT try to clean it (it's risky).
    // Instead, we mark it as a "Format Error" and hide it behind a refined UI.
    const isLeak = role === 'assistant' && isJsonLeak(content);

    // If it's a leak, we show a friendly message. 
    // If it's empty and not thinking, we show "Complete".
    // If it's streaming (isThinking), we show "Processing".

    if (isLeak) {
        // We will handle this in the render part by showing a specific UI state
        // We don't overwrite displayContentText here to "clean" it.
        // We keep displayContentText as is, but we will render a fallback UI.
        // pass;  <-- REMOVED
    } else if (content.trim().length === 0) {
        if (isThinking) {
            isProcessing = true;
        } else {
            displayContentText = "✅ تم تحديث البيانات بنجاح.";
        }
    }

    // ... (Inside the component, we need to handle the rendering of 'isLeak')
    // Since I cannot change the Render method in this specific chunk easily without context of where variables are used,
    // I will use a local variable to control what is rendered.

    const showFormattingError = isLeak;


    const handleCopy = async () => {
        try {
            await navigator.clipboard.writeText(displayContentText);
            setCopied(true);
            toast.success('تم النسخ بنجاح');
            setTimeout(() => setCopied(false), 2000);
        } catch (error) {
            console.error('Copy failed:', error);
            try {
                const textArea = document.createElement('textarea');
                textArea.value = displayContentText;
                textArea.style.position = 'fixed';
                textArea.style.opacity = '0';
                document.body.appendChild(textArea);
                textArea.select();
                const success = document.execCommand('copy');
                document.body.removeChild(textArea);
                if (success) {
                    setCopied(true);
                    toast.success('تم النسخ بنجاح');
                    setTimeout(() => setCopied(false), 2000);
                } else {
                    toast.error('فشل النسخ');
                }
            } catch (fallbackError) {
                toast.error('المتصفح لا يدعم النسخ');
            }
        }
    };

    // ✅ FIX 2: استخدام CSS Line Clamp بدلاً من Slice البرمجي لتجنب كسر الـ Markdown
    const needsExpansion = displayContentText.length > 500;
    // لا نقوم بالقص هنا، سنترك CSS يقوم بذلك بشكل جميل

    if (isProcessing) {
        return (
            <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={cn("w-full mx-auto mb-4 px-4", isCompact ? "max-w-full" : "max-w-4xl mb-8")}
            >
                <ThinkingPulse />
            </motion.div>
        );
    }

    if (isThinking) {
        return (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className={cn("w-full mx-auto mb-4 px-4", isCompact ? "max-w-full" : "max-w-4xl mb-8")}>
                <div className="flex items-center gap-3 mb-3">
                    <div className={cn("rounded-lg bg-obsidian-800 border border-gold-500/20 flex items-center justify-center animate-pulse", isCompact ? "w-6 h-6" : "w-8 h-8")}>
                        <Sparkles className={cn("text-gold-500", isCompact ? "w-3 h-3" : "w-4 h-4")} />
                    </div>
                    <span className={cn("text-gold-500 font-medium animate-pulse", isCompact ? "text-xs" : "text-sm")}>
                        {statusText || "جاري المعالجة..."}
                    </span>
                </div>
                <div className={cn("w-full bg-obsidian-900/30 rounded-xl border border-dashed border-gray-800 animate-pulse", isCompact ? "h-16" : "h-24")} />
            </motion.div>
        );
    }

    if (isUser) {
        return (
            <div className={cn("flex w-full justify-start px-4", isCompact ? "mb-2" : "mb-4")} dir="rtl">
                <div className={cn("flex gap-3 w-full", isCompact ? "max-w-[95%]" : "max-w-[85%] md:max-w-[70%]")}>
                    <div className="flex flex-col items-start w-full">
                        {/* User Name Header */}
                        <div className="flex items-center gap-2 mb-1 mr-1">
                            <div className="w-5 h-5 rounded-md bg-indigo-500/20 flex items-center justify-center border border-indigo-500/30">
                                <User className="w-3 h-3 text-indigo-400" />
                            </div>
                            <span className="text-xs font-bold text-indigo-300">المحامي {user?.full_name || "أحمد مرجان"}</span>
                            <span className="text-[10px] text-gray-600">|</span>
                            <span className="text-[10px] text-gray-500">{formatTimestamp(timestamp)}</span>
                        </div>

                        {/* User Message Bubble: Matching Agent Style (Border + Glow) */}
                        <div className={cn(
                            "relative bg-obsidian-900/40 backdrop-blur-sm text-gray-200 rounded-2xl rounded-tr-none shadow-sm border border-gold-500/10",
                            "leading-relaxed",
                            isCompact ? "px-3 py-2 text-xs" : "px-4 py-3 text-sm", // Smaller fonts
                            failed && "border-red-500/50 bg-red-950/20"
                        )}>
                            {content}
                            {failed && (
                                <div className="flex items-center gap-2 mt-2 pt-2 border-t border-red-500/20">
                                    <AlertCircle className="w-3 h-3 text-red-400" />
                                    <span className="text-xs text-red-400">فشل الإرسال</span>
                                    {onRetry && (
                                        <button onClick={onRetry} className="text-xs text-red-400 hover:text-red-300 underline flex items-center gap-1">
                                            <RotateCcw className="w-3 h-3" />
                                            إعادة المحاولة
                                        </button>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className={cn("w-full px-2 group", isCompact ? "mb-4" : "mb-6")}>
            {/* ThinkingProcess for historical/static reasoning */}
            {reasoning && <ThinkingProcess reasoning={reasoning} />}

            <div className={cn("flex gap-4 mx-auto", isCompact ? "max-w-full" : "w-full")}>
                {!isCompact && (
                    <div className="flex flex-col items-center gap-1 shrink-0 pt-1">
                        <div className={cn("w-8 h-8 rounded-lg flex items-center justify-center bg-obsidian-800/50 shadow-sm border border-white/5")}>
                            <Bot className={cn("w-4 h-4 text-gold-500/80")} />
                        </div>
                    </div>
                )}

                <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-2">
                            <h3 className={cn("font-bold text-gold-500/90", isCompact ? "text-xs" : "text-sm")}>{agentInfo.name}</h3>
                        </div>
                        <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button onClick={handleCopy} className="p-1 hover:bg-white/5 rounded text-gray-500 hover:text-white transition-colors" aria-label="نسخ النص">
                                {copied ? <Check className="w-3 h-3 text-green-500" /> : <Copy className="w-3 h-3" />}
                            </button>
                        </div>
                    </div>

                    {/* AI Message Bubble: Restored Visible Container */}
                    <div className={cn(
                        "relative bg-obsidian-900/40 backdrop-blur-sm rounded-2xl rounded-tl-none shadow-sm border border-gold-500/10 p-4",
                        "prose prose-invert max-w-none",
                        "prose-p:text-gray-300 prose-p:leading-relaxed prose-p:my-1.5",
                        "prose-headings:text-gold-50 prose-headings:font-bold prose-headings:mb-2 prose-headings:mt-3",
                        "prose-strong:text-gold-400 prose-strong:font-bold",
                        "prose-ul:my-1 prose-ol:my-1 prose-li:my-0.5",
                        "prose-blockquote:border-r-gold-500/30 prose-blockquote:bg-obsidian-800/30 prose-blockquote:py-1 prose-blockquote:pr-3 prose-blockquote:my-2",
                        "prose-code:text-gold-300 prose-code:bg-obsidian-900/50 prose-code:px-1 prose-code:rounded prose-code:text-[10px] prose-code:font-mono",
                        "prose-pre:bg-obsidian-950/50 prose-pre:border prose-pre:border-gray-800/50 prose-pre:rounded-lg prose-pre:shadow-inner",
                        isCompact ? "prose-xs" : "prose-sm text-sm",
                        !isExpanded && needsExpansion && "line-clamp-8"
                    )}>
                        {showFormattingError ? (
                            <div className="rounded-lg bg-red-950/10 border border-red-500/10 p-3 text-right" dir="rtl">
                                <div className="flex items-center gap-2 text-red-400 mb-1">
                                    <AlertCircle className="w-3 h-3" />
                                    <span className="font-bold text-xs">بيانات تقنية</span>
                                </div>
                                <button
                                    onClick={() => setIsExpanded(!isExpanded)}
                                    className="text-[10px] text-red-500/70 hover:text-red-400 underline"
                                >
                                    {isExpanded ? "إخفاء" : "عرض"}
                                </button>
                                {isExpanded && (
                                    <pre className="mt-2 p-2 bg-black/30 rounded text-[10px] text-gray-500 overflow-x-auto font-mono text-left" dir="ltr">
                                        {content}
                                    </pre>
                                )}
                            </div>
                        ) : (
                            <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeSanitize]} components={{
                                a: ({ href, children }) => (
                                    <a href={href} target="_blank" rel="noopener noreferrer" className="text-gold-400 hover:underline">
                                        {children}
                                    </a>
                                ),
                                code: ({ inline, children, ...props }: any) => {
                                    if (inline) {
                                        return <code className="bg-obsidian-900/50 px-1 py-0.5 rounded text-[11px]" {...props}>{children}</code>;
                                    }
                                    return (
                                        <pre className="bg-obsidian-950/50 p-3 rounded-lg overflow-x-auto border border-white/5 my-2 shadow-inner">
                                            <code {...props}>{children}</code>
                                        </pre>
                                    );
                                }
                            }}>
                                {displayContentText}
                            </ReactMarkdown>
                        )}
                    </div>

                    {needsExpansion && (
                        <button
                            onClick={() => setIsExpanded(!isExpanded)}
                            className="text-gold-500/50 text-[10px] mt-1 hover:text-gold-400 flex items-center gap-1 transition-colors"
                        >
                            {isExpanded ? <span>عرض أقل <ChevronUp className="w-3 h-3 inline" /></span> : <span>قراءة المزيد <ChevronDown className="w-3 h-3 inline" /></span>}
                        </button>
                    )}

                    {!isCompact && (
                        <span className="text-[10px] text-gray-600 mt-2 flex items-center gap-1 opacity-50">
                            <Clock className="w-3 h-3" />
                            {formatTimestamp(timestamp)}
                        </span>
                    )}
                </div>
            </div>
        </div>
    );
};