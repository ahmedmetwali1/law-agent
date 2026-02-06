import React, { useState } from 'react';
import { MessageSquare, ArrowLeft, Send } from 'lucide-react';
import { motion } from 'framer-motion';

interface DecisionCardProps {
    question: string;
    onAnswer: (answer: string) => void;
}

export function DecisionCard({ question, onAnswer }: DecisionCardProps) {
    const [answer, setAnswer] = useState('');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (answer.trim()) {
            onAnswer(answer);
        }
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            className="my-4 mx-auto max-w-2xl w-full"
        >
            <div className="bg-obsidian-900 border border-gold-500/30 rounded-2xl overflow-hidden shadow-2xl ring-1 ring-gold-500/20">
                {/* Header */}
                <div className="bg-gradient-to-r from-gold-500/10 to-transparent p-4 border-b border-gold-500/10 flex items-center gap-3">
                    <div className="bg-gold-500/20 p-2 rounded-lg">
                        <MessageSquare className="w-5 h-5 text-gold-500" />
                    </div>
                    <div>
                        <h3 className="font-bold text-gray-200 text-sm">مطلوب توضيح</h3>
                        <p className="text-[10px] text-gold-500/80">المساعد يحتاج لمعلومة إضافية للمتابعة</p>
                    </div>
                </div>

                {/* Question Body */}
                <div className="p-6">
                    <p className="text-lg text-white font-medium leading-relaxed mb-6 bg-black/20 p-4 rounded-xl border border-gray-800">
                        {question}
                    </p>

                    <form onSubmit={handleSubmit} className="flex gap-3">
                        <input
                            autoFocus
                            type="text"
                            value={answer}
                            onChange={(e) => setAnswer(e.target.value)}
                            placeholder="اكتب إجابتك هنا..."
                            className="flex-1 bg-obsidian-950 border border-gray-700 rounded-xl px-4 py-3 text-white focus:border-gold-500 focus:ring-1 focus:ring-gold-500 transition-all shadow-inner"
                        />
                        <button
                            type="submit"
                            disabled={!answer.trim()}
                            className="bg-gold-500 hover:bg-gold-400 text-black font-bold px-6 rounded-xl flex items-center gap-2 transition-transform active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            <span>إرسال</span>
                            <ArrowLeft className="w-4 h-4" />
                        </button>
                    </form>
                </div>
            </div>
        </motion.div>
    );
}
