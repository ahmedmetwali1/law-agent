import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, ChevronDown, ChevronUp, Terminal } from 'lucide-react';

interface ToolAccordionProps {
    content: string;
    toolName?: string;
}

export const ToolAccordion: React.FC<ToolAccordionProps> = ({ content, toolName = "System Tool" }) => {
    const [isOpen, setIsOpen] = useState(false);

    // Parse content if JSON for pretty printing
    let displayContent = content;
    try {
        const json = JSON.parse(content);
        displayContent = JSON.stringify(json, null, 2);
    } catch (e) {
        // Not JSON, keep as text
    }

    return (
        <div className="w-full my-1 px-4 md:px-12 flex justify-start">
            <div className={`
                transition-all duration-300 rounded-lg overflow-hidden border
                ${isOpen ? 'w-full bg-obsidian-900 border-gray-700' : 'w-auto bg-green-950/20 border-green-800/30 hover:bg-green-950/40'}
            `}>
                <button
                    onClick={() => setIsOpen(!isOpen)}
                    className="flex items-center gap-2 px-3 py-1.5 text-xs text-green-400/80 hover:text-green-300 transition-colors"
                    title="انقر لعرض التفاصيل التقنية"
                >
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span className="font-medium">
                        تم التنفيذ: {toolName}
                    </span>
                    {isOpen ? <ChevronUp className="w-3 h-3 opacity-50" /> : <ChevronDown className="w-3 h-3 opacity-50" />}
                </button>

                <AnimatePresence>
                    {isOpen && (
                        <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: "auto", opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            transition={{ duration: 0.2 }}
                        >
                            <div className="px-3 py-2 border-t border-gray-800 bg-black/40">
                                <div className="flex items-center gap-1 text-[10px] text-gray-500 mb-1">
                                    <Terminal className="w-3 h-3" />
                                    <span>المخرجات التقنية:</span>
                                </div>
                                <pre className="text-[10px] text-gray-400 font-mono overflow-x-auto whitespace-pre-wrap max-h-60 scrollbar-thin">
                                    {displayContent}
                                </pre>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
};
