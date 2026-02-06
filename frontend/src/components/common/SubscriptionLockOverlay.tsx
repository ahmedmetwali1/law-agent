import { useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { Lock, CreditCard } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import { motion, AnimatePresence } from 'framer-motion'

export function SubscriptionLockOverlay() {
    const { profile, loading } = useAuth()
    const location = useLocation()
    const navigate = useNavigate()
    const [isLocked, setIsLocked] = useState(false)

    // Allowed Routes (Regex or Exact Match)
    const allowedRoutes = [
        '/subscriptions',
        '/settings',
        '/calendar',
        '/dashboard',
        '/login',
        '/signup'
    ]

    useEffect(() => {
        if (loading || !profile?.subscription_info) {
            setIsLocked(false)
            return
        }

        const { is_expired } = profile.subscription_info
        const currentPath = location.pathname

        // Check if current page is allowed
        const isAllowed = allowedRoutes.some(route => currentPath.startsWith(route))

        if (is_expired && !isAllowed) {
            setIsLocked(true)
        } else {
            setIsLocked(false)
        }

    }, [location.pathname, profile, loading])

    if (!isLocked) return null

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0, backdropFilter: 'blur(0px)' }}
                animate={{ opacity: 1, backdropFilter: 'blur(12px)' }}
                exit={{ opacity: 0, backdropFilter: 'blur(0px)' }}
                className="fixed inset-0 z-[9999] flex items-center justify-center bg-obsidian-950/60"
            >
                <div className="absolute inset-0 bg-gradient-to-br from-obsidian-900/80 to-black/80 backdrop-blur-xl" />

                <div className="relative z-10 max-w-md w-full mx-4 text-center">
                    <div className="w-20 h-20 bg-red-500/10 rounded-full flex items-center justify-center mx-auto mb-6 border border-red-500/20 shadow-xl shadow-red-900/20">
                        <Lock className="w-10 h-10 text-red-500" />
                    </div>

                    <h2 className="text-3xl font-bold text-white font-cairo mb-4">
                        الاشتراك منتهي
                    </h2>

                    <p className="text-gray-300 font-cairo mb-8 text-lg leading-relaxed">
                        عذراً، لا يمكن الوصول لهذه الصفحة لأن اشتراكك الحالي قد انتهى.
                        يمكنك فقط الوصول للتقويم والإعدادات.
                        <br />
                        <span className="text-red-400 text-sm mt-2 block">
                            يرجى تجديد الاشتراك لاستعادة كامل الصلاحيات.
                        </span>
                    </p>

                    <button
                        onClick={() => navigate('/subscriptions')}
                        className="group relative inline-flex items-center justify-center gap-3 px-8 py-4 bg-gradient-to-r from-gold-600 to-gold-500 hover:from-gold-500 hover:to-gold-400 text-white font-bold rounded-2xl transition-all duration-300 transform hover:scale-105 shadow-lg hover:shadow-gold-500/25"
                    >
                        <CreditCard className="w-5 h-5 text-white" />
                        <span className="font-cairo text-lg text-white">تجديد الاشتراك الآن / الذهاب للوحة التحكم</span>
                        <div className="absolute inset-0 rounded-2xl ring-2 ring-white/20 group-hover:ring-white/40 transition-all" />
                    </button>

                    <button
                        onClick={() => navigate('/dashboard')}
                        className="mt-6 text-white hover:text-gold-400 font-cairo text-sm underline underline-offset-4 transition-colors block mx-auto"
                    >
                        الذهاب للوحة المعلومات
                    </button>
                </div>
            </motion.div>
        </AnimatePresence>
    )
}
