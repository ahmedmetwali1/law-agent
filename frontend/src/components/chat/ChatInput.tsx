import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, Mic, Paperclip } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ChatInputProps {
    onSend: (message: string) => void;
    isLoading: boolean;
    onVoiceClick?: () => void;
    isRecording?: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({ onSend, isLoading, onVoiceClick, isRecording }) => {
    const [input, setInput] = useState('');
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
        }
    }, [input]);

    const handleSubmit = (e?: React.FormEvent) => {
        e?.preventDefault();
        if (!input.trim() || isLoading) return;
        onSend(input);
        setInput('');
        if (textareaRef.current) textareaRef.current.style.height = 'auto';
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit();
        }
    };

    return (
        <div className="px-4 pb-6 pt-2 bg-obsidian-950 sticky bottom-0 z-10 w-full max-w-6xl mx-auto">
            <div className="relative flex items-end gap-2 bg-obsidian-900 border border-gray-800 rounded-xl p-2 shadow-sm focus-within:border-gold-500/30 transition-all">

                <div className="flex gap-1 mb-0.5">
                    <button className="p-2 text-gray-500 hover:text-white hover:bg-gray-800 rounded-lg transition-colors" title="إرفاق ملف">
                        <Paperclip className="w-4 h-4" />
                    </button>
                    <button
                        onClick={onVoiceClick}
                        className={cn(
                            "p-2 rounded-lg transition-colors",
                            isRecording
                                ? "text-red-500 bg-red-500/10 hover:bg-red-500/20 animate-pulse"
                                : "text-gray-500 hover:text-white hover:bg-gray-800"
                        )}
                        title={isRecording ? "إيقاف التسجيل" : "تسجيل صوتي"}
                    >
                        <Mic className="w-4 h-4" />
                    </button>
                </div>

                <textarea
                    ref={textareaRef}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="اكتب رسالتك هنا..."
                    rows={1}
                    className="flex-1 bg-transparent border-none focus:ring-0 resize-none py-2.5 text-sm text-gray-200 placeholder:text-gray-600 min-h-[40px] max-h-[120px] scrollbar-thin scrollbar-thumb-gray-700 leading-relaxed"
                    dir="rtl"
                />

                <button
                    onClick={() => handleSubmit()}
                    disabled={!input.trim() || isLoading}
                    className={cn(
                        "p-2 rounded-lg transition-all duration-200 mb-0.5 shrink-0",
                        input.trim() && !isLoading
                            ? "bg-gold-500 text-obsidian-950 hover:bg-gold-400 shadow-sm"
                            : "bg-gray-800 text-gray-600 cursor-not-allowed"
                    )}
                >
                    {isLoading ? (
                        <div className="flex items-center gap-2">
                            <Sparkles className="w-4 h-4 animate-spin" />
                        </div>
                    ) : (
                        <Send className="w-4 h-4 transform rotate-180" />
                    )}
                </button>
            </div>

            {/* Disclaimer: Brighter and Readable */}
            <div className="text-center mt-3">
                <p className="text-[11px] text-gold-500/70 bg-gold-900/10 py-1 px-3 rounded-full inline-block border border-gold-500/20">
                    ⚠️ يمكن للمساعد الذكي ارتكاب الأخطاء. يرجى التحقق من المعلومات الهامة.
                </p>
            </div>
        </div>
    );
};
