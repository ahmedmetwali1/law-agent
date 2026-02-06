import React from 'react';
import { motion } from 'framer-motion';
import { Scale, Search, Users, Gavel } from 'lucide-react';
import { useChatStore, ActivityState } from '@/stores/chatStore';

const stages = [
    { id: 'ROUTING', label: 'توجيه', icon: Scale },
    { id: 'INVESTIGATING', label: 'تحقيق', icon: Search },
    { id: 'DELIBERATING', label: 'مداولة', icon: Users },
    { id: 'VERDICT', label: 'إصدار الحكم', icon: Gavel },
];

export const StageProgressStepper: React.FC = () => {
    const { currentActivity } = useChatStore();

    // Determine active index
    const activeIndex = stages.findIndex(s => s.id === currentActivity.stage);

    // If IDLE, show nothing or full inactive
    if (currentActivity.stage === 'IDLE') return null;

    return (
        <div className="w-full bg-obsidian-900/50 backdrop-blur-md border-b border-gray-800 py-3 px-4 z-40 sticky top-0">
            <div className="max-w-3xl mx-auto flex items-center justify-between relative">

                {/* Connecting Line */}
                <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-gray-800 -z-10" />

                {stages.map((stage, index) => {
                    const isActive = index === activeIndex;
                    const isCompleted = index < activeIndex;

                    return (
                        <div key={stage.id} className="flex flex-col items-center gap-2 relative">
                            {/* Circle */}
                            <motion.div
                                className={`w-8 h-8 rounded-full flex items-center justify-center border-2 transition-colors duration-300
                                    ${isActive ? 'bg-obsidian-950 border-gold-500 text-gold-500 shadow-[0_0_15px_rgba(234,179,8,0.5)]' :
                                        isCompleted ? 'bg-emerald-900/20 border-emerald-500 text-emerald-500' :
                                            'bg-obsidian-950 border-gray-700 text-gray-700'}`}
                                animate={isActive ? { scale: [1, 1.1, 1] } : {}}
                                transition={{ repeat: isActive ? Infinity : 0, duration: 2 }}
                            >
                                <stage.icon className="w-4 h-4" />
                            </motion.div>

                            {/* Label */}
                            <span className={`text-[10px] font-medium transition-colors duration-300
                                ${isActive ? 'text-gold-500' : isCompleted ? 'text-emerald-500' : 'text-gray-600'}`}>
                                {stage.label}
                            </span>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};
