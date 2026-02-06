import React from 'react';
import { motion } from 'framer-motion';

const LOADING_PHRASES = [
    "جاري المعالجة...",
    "النظام يعمل...",
    "تحليل الطلب..."
];

interface PulsingLoaderProps {
    realtimeStatus?: string | null;
}

export const PulsingLoader: React.FC<PulsingLoaderProps> = ({ realtimeStatus }) => {
    // If realtimeStatus is present (detailed tool status), we ignore it for the text
    // as per the new requirement for minimalist design. 
    // We only cycle through generic phrases.

    // Optional: We could still show the detailed status on hover, 
    // but the requirement is "The user finds text details distracting".
    // So distinct phrases are used cyclically or just one static phrase.
    // Let's implement a simple cycle for the "Alive" feel.

    const [phraseIndex, setPhraseIndex] = React.useState(0);

    React.useEffect(() => {
        const interval = setInterval(() => {
            setPhraseIndex((prev) => (prev + 1) % LOADING_PHRASES.length);
        }, 2500);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="flex flex-col items-center justify-center w-full py-6 space-y-4 animate-fade-in">
            {/* The Pulsing Brain / Orb */}
            <div className="relative flex items-center justify-center">
                {/* Outer Glow Ring */}
                <motion.div
                    className="absolute w-12 h-12 rounded-full bg-gold-500/20 shadow-lg shadow-gold-500/20"
                    animate={{
                        scale: [1, 1.5, 1],
                        opacity: [0.3, 0.1, 0.3]
                    }}
                    transition={{
                        duration: 2,
                        repeat: Infinity,
                        ease: "easeInOut"
                    }}
                />

                {/* Core Circle */}
                <motion.div
                    className="w-4 h-4 rounded-full bg-gold-500 shadow-[0_0_15px_rgba(234,179,8,0.6)]"
                    animate={{
                        scale: [1, 1.2, 1],
                        opacity: [0.8, 1, 0.8]
                    }}
                    transition={{
                        duration: 1.5,
                        repeat: Infinity,
                        ease: "easeInOut"
                    }}
                />

                {/* Orbital Ring (Spinning) */}
                <motion.div
                    className="absolute w-8 h-8 rounded-full border border-gold-500/30 border-t-gold-500"
                    animate={{ rotate: 360 }}
                    transition={{
                        duration: 1.5,
                        repeat: Infinity,
                        ease: "linear"
                    }}
                />
            </div>

            {/* Minimalist Text */}
            <motion.p
                key={phraseIndex}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="text-[10px] text-gold-500/60 font-mono tracking-widest"
            >
                {LOADING_PHRASES[phraseIndex]}
            </motion.p>
        </div>
    );
};
