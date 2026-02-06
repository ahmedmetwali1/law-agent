import React from 'react';

interface CitationBlockProps {
    text: string;
}

export const CitationBlock: React.FC<CitationBlockProps> = ({ text }) => {
    // Regex matches: "استناداً للمادة" or "المبدأ:" or "حكم"
    // Also matches typical citation patterns if we want to parse specific parts
    // For now, we wrap the whole text in the block style as requested for paragraphs containing citations

    return (
        <div className="my-3 pl-4 border-r-4 border-r-gold-400 bg-gold-50/30 p-3 rounded-l-md italic text-gray-700 leading-relaxed text-right dir-rtl">
            {text}
        </div>
    );
};

export const FormatWithCitations: React.FC<{ content: string }> = ({ content }) => {
    // Split by newlines to process paragraphs
    const paragraphs = content.split('\n');

    return (
        <div className="space-y-2">
            {paragraphs.map((p, idx) => {
                const isCitation = p.includes('استناداً') || p.includes('تنص') || p.includes('مبدأ');
                if (isCitation) {
                    return <CitationBlock key={idx} text={p} />;
                }
                // Return normal paragraph
                // Check if empty
                if (!p.trim()) return <div key={idx} className="h-2" />;
                return <p key={idx} className="text-gray-800 leading-relaxed">{p}</p>;
            })}
        </div>
    );
};
