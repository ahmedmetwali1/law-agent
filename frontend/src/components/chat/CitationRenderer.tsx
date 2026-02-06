import React from 'react';
import { BookOpen } from 'lucide-react';

interface CitationRendererProps {
    text: string;
}

export function CitationRenderer({ text }: CitationRendererProps) {
    const parts = text.split(/(\[المصدر:.*?,?.*?\])/g);

    return (
        <span>
            {parts.map((part, i) => {
                const match = part.match(/\[المصدر:\s*(.*?)(?:,\s*مادة\s*(.*?))?\]/);

                if (match) {
                    const source = match[1];
                    const article = match[2];

                    return (
                        <span key={i} className="group relative inline-block mx-1 align-middle">
                            <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-gold-500/10 text-gold-500 border border-gold-500/20 cursor-help hover:bg-gold-500/20 transition-colors text-[10px] font-bold font-mono">
                                <BookOpen className="w-3 h-3" />
                                {article ? `مادة ${article}` : source}
                            </span>

                            {/* Custom Tooltip */}
                            <span className="invisible opacity-0 group-hover:visible group-hover:opacity-100 transition-all duration-200 absolute bottom-full mb-2 left-1/2 -translate-x-1/2 px-3 py-2 bg-obsidian-900/95 backdrop-blur-sm border border-gold-500/30 text-white text-xs rounded-lg shadow-xl w-48 z-50 pointer-events-none">
                                <span className="block font-bold text-gold-500 mb-1 border-b border-gold-500/20 pb-1">{source}</span>
                                {article && <span className="block text-gray-300 font-mono text-[10px] mt-1">المادة {article}</span>}
                                <span className="block text-[9px] text-gray-500 mt-2 italic">
                                    انقر للبحث عن النص الكامل في المرجع.
                                </span>
                                {/* Arrow */}
                                <span className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-obsidian-900/95"></span>
                            </span>
                        </span>
                    );
                }

                return <span key={i}>{part}</span>;
            })}
        </span>
    );
}
