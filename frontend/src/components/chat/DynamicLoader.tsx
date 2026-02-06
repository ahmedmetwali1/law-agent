import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, Loader2 } from 'lucide-react';

const LOADING_MESSAGES = [
    "جاري تحليل الطلب...",
    "البحث في القواعد القانونية...",
    "مراجعة السوابق القضائية...",
    "صياغة الرد القانوني...",
    "المراجعة والتدقيق النهائي..."
];

interface DynamicLoaderProps {
    realtimeStatus?: string | null;
}

export const DynamicLoader: React.FC<DynamicLoaderProps> = ({ realtimeStatus }) => {
    const [msgIndex, setMsgIndex] = useState(0);

    useEffect(() => {
        if (realtimeStatus) return; // Stop cycling if we have real status

        const interval = setInterval(() => {
            setMsgIndex((prev) => (prev + 1) % LOADING_MESSAGES.length);
        }, 3000);
        return () => clearInterval(interval);
    }, [realtimeStatus]);

    const currentMessage = realtimeStatus || LOADING_MESSAGES[msgIndex];

    return (
        <div className="flex items-start gap-3 w-full animate-fade-in py-4">
            <div className="w-8 h-8 rounded-lg bg-gold-500/10 flex items-center justify-center shrink-0 border border-gold-500/20">
                <Sparkles className="w-4 h-4 text-gold-500 animate-pulse" />
            </div>

            <div className="flex flex-col gap-2 pt-1.5">
                <div className="h-2 w-full max-w-[200px] overflow-hidden rounded-full bg-obsidian-800">
                    <motion.div
                        className="h-full bg-gold-500"
                        initial={{ width: "0%" }}
                        animate={{ width: "100%" }}
                        transition={{
                            duration: 2.5,
                            repeat: Infinity,
                            repeatType: "reverse",
                            ease: "easeInOut"
                        }}
                    />
                </div>

                <AnimatePresence mode='wait'>
                    <motion.p
                        key={currentMessage} // Animate when text changes
                        initial={{ opacity: 0, y: 5 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -5 }}
                        transition={{ duration: 0.3 }}
                        className="text-xs text-gold-500/80 font-medium font-mono"
                    >
                        {currentMessage}
                    </motion.p>
                </AnimatePresence>
            </div>
        </div>
    );
};
