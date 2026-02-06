import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import {
    LayoutDashboard,
    Sparkles,
    Users,
    Briefcase,
    Scale,
    Calendar,
    CheckSquare,
    FileText,
    FolderOpen,
    FileWarning,
    BookOpen,
    Book,
    UserPlus,
    ClipboardList,
    Settings,
    LogOut,
    MessageSquare,
    Shield,
    CreditCard,
    Webhook
} from 'lucide-react'
import { toast } from 'sonner'
import { useAuth } from '../../contexts/AuthContext'
import { useSettings } from '../../contexts/SettingsContext' // ✅ Import Settings

interface NavItem {
    icon: React.ElementType
    label: string
    href: string
}

interface NavigationSidebarProps {
    onExpandChange?: (isExpanded: boolean) => void
    mobileIsOpen?: boolean
    onMobileClose?: () => void
}

const navItems: NavItem[] = [
    { icon: LayoutDashboard, label: 'لوحة التحكم', href: '/dashboard' },
    { icon: Sparkles, label: 'المحادثة الذكية', href: '/chat' },
    { icon: Webhook, label: 'N8N Chat', href: '/n8n-chat' },
    { icon: Users, label: 'الموكلين', href: '/clients' },
    { icon: Scale, label: 'القضايا', href: '/cases' },
    { icon: Calendar, label: 'الجلسات', href: '/hearings' },
    { icon: UserPlus, label: 'المساعدين', href: '/assistants' },  // ✅ NEW
    { icon: CreditCard, label: 'اشتراكاتي', href: '/subscriptions' }, // ✅ NEW
    { icon: CheckSquare, label: 'المهام', href: '/tasks' },
    { icon: FileWarning, label: 'المحاضر', href: '/reports' },
    { icon: FileText, label: 'السجل', href: '/audit-log' },  // ✅ NEW
    { icon: FileText, label: 'المستندات', href: '/documents' },
    { icon: Book, label: 'قاعدة المعرفة', href: '/knowledge' },
    { icon: Settings, label: 'الإعدادات', href: '/settings' },
    { icon: MessageSquare, label: 'الدعم الفني', href: '/support' },
]

export function NavigationSidebar({ onExpandChange, mobileIsOpen = false, onMobileClose }: NavigationSidebarProps) {
    const [isExpanded, setIsExpanded] = useState(false)
    const location = useLocation()
    const navigate = useNavigate()
    const { user } = useAuth()
    const { settings } = useSettings() // ✅ Use Settings

    useEffect(() => {
        onExpandChange?.(isExpanded)
    }, [isExpanded, onExpandChange])

    const handleLogout = () => {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        toast.success('تم تسجيل الخروج بنجاح')
        navigate('/login')
    }

    return (
        <>
            {/* Desktop Sidebar - Hidden on mobile */}
            <motion.aside
                initial={false}
                animate={{ width: isExpanded ? '240px' : '80px' }}
                transition={{ duration: 0.3, ease: 'easeInOut' }}
                onMouseEnter={() => setIsExpanded(true)}
                onMouseLeave={() => setIsExpanded(false)}
                className="hidden lg:flex fixed right-0 top-16 bottom-8 glass-dark border-r border-gold-500/20 z-40 overflow-hidden flex-col"
            >
                <div className="h-16 flex items-center justify-center border-b border-gold-500/10">
                    {settings.platform_logo_url ? (
                        <img
                            src={settings.platform_logo_url}
                            alt={settings.platform_name}
                            className={`transition-all duration-300 ${isExpanded ? 'w-10 h-10' : 'w-8 h-8'}`}
                        />
                    ) : (
                        <div className={`rounded-full bg-gradient-to-br from-gold-400 to-gold-600 flex items-center justify-center font-bold text-obsidian-900 ${isExpanded ? 'w-10 h-10 text-xl' : 'w-8 h-8 text-base'}`}>
                            {settings.platform_name ? settings.platform_name.charAt(0) : 'L'}
                        </div>
                    )}
                    {isExpanded && (
                        <motion.span
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            className="mr-3 font-bold text-lg text-white whitespace-nowrap overflow-hidden"
                        >
                            {settings.platform_name || 'Legal AI'}
                        </motion.span>
                    )}
                </div>

                <nav className="flex flex-col gap-2 p-4 h-full overflow-hidden">
                    <div className="flex-1 space-y-1 scrollbar-thin overflow-y-auto">
                        {navItems.map((item) => {
                            const isActive = location.pathname === item.href || location.pathname.startsWith(item.href + '/')
                            const Icon = item.icon

                            return (
                                <Link
                                    key={item.href}
                                    to={item.href}
                                    className={`group relative flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 ${isActive
                                        ? 'bg-cobalt-600 text-white shadow-lg shadow-cobalt-600/20'
                                        : 'text-gray-400 hover:bg-obsidian-700 hover:text-white'
                                        }`}
                                >
                                    {isActive && (
                                        <motion.div
                                            layoutId="activeTab"
                                            className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-gold-500 rounded-r-full"
                                        />
                                    )}
                                    <Icon className="w-5 h-5 flex-shrink-0" />
                                    <motion.span
                                        initial={{ opacity: 0, x: -10 }}
                                        animate={{
                                            opacity: isExpanded ? 1 : 0,
                                            x: isExpanded ? 0 : -10,
                                        }}
                                        transition={{ duration: 0.2 }}
                                        className="whitespace-nowrap text-sm font-medium"
                                    >
                                        {item.label}
                                    </motion.span>
                                    {!isActive && (
                                        <div className="absolute inset-0 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity bg-gradient-to-l from-cobalt-600/10 to-transparent" />
                                    )}
                                </Link>
                            )
                        })}
                    </div>

                    {user && (user.role_id === 'e2d8b2c0-7b8d-4b46-88e8-cb0071467901' || user.role?.name === 'admin') && (
                        <Link
                            to="/admin"
                            className={`group relative flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 ${location.pathname.startsWith('/admin')
                                ? 'bg-purple-600 text-white shadow-lg shadow-purple-600/20'
                                : 'text-gray-400 hover:bg-obsidian-700 hover:text-white'
                                } border-t border-gold-500/10 mt-2`}
                        >
                            {location.pathname.startsWith('/admin') && (
                                <motion.div
                                    layoutId="activeTab"
                                    className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-purple-500 rounded-r-full"
                                />
                            )}
                            <Shield className="w-5 h-5 flex-shrink-0" />
                            <motion.span
                                initial={{ opacity: 0, x: -10 }}
                                animate={{
                                    opacity: isExpanded ? 1 : 0,
                                    x: isExpanded ? 0 : -10,
                                }}
                                transition={{ duration: 0.2 }}
                                className="whitespace-nowrap text-sm font-medium"
                            >
                                لوحة الإدارة
                            </motion.span>
                        </Link>
                    )}

                    <button
                        onClick={handleLogout}
                        className="group relative flex items-center gap-4 px-4 py-3 rounded-lg transition-all duration-200 hover:bg-error/20 text-gray-400 hover:text-error border-t border-gold-500/10 mt-2"
                    >
                        <LogOut className="w-5 h-5 flex-shrink-0" />
                        <motion.span
                            initial={{ opacity: 0, x: -10 }}
                            animate={{
                                opacity: isExpanded ? 1 : 0,
                                x: isExpanded ? 0 : -10,
                            }}
                            transition={{ duration: 0.2 }}
                            className="whitespace-nowrap text-sm font-medium"
                        >
                            تسجيل الخروج
                        </motion.span>
                    </button>
                </nav>
            </motion.aside>

            {/* Mobile Sidebar - Drawer Overlay */}
            <AnimatePresence>
                {mobileIsOpen && (
                    <>
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={onMobileClose}
                            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 lg:hidden"
                        />
                        <motion.aside
                            initial={{ x: '100%' }}
                            animate={{ x: 0 }}
                            exit={{ x: '100%' }}
                            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
                            className="fixed right-0 top-0 bottom-0 w-72 bg-obsidian-900 border-l border-gold-500/20 z-[60] overflow-y-auto lg:hidden"
                        >
                            <div className="p-4 border-b border-gold-500/10 flex items-center justify-between">
                                <span className="font-bold text-gold-500 text-lg">
                                    {settings.platform_name || 'Legal AI'}
                                </span>
                                <button onClick={onMobileClose} className="p-2 hover:bg-white/10 rounded-lg">
                                    <LogOut className="w-5 h-5 text-gray-400 rotate-180" />
                                </button>
                            </div>

                            <nav className="flex flex-col gap-2 p-4">
                                {navItems.map((item) => {
                                    const isActive = location.pathname === item.href || location.pathname.startsWith(item.href + '/')
                                    const Icon = item.icon
                                    return (
                                        <Link
                                            key={item.href}
                                            to={item.href}
                                            onClick={onMobileClose}
                                            className={`flex items-center gap-4 px-4 py-3 rounded-xl transition-all ${isActive
                                                ? 'bg-cobalt-600 text-white'
                                                : 'text-gray-400 hover:text-white hover:bg-white/5'
                                                }`}
                                        >
                                            <Icon className="w-5 h-5" />
                                            <span className="font-medium">{item.label}</span>
                                        </Link>
                                    )
                                })}

                                {user && (user.role_id === 'e2d8b2c0-7b8d-4b46-88e8-cb0071467901' || user.role?.name === 'admin') && (
                                    <Link
                                        to="/admin"
                                        onClick={onMobileClose}
                                        className="flex items-center gap-4 px-4 py-3 rounded-xl text-purple-400 hover:bg-purple-500/10 mt-2"
                                    >
                                        <Shield className="w-5 h-5" />
                                        <span className="font-medium">لوحة الإدارة</span>
                                    </Link>
                                )}

                                <button
                                    onClick={handleLogout}
                                    className="flex items-center gap-4 px-4 py-3 rounded-xl text-error hover:bg-error/10 mt-auto"
                                >
                                    <LogOut className="w-5 h-5" />
                                    <span className="font-medium">تسجيل الخروج</span>
                                </button>
                            </nav>
                        </motion.aside>
                    </>
                )}
            </AnimatePresence>
        </>
    )
}
