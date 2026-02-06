import { useState, useRef, useEffect } from 'react'
import { Search, Bell, User, Settings, LogOut, Menu } from 'lucide-react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import { useNotificationStore } from '../../stores/notificationStore'
import { useBreadcrumb } from '../../contexts/BreadcrumbContext'
import { globalSearch, SearchResult } from '../../services/searchService'
import { formatDistanceToNow } from 'date-fns'
import { arSA } from 'date-fns/locale'

interface GlobalHeaderProps {
    onMenuClick?: () => void
}

export function GlobalHeader({ onMenuClick }: GlobalHeaderProps) {
    const location = useLocation()
    const navigate = useNavigate()
    const { profile, signOut, isAssistant, officeId, getEffectiveLawyerId } = useAuth()
    const { unreadCount, notifications, fetchNotifications, markAsRead } = useNotificationStore()
    const [searchQuery, setSearchQuery] = useState('')
    const [searchResults, setSearchResults] = useState<SearchResult[]>([])
    const [showSearchResults, setShowSearchResults] = useState(false)
    const [isSearching, setIsSearching] = useState(false)
    const [showUserMenu, setShowUserMenu] = useState(false)
    const [showNotifications, setShowNotifications] = useState(false)
    const [showMobileSearch, setShowMobileSearch] = useState(false) // ✅ Mobile Search State
    const [officeLawyer, setOfficeLawyer] = useState<any>(null)
    const menuRef = useRef<HTMLDivElement>(null)
    const notifRef = useRef<HTMLDivElement>(null)
    const searchRef = useRef<HTMLDivElement>(null)

    // Close dropdowns when clicking outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
                setShowUserMenu(false)
            }
            if (notifRef.current && !notifRef.current.contains(event.target as Node)) {
                setShowNotifications(false)
            }
            if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
                setShowSearchResults(false)
                // Don't close mobile search immediately if clicking inside, but if outside yes
                if (window.innerWidth < 1024) setShowMobileSearch(false)
            }
        }

        document.addEventListener('mousedown', handleClickOutside)
        return () => document.removeEventListener('mousedown', handleClickOutside)
    }, [])

    // Debounced search
    useEffect(() => {
        const timer = setTimeout(async () => {
            if (searchQuery.trim().length >= 2) {
                setIsSearching(true)
                const lawyerId = getEffectiveLawyerId()
                if (lawyerId) {
                    const results = await globalSearch(searchQuery, lawyerId)
                    setSearchResults(results)
                    setShowSearchResults(true)
                }
                setIsSearching(false)
            } else {
                setSearchResults([])
                setShowSearchResults(false)
            }
        }, 300)

        return () => clearTimeout(timer)
    }, [searchQuery, getEffectiveLawyerId])

    // ✅ BFF Pattern: جلب بيانات المحامي للمساعد
    useEffect(() => {
        const fetchOfficeLawyer = async () => {
            if (isAssistant && officeId) {
                try {
                    const { apiClient } = await import('../../api/client')
                    const data = await apiClient.get('/api/users/office-lawyer')
                    if (data) setOfficeLawyer(data)
                } catch (error) {
                    console.error('Error fetching office lawyer:', error)
                }
            }
        }
        fetchOfficeLawyer()
    }, [isAssistant, officeId])

    // Fetch notifications on mount and when lawyerId changes
    useEffect(() => {
        const lawyerId = getEffectiveLawyerId()
        if (lawyerId) {
            fetchNotifications(lawyerId)
        }

        // Refresh every 5 minutes
        const interval = setInterval(() => {
            if (lawyerId) fetchNotifications(lawyerId)
        }, 5 * 60 * 1000)

        return () => clearInterval(interval)
    }, [getEffectiveLawyerId, fetchNotifications])

    // Generate breadcrumbs from current path
    const generateBreadcrumbs = () => {
        const { pageTitle } = useBreadcrumb()
        const paths = location.pathname.split('/').filter(Boolean)
        const breadcrumbs = [{ label: 'الرئيسية', path: '/' }]

        const pathMap: Record<string, string> = {
            dashboard: 'لوحة التحكم',
            clients: 'الموكلين',
            cases: 'القضايا',
            hearings: 'الجلسات',
            tasks: 'المهام',
            reports: 'المحاضر',
            documents: 'المستندات',
            knowledge: 'قاعدة المعرفة',
            settings: 'الإعدادات',
        }

        // UUID pattern detector
        const isUUID = (str: string) => /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(str)

        paths.forEach((path, index) => {
            const cumulativePath = '/' + paths.slice(0, index + 1).join('/')

            // If it's the last item, it's a UUID, and we have a pageTitle, use it
            const isLastItem = index === paths.length - 1
            const label = (isLastItem && isUUID(path) && pageTitle)
                ? pageTitle
                : (pathMap[path] || path)

            breadcrumbs.push({
                label,
                path: cumulativePath,
            })
        })

        return breadcrumbs
    }

    const breadcrumbs = generateBreadcrumbs()

    const handleLogout = async () => {
        await signOut()
        navigate('/login')
    }

    return (
        <header className="fixed top-0 left-0 right-0 z-50 h-16 glass-dark border-b border-gold-500/10">
            <div className="flex items-center justify-between h-full px-6">

                {/* Right Side - Breadcrumbs & Menu */}
                <div className="flex items-center gap-4">
                    {/* Mobile Menu Button */}
                    <button
                        onClick={onMenuClick}
                        className="lg:hidden p-2 text-gray-400 hover:text-white rounded-lg hover:bg-white/10 transition-colors"
                    >
                        <Menu className="w-6 h-6" />
                    </button>

                    <nav className="flex items-center gap-2 text-sm">
                        {breadcrumbs.map((crumb, index) => (
                            <div key={crumb.path} className="flex items-center gap-2">
                                <a
                                    href={crumb.path}
                                    className={`
                                        transition-colors
                                        ${index === breadcrumbs.length - 1
                                            ? 'text-white font-medium'
                                            : 'text-gray-400 hover:text-gray-300'
                                        }
                                    `}
                                >
                                    {crumb.label}
                                </a>
                                {index < breadcrumbs.length - 1 && (
                                    <span className="text-gray-600">/</span>
                                )}
                            </div>
                        ))}
                    </nav>
                </div>

                {/* Left Side - Actions */}
                <div className="flex items-center gap-2 lg:gap-4">
                    {/* Global Search */}
                    <div className="relative" ref={searchRef}>
                        {/* Mobile Search Icon Toggle */}
                        {!showMobileSearch && (
                            <button
                                onClick={() => setShowMobileSearch(true)}
                                className="lg:hidden p-2 text-gray-400 hover:text-white rounded-lg hover:bg-white/10 transition-colors"
                            >
                                <Search className="w-5 h-5" />
                            </button>
                        )}

                        {/* Search Input - Hidden on Mobile unless toggled */}
                        <div className={`
                            flex items-center gap-2 bg-obsidian-800 rounded-lg px-4 py-2 border border-gray-600/20 
                            focus-within:border-cobalt-500/50 transition-all duration-300
                            ${showMobileSearch
                                ? 'absolute -right-10 top-0 w-[calc(100vw-8rem)] z-50 shadow-2xl scale-100 opacity-100 origin-right'
                                : 'hidden lg:flex w-64 scale-100'
                            }
                        `}>
                            <Search className="w-4 h-4 text-gray-400 shrink-0" />
                            <input
                                type="text"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                placeholder="بحث..."
                                autoFocus={showMobileSearch}
                                className="flex-1 bg-transparent text-sm outline-none placeholder:text-gray-500 min-w-0"
                                style={{ fontFamily: 'Cairo, sans-serif' }}
                            />
                            {isSearching && (
                                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gold-500 shrink-0"></div>
                            )}
                        </div>

                        {/* Search Results Dropdown */}
                        {showSearchResults && searchResults.length > 0 && (
                            <div className="absolute left-0 mt-2 w-96 glass-dark border border-gold-500/20 rounded-lg shadow-xl overflow-hidden z-50">
                                <div className="max-h-96 overflow-y-auto">
                                    {/* Group results by type */}
                                    {['case', 'client', 'opponent', 'authorization'].map(type => {
                                        const typeResults = searchResults.filter(r => r.type === type)
                                        if (typeResults.length === 0) return null

                                        const typeLabels: Record<string, string> = {
                                            case: 'قضايا',
                                            client: 'موكلين',
                                            opponent: 'خصوم',
                                            authorization: 'توكيلات'
                                        }

                                        return (
                                            <div key={type}>
                                                <div className="px-4 py-2 bg-obsidian-800/50 border-b border-gold-500/10">
                                                    <span className="text-xs font-bold text-gold-500" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                                        {typeLabels[type]} ({typeResults.length})
                                                    </span>
                                                </div>
                                                {typeResults.map(result => (
                                                    <button
                                                        key={result.id}
                                                        onClick={() => {
                                                            navigate(result.path)
                                                            setShowSearchResults(false)
                                                            setSearchQuery('')
                                                        }}
                                                        className="w-full px-4 py-3 hover:bg-obsidian-700 transition text-right flex items-start gap-3 border-b border-gray-800 last:border-0"
                                                    >
                                                        <span className="text-2xl">{result.icon}</span>
                                                        <div className="flex-1">
                                                            <div className="text-sm text-white font-medium" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                                                {result.title}
                                                            </div>
                                                            {result.subtitle && (
                                                                <div className="text-xs text-gray-400 mt-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                                                    {result.subtitle}
                                                                </div>
                                                            )}
                                                        </div>
                                                    </button>
                                                ))}
                                            </div>
                                        )
                                    })}
                                </div>
                            </div>
                        )}

                        {/* No Results Message */}
                        {showSearchResults && searchQuery.trim().length >= 2 && searchResults.length === 0 && !isSearching && (
                            <div className="absolute left-0 mt-2 w-96 glass-dark border border-gold-500/20 rounded-lg shadow-xl p-4 z-50">
                                <p className="text-sm text-gray-400 text-center" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                    لا توجد نتائج
                                </p>
                            </div>
                        )}
                    </div>

                    {/* Notification Bell */}
                    <div className="relative" ref={notifRef}>
                        <button
                            onClick={() => setShowNotifications(!showNotifications)}
                            className="relative p-2 hover:bg-obsidian-700 rounded-lg transition group"
                        >
                            <Bell className="w-5 h-5 text-gray-400 group-hover:text-white transition" />
                            {unreadCount > 0 && (
                                <span className="absolute top-1 left-1 min-w-[18px] h-[18px] bg-error rounded-full flex items-center justify-center text-[10px] font-bold">
                                    {unreadCount}
                                </span>
                            )}
                        </button>

                        {/* Notifications Dropdown */}
                        {showNotifications && (
                            <div className="absolute left-0 mt-2 w-80 glass-dark border border-gold-500/20 rounded-lg shadow-xl overflow-hidden">
                                <div className="p-3 border-b border-gold-500/10 flex items-center justify-between">
                                    <h3 className="font-bold text-gold-500" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                        الإشعارات {unreadCount > 0 && `(${unreadCount})`}
                                    </h3>
                                </div>
                                <div className="max-h-96 overflow-y-auto">
                                    {notifications.length === 0 ? (
                                        <div className="p-4 text-center text-gray-400 text-sm">
                                            لا توجد إشعارات جديدة
                                        </div>
                                    ) : (
                                        notifications.map(notif => (
                                            <button
                                                key={notif.id}
                                                onClick={() => {
                                                    if (notif.link) {
                                                        navigate(notif.link)
                                                    }
                                                    markAsRead(notif.id)
                                                    setShowNotifications(false)
                                                }}
                                                className={`w-full px-4 py-3 border-b border-gray-800 last:border-0 text-right hover:bg-obsidian-700 transition ${!notif.read ? 'bg-gold-500/5' : ''
                                                    }`}
                                            >
                                                <div className="flex items-start gap-3">
                                                    <div className="flex-1">
                                                        <div className="text-sm font-medium text-white mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                                            {notif.title}
                                                        </div>
                                                        <div className="text-xs text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                                            {notif.message}
                                                        </div>
                                                        <div className="text-[10px] text-gray-500 mt-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                                            {formatDistanceToNow(notif.timestamp, { addSuffix: true, locale: arSA })}
                                                        </div>
                                                    </div>
                                                    {!notif.read && (
                                                        <div className="w-2 h-2 rounded-full bg-gold-500 mt-1"></div>
                                                    )}
                                                </div>
                                            </button>
                                        ))
                                    )}
                                </div>
                            </div>
                        )}
                    </div>

                    {/* User Profile Menu */}
                    <div className="relative" ref={menuRef}>
                        <button
                            onClick={() => setShowUserMenu(!showUserMenu)}
                            className="flex items-center gap-2 hover:bg-obsidian-700 px-3 py-2 rounded-lg transition group"
                        >
                            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cobalt-500 to-cobalt-600 flex items-center justify-center ring-2 ring-gold-500/30">
                                <User className="w-4 h-4 text-white" />
                            </div>
                            <div className="hidden lg:flex flex-col items-start">
                                <span className="text-sm text-white group-hover:text-gold-500 transition font-medium" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                    {isAssistant ? 'المساعد' : 'المحامي'} {profile?.full_name || ''}
                                </span>
                                {/* ✅ NEW: عرض اسم المحامي للمساعد */}
                                {isAssistant && officeLawyer && (
                                    <span className="text-xs text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                        مساعد لـ: {officeLawyer.full_name}
                                    </span>
                                )}
                            </div>
                        </button>

                        {/* User Dropdown Menu */}
                        {showUserMenu && (
                            <div className="absolute left-0 mt-2 w-64 glass-dark border border-gold-500/20 rounded-lg shadow-xl overflow-hidden">
                                {/* Mobile Only: User Details Header inside Menu */}
                                <div className="lg:hidden p-4 border-b border-gold-500/10 bg-obsidian-800/50">
                                    <div className="flex flex-col items-start">
                                        <span className="text-sm font-bold text-white mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                            {isAssistant ? 'المساعد' : 'المحامي'} {profile?.full_name || ''}
                                        </span>
                                        {isAssistant && officeLawyer && (
                                            <span className="text-xs text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                                مساعد لـ: {officeLawyer.full_name}
                                            </span>
                                        )}
                                    </div>
                                </div>

                                <button
                                    onClick={() => {
                                        navigate('/settings')
                                        setShowUserMenu(false)
                                    }}
                                    className="w-full flex items-center gap-3 px-4 py-3 hover:bg-obsidian-700 transition text-right"
                                >
                                    <Settings className="w-4 h-4 text-gray-400" />
                                    <span className="text-sm text-white" style={{ fontFamily: 'Cairo, sans-serif' }}>الإعدادات</span>
                                </button>
                                <div className="border-t border-gold-500/10"></div>
                                <button
                                    onClick={handleLogout}
                                    className="w-full flex items-center gap-3 px-4 py-3 hover:bg-error/10 transition text-right"
                                >
                                    <LogOut className="w-4 h-4 text-error" />
                                    <span className="text-sm text-error" style={{ fontFamily: 'Cairo, sans-serif' }}>تسجيل الخروج</span>
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </header>
    )
}
