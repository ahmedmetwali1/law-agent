import { useState } from 'react';
import { Link, useLocation, Outlet } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
    LayoutDashboard,
    Users,
    UserCog,
    Settings,
    Brain,
    HeadphonesIcon,
    Bell,
    Server,
    Shield,
    FileText,
    ChevronLeft,
    ChevronRight,
    LogOut,
    Home,
    CreditCard
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

interface NavItem {
    id: string;
    label: string;
    icon: any;
    path: string;
}

const adminNavItems: NavItem[] = [
    { id: 'overview', label: 'الرئيسية', icon: LayoutDashboard, path: '/admin' },
    { id: 'subscriptions', label: 'الاشتراكات والتسعير', icon: CreditCard, path: '/admin/subscriptions' },
    { id: 'lawyers', label: 'المحامين', icon: Users, path: '/admin/lawyers' },
    { id: 'roles', label: 'الأدوار والصلاحيات', icon: UserCog, path: '/admin/roles' },
    { id: 'platform', label: 'إعدادات المنصة', icon: Settings, path: '/admin/platform' },
    { id: 'ai', label: 'الذكاء الاصطناعي', icon: Brain, path: '/admin/ai' },
    { id: 'announcements', label: 'الإعلانات', icon: Bell, path: '/admin/announcements' },
    { id: 'infrastructure', label: 'البنية التحتية', icon: Server, path: '/admin/infrastructure' },
    { id: 'support', label: 'تذاكر الدعم', icon: HeadphonesIcon, path: '/admin/support' },
    { id: 'security', label: 'الأمان', icon: Shield, path: '/admin/security' },
    { id: 'audit', label: 'سجل التدقيق', icon: FileText, path: '/admin/audit' },
];

export default function AdminLayout() {
    const location = useLocation();
    const navigate = useNavigate();
    const { user, signOut } = useAuth();
    const [isCollapsed, setIsCollapsed] = useState(false);

    const handleLogout = async () => {
        await signOut();
        navigate('/login');
    };

    const handleBackToOffice = () => {
        navigate('/dashboard');
    };

    return (
        <div className="min-h-screen bg-obsidian-900 flex" dir="rtl">
            {/* Admin Sidebar */}
            <motion.aside
                initial={false}
                animate={{ width: isCollapsed ? 80 : 280 }}
                className="fixed right-0 top-0 h-full bg-obsidian-800 border-l border-purple-500/20 z-40 flex flex-col"
            >
                {/* Header */}
                <div className="p-4 border-b border-purple-500/10">
                    <div className="flex items-center justify-between">
                        <div className={`flex items-center gap-3 ${isCollapsed ? 'justify-center' : ''}`}>
                            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-600 to-purple-500 flex items-center justify-center shadow-lg shadow-purple-600/20">
                                <Shield className="w-5 h-5 text-white" />
                            </div>
                            {!isCollapsed && (
                                <motion.div
                                    initial={{ opacity: 0, x: -10 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    exit={{ opacity: 0, x: -10 }}
                                >
                                    <h1 className="text-lg font-bold text-purple-500" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                        لوحة الإدارة
                                    </h1>
                                    <p className="text-xs text-gray-500" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                        السوبر أدمن
                                    </p>
                                </motion.div>
                            )}
                        </div>
                        <button
                            onClick={() => setIsCollapsed(!isCollapsed)}
                            className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-obsidian-700 transition-all"
                        >
                            {isCollapsed ? <ChevronLeft className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
                        </button>
                    </div>
                </div>

                {/* Back to Office Button */}
                <div className="p-2">
                    <button
                        onClick={handleBackToOffice}
                        className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-gold-500 hover:bg-gold-500/10 transition-all ${isCollapsed ? 'justify-center' : ''}`}
                        style={{ fontFamily: 'Cairo, sans-serif' }}
                    >
                        <Home className="w-5 h-5 flex-shrink-0" />
                        {!isCollapsed && <span>العودة للمكتب</span>}
                    </button>
                </div>

                {/* Navigation */}
                <nav className="flex-1 p-2 space-y-1 overflow-y-auto">
                    {adminNavItems.map(item => {
                        const Icon = item.icon;
                        const isActive = location.pathname === item.path ||
                            (item.path !== '/admin' && location.pathname.startsWith(item.path));

                        return (
                            <Link
                                key={item.id}
                                to={item.path}
                                className={`group relative flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 ${isActive
                                    ? 'bg-purple-600 text-white shadow-lg shadow-purple-600/20'
                                    : 'text-gray-400 hover:bg-obsidian-700 hover:text-white'
                                    } ${isCollapsed ? 'justify-center' : ''}`}
                            >
                                {isActive && (
                                    <motion.div
                                        layoutId="adminActiveTab"
                                        className="absolute right-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-purple-400 rounded-l-full"
                                    />
                                )}
                                <Icon className="w-5 h-5 flex-shrink-0" />
                                {!isCollapsed && (
                                    <motion.span
                                        initial={{ opacity: 0, x: -10 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        exit={{ opacity: 0, x: -10 }}
                                        className="font-medium text-sm whitespace-nowrap"
                                        style={{ fontFamily: 'Cairo, sans-serif' }}
                                    >
                                        {item.label}
                                    </motion.span>
                                )}
                                {!isActive && !isCollapsed && (
                                    <div className="absolute inset-0 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity bg-gradient-to-l from-purple-600/10 to-transparent" />
                                )}
                            </Link>
                        );
                    })}
                </nav>

                {/* User Info & Logout */}
                <div className="p-4 border-t border-purple-500/10">
                    {!isCollapsed && user && (
                        <div className="mb-3">
                            <p className="text-sm font-medium text-white" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                {user.full_name}
                            </p>
                            <p className="text-xs text-gray-500">
                                {user.email}
                            </p>
                        </div>
                    )}
                    <button
                        onClick={handleLogout}
                        className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-red-400 hover:bg-red-500/10 transition-all ${isCollapsed ? 'justify-center' : ''}`}
                        style={{ fontFamily: 'Cairo, sans-serif' }}
                    >
                        <LogOut className="w-5 h-5 flex-shrink-0" />
                        {!isCollapsed && <span>تسجيل الخروج</span>}
                    </button>
                </div>
            </motion.aside>

            {/* Main Content */}
            <main
                className="flex-1 transition-all duration-300"
                style={{ marginRight: isCollapsed ? 80 : 280 }}
            >
                <div className="p-6">
                    <Outlet />
                </div>
            </main>
        </div>
    );
}
