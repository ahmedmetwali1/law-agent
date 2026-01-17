import { ReactNode } from 'react'
import { motion } from 'framer-motion'

interface AuthLayoutProps {
    children: ReactNode
    title: string
    subtitle?: string
}

export function AuthLayout({ children, title, subtitle }: AuthLayoutProps) {
    return (
        <div className="min-h-screen bg-gradient-to-br from-obsidian-900 via-obsidian-800 to-obsidian-900 flex items-center justify-center p-4 relative overflow-hidden">
            {/* Gold Mesh Gradient Overlay */}
            <div className="absolute inset-0 opacity-10">
                <div className="absolute inset-0 bg-gradient-to-br from-gold-500/20 via-transparent to-gold-600/20" />
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(212,175,55,0.1),transparent_50%)]" />
            </div>

            {/* Animated Background Elements */}
            <div className="absolute top-20 left-20 w-72 h-72 bg-gold-500/5 rounded-full blur-3xl animate-pulse" />
            <div className="absolute bottom-20 right-20 w-96 h-96 bg-gold-600/5 rounded-full blur-3xl animate-pulse delay-1000" />

            {/* Main Content */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                className="relative z-10 w-full max-w-md"
            >
                {/* Glassmorphic Card */}
                <div className="backdrop-blur-xl bg-obsidian-800/70 border border-gold-500/20 rounded-2xl p-8 shadow-2xl">
                    {/* Header */}
                    <div className="text-center mb-8">
                        <motion.h1
                            initial={{ opacity: 0, y: -10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.2 }}
                            className="text-3xl font-bold text-gold-500 mb-2"
                            style={{ fontFamily: 'Cairo, sans-serif' }}
                        >
                            {title}
                        </motion.h1>
                        {subtitle && (
                            <motion.p
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                transition={{ delay: 0.3 }}
                                className="text-gray-400 text-sm"
                                style={{ fontFamily: 'Cairo, sans-serif' }}
                            >
                                {subtitle}
                            </motion.p>
                        )}
                    </div>

                    {/* Form Content */}
                    {children}
                </div>

                {/* Footer Decoration */}
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.4 }}
                    className="mt-4 text-center"
                >
                    <div className="inline-block px-4 py-2 backdrop-blur-sm bg-obsidian-800/50 border border-gold-500/10 rounded-full">
                        <p className="text-gold-500/60 text-xs" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            ⚖️ النظام القانوني الذكي
                        </p>
                    </div>
                </motion.div>
            </motion.div>
        </div>
    )
}
