import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
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
    MessageSquare
} from 'lucide-react'
import { toast } from 'sonner'

interface NavItem {
    icon: React.ElementType
    label: string
    href: string
}

interface NavigationSidebarProps {
    onExpandChange?: (isExpanded: boolean) => void
}

const navItems: NavItem[] = [
    { icon: LayoutDashboard, label: 'لوحة التحكم', href: '/dashboard' },
    { icon: Sparkles, label: 'المساعد الذكي', href: '/chat' },  // AI Chat Sessions
    { icon: Users, label: 'الموكلين', href: '/clients' },
    { icon: Scale, label: 'القضايا', href: '/cases' },
    { icon: Calendar, label: 'الجلسات', href: '/hearings' },
    { icon: UserPlus, label: 'المساعدين', href: '/assistants' },  // ✅ NEW
    { icon: CheckSquare, label: 'المهام', href: '/tasks' },
    { icon: FileWarning, label: 'المحاضر', href: '/reports' },
    { icon: FileText, label: 'السجل', href: '/audit-log' },  // ✅ NEW
    { icon: FileText, label: 'المستندات', href: '/documents' },
    { icon: Book, label: 'قاعدة المعرفة', href: '/knowledge' },
    { icon: Settings, label: 'الإعدادات', href: '/settings' },
    { icon: MessageSquare, label: 'الدعم الفني', href: '/support' },
]

export function NavigationSidebar({ onExpandChange }: NavigationSidebarProps) {
    const [isExpanded, setIsExpanded] = useState(false)
    const location = useLocation()
    const navigate = useNavigate()

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
        <motion.aside
            initial={false}
            animate={{ width: isExpanded ? '240px' : '80px' }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
            onMouseEnter={() => setIsExpanded(true)}
            onMouseLeave={() => setIsExpanded(false)}
            className="fixed right-0 top-16 bottom-8 glass-dark border-r border-gold-500/20 z-40 overflow-hidden"
        >
            <nav className="flex flex-col gap-2 p-4 h-full">
                {/* Navigation Items */}
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
                                {/* Active Indicator - Vertical Gold Line (LEFT side for RTL) */}
                                {isActive && (
                                    <motion.div
                                        layoutId="activeTab"
                                        className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-gold-500 rounded-r-full"
                                    />
                                )}

                                {/* Icon */}
                                <Icon className="w-5 h-5 flex-shrink-0" />

                                {/* Label - Animated */}
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

                                {/* Glow Effect on Hover */}
                                {!isActive && (
                                    <div className="absolute inset-0 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity bg-gradient-to-l from-cobalt-600/10 to-transparent" />
                                )}
                            </Link>
                        )
                    })}
                </div>

                {/* Logout Button at Bottom */}
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
    )
}
