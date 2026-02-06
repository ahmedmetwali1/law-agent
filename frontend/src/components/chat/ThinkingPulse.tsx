import React from 'react';
import { useChatStore } from '@/stores/chatStore';
import { Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export const ThinkingPulse: React.FC = () => {
    const { currentActivity } = useChatStore();

    // Only show if there is an active action but NO specific stage (fallback) 
    // OR if we want a smaller indicator. 
    // Actually, let's make this the "Micro Interaction" that was requested.
    // It can be a subtle bar that appears when `isThinking` is true.

    return (
        <AnimatePresence>
            {currentActivity.isThinking && currentActivity.stage !== 'IDLE' && (
                <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="w-full max-w-2xl mx-auto my-2 overflow-hidden relative rounded-xl bg-obsidian-900/50 border border-gold-500/10 p-3"
                    dir="rtl"
                >
                    {/* Background Wave Animation */}
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-gold-500/5 to-transparent w-[200%] animate-marquee opacity-20" />

                    <div className="relative flex items-center gap-3 z-10">
                        {/* Icon Circle */}
                        <div className="w-8 h-8 rounded-full bg-obsidian-950 border border-gold-500/20 flex items-center justify-center shrink-0 shadow-lg shadow-gold-900/10">
                            <Loader2 className="w-4 h-4 text-gold-500 animate-spin" />
                        </div>

                        {/* Text Content */}
                        <div className="flex flex-col flex-1 gap-0.5">
                            <div className="flex items-center justify-between">
                                <span className="text-[10px] font-bold text-gray-500 uppercase tracking-wider">
                                    {currentActivity.actor || "النظام"}
                                </span>
                                <span className="text-[10px] text-gold-500/70 font-mono">
                                    {currentActivity.stage}
                                </span>
                            </div>

                            <span className="text-xs text-gold-100 font-medium animate-pulse truncate">
                                {currentActivity.action || "جاري المعالجة..."}
                            </span>
                        </div>
                    </div>
                </motion.div>
            )}
        </AnimatePresence>
    );
};
