import React from 'react'
import { AlertTriangle, Clock, CreditCard, ChevronLeft, Sparkles } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import { motion } from 'framer-motion'

export function SubscriptionWarning() {
    const { profile, loading } = useAuth()

    if (loading || !profile?.subscription_info) return null

    const { status, is_expired, days_remaining, package_name } = profile.subscription_info

    // Don't show if active and plenty of time (e.g. > 5 days)
    if (!is_expired && days_remaining > 5) return null

    // Determine Banner Configuration
    const config = is_expired
        ? {
            gradient: "from-red-900/90 via-red-950/90 to-black/90",
            border: "border-red-500/30",
            iconBg: "bg-red-500/20",
            iconColor: "text-red-500",
            Icon: AlertTriangle,
            title: "فترة الاشتراك منتهية",
            message: "لقد انتهت صلاحية اشتراكك الحالي. النظام الآن في وضع القراءة فقط. يرجى التجديد لاستعادة كامل الصلاحيات.",
            buttonGradient: "from-red-600 to-red-500 hover:from-red-500 hover:to-red-400",
            buttonShadow: "shadow-red-900/20",
            glow: "shadow-[0_0_30px_-5px_rgba(239,68,68,0.3)]"
        }
        : {
            gradient: "from-yellow-900/90 via-yellow-950/90 to-black/90",
            border: "border-yellow-500/30",
            iconBg: "bg-yellow-500/20",
            iconColor: "text-yellow-500",
            Icon: Clock,
            title: "الاشتراك ينتهي قريباً",
            message: `باقة "${package_name}" ستنتهي صلاحيتها خلال ${days_remaining} يوم. جدد الآن لضمان استمرار عمل المكتب.`,
            buttonGradient: "from-yellow-600 to-yellow-500 hover:from-yellow-500 hover:to-yellow-400",
            buttonShadow: "shadow-yellow-900/20",
            glow: "shadow-[0_0_30px_-5px_rgba(234,179,8,0.3)]"
        }

    return (
        <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className={`
                relative overflow-hidden
                mx-4 mt-6 p-1 rounded-2xl
                bg-gradient-to-r ${config.gradient}
                backdrop-blur-xl border ${config.border}
                ${config.glow} z-[50]
            `}
        >
            {/* Animated Background Overlay */}
            <div className="absolute inset-0 bg-[url('/noise.png')] opacity-5 mix-blend-overlay"></div>

            <div className="relative flex flex-col md:flex-row items-center justify-between p-5 md:p-6 gap-6">

                {/* Content Section */}
                <div className="flex items-start gap-4 md:gap-6 flex-1 text-center md:text-right">
                    <div className={`
                        w-14 h-14 rounded-2xl ${config.iconBg} 
                        flex items-center justify-center shrink-0 
                        backdrop-blur-sm shadow-inner border border-white/5
                        group transition-transform duration-500 hover:scale-110
                    `}>
                        <config.Icon className={`w-7 h-7 ${config.iconColor} drop-shadow-lg`} />
                    </div>

                    <div className="flex-1">
                        <h3 className="text-xl font-bold text-white font-cairo mb-2 flex items-center justify-center md:justify-start gap-2">
                            {config.title}
                            {is_expired && <span className="px-2 py-0.5 rounded text-xs bg-red-500 text-white shadow-sm">توقف الخدمة</span>}
                        </h3>
                        <p className="text-gray-300 font-cairo leading-relaxed text-sm md:text-base opacity-90 max-w-2xl">
                            {config.message}
                        </p>
                    </div>
                </div>

                {/* Action Button */}
                <Link to="/subscriptions" className="w-full md:w-auto shrink-0">
                    <button className={`
                        group relative w-full md:w-auto
                        flex items-center justify-center gap-3 
                        px-8 py-3.5 rounded-xl
                        bg-gradient-to-r ${config.buttonGradient}
                        text-white font-bold font-cairo
                        shadow-lg ${config.buttonShadow}
                        transition-all duration-300 transform hover:scale-[1.02] active:scale-95
                        border border-white/10
                    `}>
                        <span className="relative z-10 flex items-center gap-2">
                            {is_expired ? <Sparkles className="w-5 h-5" /> : <CreditCard className="w-5 h-5" />}
                            {is_expired ? "تجديد الاشتراك الآن" : "ترقية الباقة / تجديد"}
                        </span>

                        {/* Shine Effect */}
                        <div className="absolute inset-0 rounded-xl overflow-hidden">
                            <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000 ease-in-out" />
                        </div>
                    </button>
                </Link>
            </div>
        </motion.div>
    )
}
