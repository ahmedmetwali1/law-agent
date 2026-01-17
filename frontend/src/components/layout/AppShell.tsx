import { useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { Toaster } from 'sonner'
import { Sparkles, ChevronLeft, ChevronRight } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { GlobalHeader } from './GlobalHeader'
import { NavigationSidebar } from './NavigationSidebar'
import { SystemFooter } from './SystemFooter'
import { AINexus } from '../features/ai/AINexus'

export function AppShell() {
    const [isSidebarExpanded, setIsSidebarExpanded] = useState(false) // State kept for sidebar internal logic if needed, but not affecting layout margin
    const [isAIExpanded, setIsAIExpanded] = useState(true)
    const [showMobileAI, setShowMobileAI] = useState(false)
    const location = useLocation()

    // Hide AI Nexus on /chat or /ai route
    const hideAINexus = location.pathname === '/chat' || location.pathname === '/ai'

    // Hide Navigation Sidebar only on login/signup (handled by routing usually) or logic
    const hideNavigation = false // Show navigation on all app pages including /ai

    // AI Nexus width when collapsed/expanded
    const aiWidth = isAIExpanded ? 'w-[30%]' : 'w-16'

    return (
        <div dir="rtl" className="min-h-screen bg-obsidian-900 text-white">
            {/* Global Header */}
            <GlobalHeader />

            {/* Main Layout Container - Split Screen */}
            <div className={`flex min-h-[calc(100vh-64px)] pt-16 ${location.pathname === '/ai' ? '' : 'pb-8'}`}>
                {/* Content Area - With Dynamic Margins */}
                <main
                    className={`
            flex-1 overflow-y-auto scrollbar-thin
            transition-all duration-300 ease-in-out
            mr-20  // ✅ Fixed margin: Content starts after the collapsed sidebar strip
            ${!hideAINexus && isAIExpanded ? 'ml-[20%]' : !hideAINexus ? 'ml-16' : 'ml-0'}
          `}
                >
                    <div className={location.pathname === '/ai' ? 'h-[calc(100vh-64px)] -mt-4' : 'p-4'}>
                        <Outlet />
                    </div>
                </main>

                {/* AI Nexus (Left Side) - Collapsible - ✅ تصغير العرض */}
                {!hideAINexus && (
                    <div
                        className={`
              hidden lg:block fixed left-0 top-16 bottom-8 
              border-r border-white/5 transition-all duration-300
              ${isAIExpanded ? 'w-[20%]' : 'w-16'}
            `}
                    >
                        {/* Collapse/Expand Button */}
                        <button
                            onClick={() => setIsAIExpanded(!isAIExpanded)}
                            className="absolute -right-3 top-1/2 -translate-y-1/2 z-10 w-6 h-12 bg-obsidian-700 border border-gold-500/30 rounded-r-lg flex items-center justify-center hover:bg-obsidian-600 transition"
                        >
                            {isAIExpanded ? (
                                <ChevronLeft className="w-4 h-4 text-gold-500" />
                            ) : (
                                <ChevronRight className="w-4 h-4 text-gold-500" />
                            )}
                        </button>

                        <AINexus isCollapsed={!isAIExpanded} />
                    </div>
                )}

                {/* Navigation Sidebar (Fixed Right) */}
                {!hideNavigation && <NavigationSidebar onExpandChange={setIsSidebarExpanded} />}
            </div>

            {/* System Footer */}
            <SystemFooter />

            {/* Mobile FAB (Floating Action Button) */}
            {!hideAINexus && (
                <button
                    onClick={() => setShowMobileAI(true)}
                    className="lg:hidden fixed bottom-24 left-6 w-14 h-14 rounded-full bg-gradient-to-br from-cobalt-600 to-cobalt-500 shadow-lg shadow-cobalt-600/50 flex items-center justify-center z-50 hover:scale-110 transition-transform"
                >
                    <Sparkles className="w-6 h-6 text-white" />
                </button>
            )}

            {/* Mobile Bottom Sheet */}
            {!hideAINexus && (
                <AnimatePresence>
                    {showMobileAI && (
                        <>
                            {/* Backdrop */}
                            <motion.div
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                                onClick={() => setShowMobileAI(false)}
                                className="lg:hidden fixed inset-0 bg-black/60 backdrop-blur-sm z-[60]"
                            />

                            {/* Bottom Sheet */}
                            <motion.div
                                initial={{ y: '100%' }}
                                animate={{ y: 0 }}
                                exit={{ y: '100%' }}
                                transition={{ type: 'spring', damping: 30, stiffness: 300 }}
                                className="lg:hidden fixed bottom-0 left-0 right-0 h-[85vh] bg-obsidian-900 rounded-t-3xl z-[70] overflow-hidden"
                            >
                                {/* Handle Bar */}
                                <div className="flex justify-center py-3 border-b border-gold-500/10">
                                    <div className="w-12 h-1 bg-gray-600 rounded-full" />
                                </div>

                                {/* AI Nexus Content */}
                                <div className="h-[calc(100%-48px)]">
                                    <AINexus isCollapsed={false} />
                                </div>
                            </motion.div>
                        </>
                    )}
                </AnimatePresence>
            )}
        </div>
    )
}
