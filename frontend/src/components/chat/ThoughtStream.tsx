import React, { useState, useEffect } from 'react';
import { ChevronDown, Search, PenTool, Brain, CheckCircle2, Clock } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '../../lib/utils';

export interface ThoughtStep {
    id: string; // generated client side or from backend
    content: string;
    timestamp: number;
    type: 'thought' | 'tool' | 'system';
}

interface ThoughtStreamProps {
    status: string | null;
    logs: ThoughtStep[];
    isThinking: boolean;
}

export function ThoughtStream({ status, logs, isThinking }: ThoughtStreamProps) {
    const [isExpanded, setIsExpanded] = useState(false);

    // Auto-expand on new logs if not explicitly closed? 
    // Or just keep it subtle. User asked for "pulsing bar".

    if (!isThinking && logs.length === 0) return null;

    // Determine current icon based on status text
    const getIcon = (txt: string) => {
        if (!txt) return Brain;
        if (txt.includes('بحث') || txt.includes('Searching')) return Search;
        if (txt.includes('صياغة') || txt.includes('Drafting')) return PenTool;
        return Brain;
    };

    const CurrentIcon = getIcon(status || '');

    return (
        <div className="w-full max-w-4xl mx-auto mb-2 px-4 z-10 relative">
            <div className="bg-obsidian-900/80 backdrop-blur-md border border-gray-800 rounded-xl overflow-hidden shadow-lg transition-all duration-300">
                {/* Main Status Bar */}
                <div
                    onClick={() => setIsExpanded(!isExpanded)}
                    className="flex items-center justify-between p-3 cursor-pointer hover:bg-white/5 transition-colors"
                >
                    <div className="flex items-center gap-3">
                        <div className={cn(
                            "w-2 h-2 rounded-full",
                            isThinking ? "bg-gold-500 animate-pulse" : "bg-green-500"
                        )} />

                        <div className="flex items-center gap-2 text-sm text-gray-300 font-medium">
                            {isThinking ? (
                                <>
                                    <CurrentIcon className="w-4 h-4 text-gold-500 animate-bounce-slow" />
                                    <span className="animate-pulse">{status || 'جاري المعالجة...'}</span>
                                </>
                            ) : (
                                <>
                                    <CheckCircle2 className="w-4 h-4 text-green-500" />
                                    <span>مكتمل</span>
                                </>
                            )}
                        </div>
                    </div>

                    <div className="flex items-center gap-2">
                        <span className="text-[10px] text-gray-500 bg-black/20 px-2 py-0.5 rounded-full font-mono">
                            {logs.length} steps
                        </span>
                        <ChevronDown className={cn(
                            "w-4 h-4 text-gray-400 transition-transform duration-300",
                            isExpanded && "rotate-180"
                        )} />
                    </div>
                </div>

                {/* Expanded Log View */}
                <AnimatePresence>
                    {isExpanded && (
                        <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="border-t border-gray-800/50 bg-black/20"
                        >
                            <div className="p-3 space-y-2 max-h-60 overflow-y-auto scrollbar-thin">
                                {logs.map((log) => (
                                    <div key={log.id} className="flex gap-3 text-xs text-gray-400 font-mono items-start">
                                        <span className="text-gray-600 shrink-0">
                                            {new Date(log.timestamp).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                                        </span>
                                        <span className={cn(
                                            log.type === 'tool' && "text-blue-400",
                                            log.type === 'thought' && "text-gold-500/80"
                                        )}>
                                            {log.type === 'tool' ? '🔧 ' : '💭 '}
                                            {log.content}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
}
