import { motion } from 'framer-motion'
import { LucideIcon } from 'lucide-react'
import { ReactNode } from 'react'

interface StatCardProps {
    title: string
    mainValue: string | number
    icon: LucideIcon
    trend?: {
        value: string
        isPositive: boolean
        label: string
    }
    microStats?: Array<{
        label: string
        value: string | number
        color?: string
    }>
    iconColor?: string
    delay?: number
}

export function HighDensityStatCard({
    title,
    mainValue,
    icon: Icon,
    trend,
    microStats,
    iconColor = 'text-gold-500',
    delay = 0
}: StatCardProps) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay }}
            className="backdrop-blur-xl bg-obsidian-800/70 border border-gold-500/20 rounded-xl p-5 hover:border-gold-500/40 transition-all group"
        >
            {/* Header */}
            <div className="flex items-start justify-between mb-3">
                <div>
                    <p className="text-gray-400 text-sm mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        {title}
                    </p>
                    <h3 className="text-3xl font-bold text-white" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        {mainValue}
                    </h3>
                </div>
                <div className={`p-3 rounded-lg bg-obsidian-900/50 ${iconColor} group-hover:scale-110 transition-transform`}>
                    <Icon className="w-6 h-6" />
                </div>
            </div>

            {/* Trend */}
            {trend && (
                <div className="flex items-center gap-2 mb-3 pb-3 border-b border-gold-500/10">
                    <span className={`text-sm font-medium ${trend.isPositive ? 'text-green-400' : 'text-red-400'}`}>
                        {trend.isPositive ? '↑' : '↓'} {trend.value}
                    </span>
                    <span className="text-xs text-gray-500" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        {trend.label}
                    </span>
                </div>
            )}

            {/* Micro Stats */}
            {microStats && microStats.length > 0 && (
                <div className="grid grid-cols-2 gap-2">
                    {microStats.map((stat, index) => (
                        <div key={index} className="bg-obsidian-900/30 rounded-lg p-2">
                            <p className="text-xs text-gray-500 mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                {stat.label}
                            </p>
                            <p
                                className={`text-sm font-semibold ${stat.color || 'text-white'}`}
                                style={{ fontFamily: 'Cairo, sans-serif' }}
                            >
                                {stat.value}
                            </p>
                        </div>
                    ))}
                </div>
            )}
        </motion.div>
    )
}
