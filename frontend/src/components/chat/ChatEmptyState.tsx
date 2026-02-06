import React from 'react';
import { motion } from 'framer-motion';
import { Scale, FileText, Users, Calendar, ArrowRight, Sparkles } from 'lucide-react';

interface ChatEmptyStateProps {
    onSuggestionClick: (text: string) => void;
}

const SUGGESTIONS = [
    {
        icon: Users,
        title: "إحصائيات الموكلين",
        prompt: "كم عدد الموكلين النشطين حالياً؟",
        color: "text-blue-400",
        bg: "bg-blue-400/10"
    },
    {
        icon: Calendar,
        title: "الجلسات القادمة",
        prompt: "ما هي جلسات المحكمة المجدولة لهذا الأسبوع؟",
        color: "text-purple-400",
        bg: "bg-purple-400/10"
    },
    {
        icon: FileText,
        title: "آخر المستجدات",
        prompt: "لخص لي آخر التحديثات في القضايا الجارية",
        color: "text-green-400",
        bg: "bg-green-400/10"
    },
    {
        icon: Scale,
        title: "بحث قانوني",
        prompt: "ابحث عن سوابق قضائية بخصوص فسخ عقد العمل",
        color: "text-gold-500",
        bg: "bg-gold-500/10"
    }
];

export const ChatEmptyState: React.FC<ChatEmptyStateProps> = ({ onSuggestionClick }) => {
    return (
        <div className="flex flex-col items-center justify-center p-6 h-full max-w-4xl mx-auto">
            {/* Header */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center mb-12"
            >
                <div className="w-20 h-20 bg-gradient-to-br from-gold-500/20 to-amber-600/20 rounded-3xl flex items-center justify-center mx-auto mb-6 shadow-xl shadow-gold-500/5 border border-gold-500/20">
                    <Scale className="w-10 h-10 text-gold-500" />
                </div>
                <h1 className="text-3xl font-bold text-white mb-3">
                    مرحباً بك في <span className="text-gold-500">نظام المحامي الذكي</span>
                </h1>
                <p className="text-gray-400 max-w-lg mx-auto leading-relaxed">
                    أنا وكيلك الذكي، جاهز لمساعدتك في إدارة القضايا، البحث القانوني، وصياغة العقود.
                    كيف يمكنني مساعدتك اليوم؟
                </p>
            </motion.div>

            {/* Suggestions Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full">
                {SUGGESTIONS.map((item, idx) => (
                    <motion.button
                        key={idx}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: idx * 0.1 + 0.2 }}
                        onClick={() => onSuggestionClick(item.prompt)}
                        className="group flex items-center gap-4 p-4 rounded-2xl bg-obsidian-800/50 border border-gray-800 hover:border-gold-500/30 hover:bg-obsidian-800 transition-all text-right"
                    >
                        <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${item.bg}`}>
                            <item.icon className={`w-6 h-6 ${item.color}`} />
                        </div>
                        <div className="flex-1">
                            <h3 className="text-white font-bold mb-1 group-hover:text-gold-500 transition-colors">
                                {item.title}
                            </h3>
                            <p className="text-xs text-gray-500">
                                {item.prompt}
                            </p>
                        </div>
                        <ArrowRight className="w-5 h-5 text-gray-600 group-hover:text-gold-500 -translate-x-2 opacity-0 group-hover:opacity-100 group-hover:translate-x-0 transition-all" />
                    </motion.button>
                ))}
            </div>

            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 1 }}
                className="mt-12 flex items-center gap-2 text-xs text-gray-600"
            >
                <Sparkles className="w-3 h-3" />
                <span>مدعوم بأحدث تقنيات الذكاء الاصطناعي القانوني</span>
            </motion.div>
        </div>
    );
};
