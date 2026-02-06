import React, { useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useChatStore } from '@/stores/chatStore';
import { UserCog, GitBranch, ShieldCheck, Sword, Lightbulb } from 'lucide-react';

const agentIcons: Record<string, any> = {
    'Strategist': GitBranch,
    'Auditor': ShieldCheck,
    'Challenger': Sword,
    'Pragmatist': Lightbulb,
    'default': UserCog
};

const agentColors: Record<string, string> = {
    'Strategist': 'text-purple-400 border-purple-500/30 bg-purple-900/10',
    'Auditor': 'text-emerald-400 border-emerald-500/30 bg-emerald-900/10',
    'Challenger': 'text-rose-400 border-rose-500/30 bg-rose-900/10',
    'Pragmatist': 'text-amber-400 border-amber-500/30 bg-amber-900/10',
    'default': 'text-blue-400 border-blue-500/30 bg-blue-900/10'
};

export const CouncilLiveView: React.FC = () => {
    const { councilSession } = useChatStore();
    const scrollRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom of monologues
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [councilSession.monologues.length]);

    if (councilSession.monologues.length === 0) {
        return (
            <div className="h-full flex flex-col items-center justify-center text-gray-600 p-4">
                <UserCog className="w-12 h-12 mb-2 opacity-20" />
                <p className="text-sm">غرفة المداولة فارغة حالياً</p>
            </div>
        );
    }

    return (
        <div className="flex flex-col h-full bg-obsidian-950/50 backdrop-blur-sm border-r border-gray-800">
            <div className="p-3 border-b border-gray-800 bg-obsidian-950/80 sticky top-0 z-10">
                <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span>
                    غرفة المداولة (Live)
                </h3>
            </div>

            <div ref={scrollRef} className="flex-1 overflow-y-auto p-3 space-y-3 scrollbar-thin scrollbar-thumb-gray-800">
                <AnimatePresence initial={false}>
                    {councilSession.monologues.map((entry) => {
                        // Normalize agent name
                        const agentKey = Object.keys(agentIcons).find(k => entry.agent.includes(k)) || 'default';
                        const Icon = agentIcons[agentKey];
                        const colorClass = agentColors[agentKey];

                        return (
                            <motion.div
                                key={entry.id}
                                initial={{ opacity: 0, x: -20, height: 0 }}
                                animate={{ opacity: 1, x: 0, height: 'auto' }}
                                exit={{ opacity: 0 }}
                                className={`p-3 rounded-lg border text-right text-sm ${colorClass}`}
                            >
                                <div className="flex items-center gap-2 mb-1 opacity-80">
                                    <Icon className="w-3 h-3" />
                                    <span className="text-xs font-bold">{entry.agent}</span>
                                    <span className="text-[10px] opacity-50 mr-auto">
                                        {entry.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                    </span>
                                </div>
                                <p className="leading-relaxed opacity-90 text-xs">
                                    {entry.content}
                                </p>
                            </motion.div>
                        );
                    })}
                </AnimatePresence>
            </div>
        </div>
    );
};
