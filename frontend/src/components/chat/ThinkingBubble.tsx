import React, { useState } from 'react';
import {
    Brain,
    ChevronDown,
    Sparkles,
    Microscope,
    ListTree,
    Zap,
    Terminal
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { cn } from '../../lib/utils';
// Assuming a MarkdownRenderer component exists
// import { MarkdownRenderer } from './MarkdownRenderer'; 

interface ThinkingBubbleProps {
    content: string;
    metadata?: {
        node?: 'analyze' | 'plan' | 'execute' | 'format';
        action?: string;
    };
}

export function ThinkingBubble({ content, metadata }: ThinkingBubbleProps) {
    const [isExpanded, setIsExpanded] = useState(false);
    const node = metadata?.node;
    const action = metadata?.action;

    // Extract <thought> tags
    const thoughts = extractThoughts(content);
    const cleanContent = content.replace(/<thought>.*?<\/thought>/gs, '').trim();

    const nodeConfig = {
        analyze: {
            icon: Microscope,
            label: 'تحليل المتطلبات',
            color: 'from-purple-500 to-indigo-600',
            glow: 'shadow-purple-500/20'
        },
        plan: {
            icon: ListTree,
            label: 'رسم الخطة الاستراتيجية',
            color: 'from-blue-500 to-cyan-600',
            glow: 'shadow-blue-500/20'
        },
        execute: {
            icon: Zap,
            label: 'تنفيذ العمليات',
            color: 'from-amber-500 to-orange-600',
            glow: 'shadow-amber-500/20'
        },
        format: {
            icon: Sparkles,
            label: 'صياغة الرد النهائي',
            color: 'from-emerald-500 to-teal-600',
            glow: 'shadow-emerald-500/20'
        }
    };

    const config = nodeConfig[node as keyof typeof nodeConfig] || nodeConfig.format;
    const Icon = config.icon;

    if (!thoughts.length && !cleanContent) return null;

    return (
        <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="group max-w-[85%] mb-4"
        >
            {/* Node Header Indicator */}
            <div className="flex items-center gap-2.5 mb-2 ml-4">
                <div className={cn(
                    "p-1.5 rounded-lg bg-gradient-to-br shadow-lg transition-transform group-hover:scale-110 duration-300",
                    config.color,
                    config.glow
                )}>
                    <Icon className="w-3.5 h-3.5 text-white" />
                </div>
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                    {config.label}
                </span>
            </div>

            <div className="relative">
                {/* Internal Thought (Collapsible) */}
                {thoughts.length > 0 && (
                    <div className="mb-2">
                        <button
                            onClick={() => setIsExpanded(!isExpanded)}
                            className="group/btn flex items-center gap-2 text-[10px] text-slate-500 hover:text-purple-400 transition-colors bg-slate-900/40 px-3 py-1.5 rounded-full border border-slate-800/50 hover:border-purple-500/30"
                        >
                            <Brain className={cn("w-3 h-3 transition-transform", isExpanded && "scale-110 text-purple-400")} />
                            <span className="font-medium">التفكير المنطقي الداخلي</span>
                            <ChevronDown className={cn("w-3 h-3 transition-transform duration-300", isExpanded && "rotate-180")} />
                        </button>

                        <AnimatePresence>
                            {isExpanded && (
                                <motion.div
                                    initial={{ height: 0, opacity: 0, scale: 0.95 }}
                                    animate={{ height: 'auto', opacity: 1, scale: 1 }}
                                    exit={{ height: 0, opacity: 0, scale: 0.95 }}
                                    className="overflow-hidden mt-2"
                                >
                                    <div className="bg-slate-900/60 backdrop-blur-sm border border-slate-800/80 rounded-2xl p-4 shadow-inner">
                                        {thoughts.map((thought, idx) => (
                                            <p key={idx} className="text-[11px] text-slate-400 italic leading-relaxed mb-2 last:mb-0 pr-4 border-r border-purple-500/20">
                                                {thought}
                                            </p>
                                        ))}
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>
                )}

                {/* Narrative Content (The actual text shown while thinking) */}
                {cleanContent && (
                    <div className="bg-gradient-to-br from-slate-900/90 to-slate-800/60 backdrop-blur-md border border-slate-700/40 rounded-3xl p-4 shadow-xl ring-1 ring-white/5">
                        <div className="prose prose-sm prose-invert max-w-none break-words" dir="auto">
                            <Markdown
                                remarkPlugins={[remarkGfm]}
                                components={{
                                    p: ({ children }) => <p className="mb-2 last:mb-0 text-xs text-slate-200">{children}</p>,
                                    code: ({ children }) => <code className="bg-black/30 px-1 py-0.5 rounded text-gold-300 font-mono text-[10px]">{children}</code>
                                }}
                            >
                                {cleanContent}
                            </Markdown>
                        </div>
                    </div>
                )}

                {/* Technical Metadata Footer */}
                {action && (
                    <div className="flex items-center gap-2 mt-2 ml-4">
                        <div className="px-2 py-0.5 rounded bg-slate-900/50 border border-slate-800 text-[9px] font-mono text-slate-500 flex items-center gap-1.5">
                            <Terminal className="w-2.5 h-2.5" />
                            {action}
                        </div>
                    </div>
                )}
            </div>
        </motion.div>
    );
}

function extractThoughts(content: string): string[] {
    const matches = content.matchAll(/<thought>(.*?)<\/thought>/gs);
    return Array.from(matches, m => m[1].trim());
}
