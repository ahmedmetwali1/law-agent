import { motion } from 'framer-motion'
import { BookOpen, Construction } from 'lucide-react'

export function KnowledgeBasePage() {
    return (
        <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-6 bg-obsidian-900/50 rounded-3xl border border-gray-800">
            <motion.div
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ duration: 0.5 }}
                className="relative"
            >
                <div className="absolute inset-0 bg-gold-500/20 blur-3xl rounded-full" />
                <BookOpen className="w-32 h-32 text-gold-500 relative z-10 mb-6" />
                <Construction className="w-12 h-12 text-gray-400 absolute -bottom-2 -right-2 z-20 bg-obsidian-900 rounded-full p-2 border border-gray-700" />
            </motion.div>

            <motion.h1
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.2 }}
                className="text-4xl font-bold bg-gradient-to-r from-gold-400 via-gold-200 to-gold-500 bg-clip-text text-transparent mb-4"
            >
                قاعدة المعرفة القانونية
            </motion.h1>

            <motion.p
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.3 }}
                className="text-xl text-gray-400 max-w-lg mx-auto leading-relaxed"
            >
                نعمل حالياً على بناء مكتبة قانونية ذكية مدعومة بالذكاء الاصطناعي لمساعدتك في البحث والاستشارة.
            </motion.p>

            <motion.div
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.4 }}
                className="mt-8 px-6 py-2 bg-obsidian-800 border border-gold-500/30 rounded-full text-gold-400 text-sm font-mono tracking-wider"
            >
                قريباً - COMING SOON
            </motion.div>
        </div>
    )
}
