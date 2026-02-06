import React from 'react';
import { useChatStore } from '@/stores/chatStore';
import { Loader2, Sparkles, Brain, Search, Gavel, Radio, Radar } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export const GoldenReasoningBox: React.FC = () => {
    const { currentActivity } = useChatStore();

    if (!currentActivity.isThinking || currentActivity.stage === 'IDLE') return null;

    // Determine Icon based on Stage
    const getStageConfig = () => {
        switch (currentActivity.stage) {
            case 'ROUTING': return { icon: Sparkles, label: 'توجيه', color: 'text-indigo-400' };
            case 'INVESTIGATING': return { icon: Search, label: 'بحث', color: 'text-blue-400' };
            case 'DELIBERATING': return { icon: Brain, label: 'تفكير', color: 'text-purple-400' };
            case 'VERDICT': return { icon: Gavel, label: 'حكم', color: 'text-emerald-400' };
            default: return { icon: Radio, label: 'معالجة', color: 'text-gold-400' };
        }
    };

    const config = getStageConfig();
    const Icon = config.icon;

    return (
        <AnimatePresence>
            <motion.div
                key="radar-box"
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                className="w-full flex flex-col items-center justify-center my-6 gap-4"
            >
                {/* 📡 Radar Circle */}
                <div className="relative w-24 h-24 flex items-center justify-center">

                    {/* Ring 1 (Pulse) */}
                    <motion.div
                        className={`absolute inset-0 rounded-full border-2 border-dashed ${config.color.replace('text-', 'border-')}/30`}
                        animate={{ rotate: 360, scale: [1, 1.05, 1] }}
                        transition={{ duration: 10, repeat: Infinity, ease: "linear" }}
                    />

                    {/* Ring 2 (Sonar Scan) */}
                    <div className="absolute inset-0 rounded-full overflow-hidden">
                        <motion.div
                            className={`absolute inset-[-50%] bg-[conic-gradient(from_0deg,transparent_0_300deg,currentColor_360deg)] ${config.color.replace('text-', 'text-')}/40`}
                            animate={{ rotate: 360 }}
                            transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
                            style={{ borderRadius: "40%" }} // Soften edges
                        />
                    </div>

                    {/* Core Circle */}
                    <div className="relative z-10 w-16 h-16 bg-obsidian-950 rounded-full border border-gray-800 flex items-center justify-center shadow-2xl shadow-black/50">
                        <Icon className={`w-8 h-8 ${config.color} animate-pulse`} />
                    </div>
                </div>

                {/* 📝 Status Text (Floating below) */}
                <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    key={currentActivity.action}
                    className="flex flex-col items-center gap-1"
                >
                    <span className={`text-xs font-bold tracking-widest uppercase ${config.color}`}>
                        {config.label}
                    </span>
                    <span className="text-sm text-gray-400 font-medium max-w-md text-center px-4 leading-relaxed">
                        {currentActivity.action}
                    </span>
                </motion.div>

            </motion.div>
        </AnimatePresence>
    );
};
