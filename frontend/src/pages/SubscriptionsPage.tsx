import { motion } from 'framer-motion'
import { CreditCard, Star } from 'lucide-react'

export function SubscriptionsPage() {
    return (
        <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-6 bg-obsidian-900/50 rounded-3xl border border-gray-800">
            <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                className="relative mb-8"
            >
                <div className="absolute inset-0 bg-green-500/20 blur-3xl rounded-full" />
                <CreditCard className="w-24 h-24 text-green-500 relative z-10" />
                <Star className="w-8 h-8 text-gold-500 absolute -top-2 -right-2 z-20 fill-gold-500" />
            </motion.div>

            <h1 className="text-3xl font-bold text-white mb-4">الاشتراكات والباقات</h1>
            <p className="text-gray-400 max-w-md mx-auto mb-8">
                صفحة إدارة الاشتراكات وتجديد الباقات قيد التطوير حالياً. ستتمكن قريباً من ترقية باقتك والتحكم في الفواتير من هنا.
            </p>

            <div className="px-6 py-2 bg-obsidian-800 border border-green-500/30 rounded-full text-green-400 text-sm font-mono">
                قريباً - COMING SOON
            </div>
        </div>
    )
}
