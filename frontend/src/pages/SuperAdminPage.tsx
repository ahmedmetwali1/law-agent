import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';
import {
    Settings,
    Users,
    Activity,
    Database,
    RefreshCw,
    Save,
    Shield,
    TrendingUp,
    Server,
    Cpu,
    HardDrive,
    UserCog,
    Eye,
    Edit3,
    Check,
    X,
    AlertTriangle,
    Zap,
    Globe,
    ChevronLeft,
    ChevronRight
} from 'lucide-react';
import {
    getPlatformSettings,
    updatePlatformSettings,
    getAllLawyers,
    getLawyersStats,
    getSystemHealth,
    clearCache,
    getAllRoles,
    PlatformSettings,
    LawyerInfo,
    LawyersStats,
    SystemHealth,
    Role,
    ADMIN_ROLE_ID
} from '../api/admin';
import { toast } from 'sonner';

export default function SuperAdminPage() {
    const { user } = useAuth();
    const navigate = useNavigate();

    // State
    const [activeTab, setActiveTab] = useState('overview');
    const [settings, setSettings] = useState<PlatformSettings | null>(null);
    const [lawyers, setLawyers] = useState<LawyerInfo[]>([]);
    const [lawyersStats, setLawyersStats] = useState<LawyersStats | null>(null);
    const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
    const [roles, setRoles] = useState<Role[]>([]);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [editedSettings, setEditedSettings] = useState<Partial<PlatformSettings>>({});

    // Pagination for lawyers
    const [currentPage, setCurrentPage] = useState(1);
    const LAWYERS_PER_PAGE = 6;

    // Check Admin role
    useEffect(() => {
        if (user && user.role_id !== ADMIN_ROLE_ID && user.role?.name !== 'admin') {
            navigate('/dashboard');
        }
    }, [user, navigate]);

    // Load data
    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            setLoading(true);
            const [settingsData, lawyersData, statsData, healthData, rolesData] = await Promise.all([
                getPlatformSettings().catch(() => null),
                getAllLawyers().catch(() => []),
                getLawyersStats().catch(() => null),
                getSystemHealth().catch(() => null),
                getAllRoles().catch(() => [])
            ]);

            setSettings(settingsData);
            setEditedSettings(settingsData || {});
            setLawyers(lawyersData);
            setLawyersStats(statsData);
            setSystemHealth(healthData);
            setRoles(rolesData);
        } catch (error) {
            console.error('❌ Failed to load admin data:', error);
            toast.error('فشل تحميل بيانات الإدارة');
        } finally {
            setLoading(false);
        }
    };

    const handleSaveSettings = async () => {
        try {
            setSaving(true);
            const updated = await updatePlatformSettings(editedSettings);
            setSettings(updated);
            toast.success('تم حفظ الإعدادات بنجاح');
        } catch (error) {
            console.error('❌ Failed to save settings:', error);
            toast.error('فشل حفظ الإعدادات');
        } finally {
            setSaving(false);
        }
    };

    const handleClearCache = async () => {
        if (!confirm('هل أنت متأكد من مسح الـ Cache؟')) return;

        try {
            await clearCache();
            toast.success('تم مسح الـ Cache بنجاح');
            loadData();
        } catch (error) {
            console.error('❌ Failed to clear cache:', error);
            toast.error('فشل مسح الـ Cache');
        }
    };

    // Pagination calculations
    const totalPages = Math.ceil(lawyers.length / LAWYERS_PER_PAGE);
    const startIndex = (currentPage - 1) * LAWYERS_PER_PAGE;
    const currentLawyers = lawyers.slice(startIndex, startIndex + LAWYERS_PER_PAGE);

    const tabs = [
        { id: 'overview', label: 'نظرة عامة', icon: Activity },
        { id: 'platform', label: 'إعدادات المنصة', icon: Settings },
        { id: 'lawyers', label: 'المحامين', icon: Users },
        { id: 'roles', label: 'الأدوار والصلاحيات', icon: UserCog },
        { id: 'technical', label: 'البنية التقنية', icon: Server }
    ];

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gold-500 mx-auto"></div>
                    <p className="text-gray-400 mt-4" style={{ fontFamily: 'Cairo, sans-serif' }}>جاري التحميل...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-gold-500 flex items-center gap-3" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        <Shield className="w-8 h-8" />
                        لوحة تحكم المدير العام
                    </h1>
                    <p className="text-gray-400 mt-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        التحكم الكامل في إعدادات المنصة والمستخدمين
                    </p>
                </div>
                <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={handleSaveSettings}
                    disabled={saving}
                    className="flex items-center gap-2 px-6 py-3 bg-transparent border-2 border-gold-500 text-white font-bold rounded-lg hover:bg-gold-500/10 transition-all disabled:opacity-50"
                    style={{ fontFamily: 'Cairo, sans-serif' }}
                >
                    <Save className="w-5 h-5" />
                    {saving ? 'جاري الحفظ...' : 'حفظ التغييرات'}
                </motion.button>
            </div>

            {/* Tabs */}
            <div className="backdrop-blur-xl bg-obsidian-800/70 border border-gold-500/20 rounded-xl p-2">
                <nav className="flex gap-2 overflow-x-auto">
                    {tabs.map(tab => {
                        const Icon = tab.icon;
                        const isActive = activeTab === tab.id;
                        return (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={`flex items-center gap-2 px-4 py-3 rounded-lg transition-all whitespace-nowrap ${isActive
                                        ? 'bg-gold-500/20 text-gold-500 border border-gold-500/50'
                                        : 'text-gray-400 hover:text-white hover:bg-obsidian-700'
                                    }`}
                                style={{ fontFamily: 'Cairo, sans-serif' }}
                            >
                                <Icon className="w-5 h-5" />
                                {tab.label}
                            </button>
                        );
                    })}
                </nav>
            </div>

            {/* Content */}
            <div className="space-y-6">
                {/* Overview Tab */}
                {activeTab === 'overview' && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="space-y-6"
                    >
                        {/* Stats Cards */}
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                            <motion.div
                                whileHover={{ scale: 1.02 }}
                                className="backdrop-blur-xl bg-obsidian-800/70 border border-gold-500/20 rounded-xl p-6 hover:border-gold-500/50 transition-all"
                            >
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>إجمالي المحامين</p>
                                        <p className="text-3xl font-bold text-white mt-1">{lawyersStats?.total_lawyers || 0}</p>
                                    </div>
                                    <div className="w-12 h-12 rounded-xl bg-gold-500/20 flex items-center justify-center">
                                        <Users className="w-6 h-6 text-gold-500" />
                                    </div>
                                </div>
                                <p className="mt-3 text-sm text-green-400" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                    {lawyersStats?.active_lawyers || 0} نشط
                                </p>
                            </motion.div>

                            <motion.div
                                whileHover={{ scale: 1.02 }}
                                className="backdrop-blur-xl bg-obsidian-800/70 border border-gold-500/20 rounded-xl p-6 hover:border-gold-500/50 transition-all"
                            >
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>إجمالي القضايا</p>
                                        <p className="text-3xl font-bold text-white mt-1">{lawyersStats?.total_cases_all || 0}</p>
                                    </div>
                                    <div className="w-12 h-12 rounded-xl bg-green-500/20 flex items-center justify-center">
                                        <TrendingUp className="w-6 h-6 text-green-500" />
                                    </div>
                                </div>
                            </motion.div>

                            <motion.div
                                whileHover={{ scale: 1.02 }}
                                className="backdrop-blur-xl bg-obsidian-800/70 border border-gold-500/20 rounded-xl p-6 hover:border-gold-500/50 transition-all"
                            >
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>إجمالي الموكلين</p>
                                        <p className="text-3xl font-bold text-white mt-1">{lawyersStats?.total_clients_all || 0}</p>
                                    </div>
                                    <div className="w-12 h-12 rounded-xl bg-blue-500/20 flex items-center justify-center">
                                        <Users className="w-6 h-6 text-blue-500" />
                                    </div>
                                </div>
                            </motion.div>

                            <motion.div
                                whileHover={{ scale: 1.02 }}
                                className="backdrop-blur-xl bg-obsidian-800/70 border border-gold-500/20 rounded-xl p-6 hover:border-gold-500/50 transition-all"
                            >
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>حالة النظام</p>
                                        <p className={`text-3xl font-bold mt-1 ${systemHealth?.status === 'healthy' ? 'text-green-400' : 'text-red-400'}`}>
                                            {systemHealth?.status === 'healthy' ? '✓ سليم' : '✗ مشكلة'}
                                        </p>
                                    </div>
                                    <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${systemHealth?.status === 'healthy' ? 'bg-green-500/20' : 'bg-red-500/20'}`}>
                                        <Activity className={`w-6 h-6 ${systemHealth?.status === 'healthy' ? 'text-green-500' : 'text-red-500'}`} />
                                    </div>
                                </div>
                            </motion.div>
                        </div>

                        {/* System Health Details */}
                        {systemHealth && (
                            <div className="backdrop-blur-xl bg-obsidian-800/70 border border-gold-500/20 rounded-xl p-6">
                                <h3 className="text-xl font-bold text-gold-500 mb-4 flex items-center gap-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                    <HardDrive className="w-5 h-5" />
                                    تفاصيل صحة النظام
                                </h3>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div className="bg-obsidian-900/50 border border-gold-500/10 rounded-lg p-4">
                                        <div className="flex items-center justify-between mb-2">
                                            <span className="font-medium text-white" style={{ fontFamily: 'Cairo, sans-serif' }}>قاعدة البيانات</span>
                                            <span className="px-3 py-1 bg-green-500/20 text-green-400 rounded-full text-sm" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                                نشط
                                            </span>
                                        </div>
                                        <p className="text-sm text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                            وقت الاستجابة: {systemHealth.services?.database?.latency_ms?.toFixed(2) || 0} ms
                                        </p>
                                    </div>

                                    <div className="bg-obsidian-900/50 border border-gold-500/10 rounded-lg p-4">
                                        <div className="flex items-center justify-between mb-2">
                                            <span className="font-medium text-white" style={{ fontFamily: 'Cairo, sans-serif' }}>Redis Cache</span>
                                            <span className={`px-3 py-1 rounded-full text-sm ${systemHealth.services?.cache?.available
                                                    ? 'bg-green-500/20 text-green-400'
                                                    : 'bg-red-500/20 text-red-400'
                                                }`} style={{ fontFamily: 'Cairo, sans-serif' }}>
                                                {systemHealth.services?.cache?.available ? 'متصل' : 'غير متصل'}
                                            </span>
                                        </div>
                                        <div className="flex items-center justify-between">
                                            <p className="text-sm text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                                معدل الإصابة: {systemHealth.services?.cache?.hit_rate || 'N/A'}
                                            </p>
                                            <button
                                                onClick={handleClearCache}
                                                className="text-sm text-gold-500 hover:text-gold-400 transition-colors"
                                                style={{ fontFamily: 'Cairo, sans-serif' }}
                                            >
                                                مسح الـ Cache
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </motion.div>
                )}

                {/* Platform Settings Tab */}
                {activeTab === 'platform' && settings && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="space-y-6"
                    >
                        <div className="backdrop-blur-xl bg-obsidian-800/70 border border-gold-500/20 rounded-xl p-6">
                            <h3 className="text-xl font-bold text-gold-500 mb-6 flex items-center gap-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                <Globe className="w-5 h-5" />
                                معلومات المنصة الأساسية
                            </h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                        اسم المنصة (عربي)
                                    </label>
                                    <input
                                        type="text"
                                        value={editedSettings.platform_name || ''}
                                        onChange={(e) => setEditedSettings({ ...editedSettings, platform_name: e.target.value })}
                                        className="w-full px-4 py-3 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold-500 transition-colors"
                                        style={{ fontFamily: 'Cairo, sans-serif' }}
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                        اسم المنصة (English)
                                    </label>
                                    <input
                                        type="text"
                                        value={editedSettings.platform_name_en || ''}
                                        onChange={(e) => setEditedSettings({ ...editedSettings, platform_name_en: e.target.value })}
                                        className="w-full px-4 py-3 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold-500 transition-colors"
                                    />
                                </div>

                                <div className="md:col-span-2">
                                    <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                        وصف المنصة
                                    </label>
                                    <textarea
                                        value={editedSettings.platform_description || ''}
                                        onChange={(e) => setEditedSettings({ ...editedSettings, platform_description: e.target.value })}
                                        rows={3}
                                        className="w-full px-4 py-3 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold-500 transition-colors resize-none"
                                        style={{ fontFamily: 'Cairo, sans-serif' }}
                                    />
                                </div>
                            </div>
                        </div>
                    </motion.div>
                )}

                {/* Lawyers Management Tab */}
                {activeTab === 'lawyers' && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="space-y-6"
                    >
                        <div className="backdrop-blur-xl bg-obsidian-800/70 border border-gold-500/20 rounded-xl overflow-hidden">
                            <div className="p-6 border-b border-gold-500/10">
                                <h3 className="text-xl font-bold text-gold-500 flex items-center gap-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                    <Users className="w-5 h-5" />
                                    إدارة المحامين
                                </h3>
                                <p className="text-sm text-gray-400 mt-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                    إجمالي: {lawyers.length} محامي ({lawyersStats?.active_lawyers || 0} نشط)
                                </p>
                            </div>

                            {lawyers.length === 0 ? (
                                <div className="text-center py-12">
                                    <Users className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                                    <h3 className="text-xl font-bold text-gray-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                        لا يوجد محامين
                                    </h3>
                                </div>
                            ) : (
                                <>
                                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-6">
                                        {currentLawyers.map((lawyer, index) => (
                                            <motion.div
                                                key={lawyer.id}
                                                initial={{ opacity: 0, y: 10 }}
                                                animate={{ opacity: 1, y: 0 }}
                                                transition={{ delay: index * 0.05 }}
                                                className="bg-obsidian-900/50 border border-gold-500/10 rounded-lg p-4 hover:border-gold-500/30 transition-all"
                                            >
                                                <div className="flex items-start justify-between mb-3">
                                                    <div className="flex-1">
                                                        <h4 className="font-bold text-white" style={{ fontFamily: 'Cairo, sans-serif' }}>{lawyer.full_name}</h4>
                                                        <p className="text-sm text-gray-400">{lawyer.email}</p>
                                                    </div>
                                                    <span className={`px-2 py-1 text-xs rounded-full ${lawyer.is_active
                                                            ? 'bg-green-500/20 text-green-400'
                                                            : 'bg-red-500/20 text-red-400'
                                                        }`} style={{ fontFamily: 'Cairo, sans-serif' }}>
                                                        {lawyer.is_active ? 'نشط' : 'معطل'}
                                                    </span>
                                                </div>
                                                <div className="flex items-center gap-4 text-sm text-gray-400">
                                                    <span style={{ fontFamily: 'Cairo, sans-serif' }}>{lawyer.total_cases || 0} قضية</span>
                                                    <span style={{ fontFamily: 'Cairo, sans-serif' }}>{lawyer.total_clients || 0} موكل</span>
                                                </div>
                                            </motion.div>
                                        ))}
                                    </div>

                                    {/* Pagination */}
                                    {totalPages > 1 && (
                                        <div className="flex items-center justify-center gap-2 p-4 border-t border-gold-500/10">
                                            <button
                                                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                                                disabled={currentPage === 1}
                                                className="p-2 rounded-lg bg-obsidian-900 border border-gold-500/20 text-white hover:border-gold-500/50 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                                            >
                                                <ChevronRight className="w-5 h-5" />
                                            </button>

                                            <div className="flex items-center gap-2">
                                                {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
                                                    <button
                                                        key={page}
                                                        onClick={() => setCurrentPage(page)}
                                                        className={`px-4 py-2 rounded-lg font-medium transition-all ${currentPage === page
                                                                ? 'bg-gold-500 text-obsidian-900'
                                                                : 'bg-obsidian-900 border border-gold-500/20 text-white hover:border-gold-500/50'
                                                            }`}
                                                        style={{ fontFamily: 'Cairo, sans-serif' }}
                                                    >
                                                        {page}
                                                    </button>
                                                ))}
                                            </div>

                                            <button
                                                onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                                                disabled={currentPage === totalPages}
                                                className="p-2 rounded-lg bg-obsidian-900 border border-gold-500/20 text-white hover:border-gold-500/50 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                                            >
                                                <ChevronLeft className="w-5 h-5" />
                                            </button>
                                        </div>
                                    )}
                                </>
                            )}
                        </div>
                    </motion.div>
                )}

                {/* Roles Management Tab */}
                {activeTab === 'roles' && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="space-y-6"
                    >
                        <div className="backdrop-blur-xl bg-obsidian-800/70 border border-gold-500/20 rounded-xl overflow-hidden">
                            <div className="p-6 border-b border-gold-500/10">
                                <h3 className="text-xl font-bold text-gold-500 flex items-center gap-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                    <UserCog className="w-5 h-5" />
                                    إدارة الأدوار والصلاحيات
                                </h3>
                                <p className="text-sm text-gray-400 mt-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                    إجمالي: {roles.length} أدوار
                                </p>
                            </div>

                            {roles.length === 0 ? (
                                <div className="text-center py-12">
                                    <UserCog className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                                    <h3 className="text-xl font-bold text-gray-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                        لا يوجد أدوار
                                    </h3>
                                </div>
                            ) : (
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-6">
                                    {roles.map((role, index) => (
                                        <motion.div
                                            key={role.id}
                                            initial={{ opacity: 0, y: 10 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            transition={{ delay: index * 0.05 }}
                                            className="bg-obsidian-900/50 border border-gold-500/10 rounded-lg p-4 hover:border-gold-500/30 transition-all"
                                        >
                                            <div className="flex items-start justify-between mb-3">
                                                <div className="flex-1">
                                                    <h4 className="font-bold text-white" style={{ fontFamily: 'Cairo, sans-serif' }}>{role.name_ar || role.name}</h4>
                                                    <p className="text-sm text-gray-400">{role.name}</p>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <span className={`px-2 py-1 text-xs rounded-full ${role.is_active
                                                            ? 'bg-green-500/20 text-green-400'
                                                            : 'bg-red-500/20 text-red-400'
                                                        }`} style={{ fontFamily: 'Cairo, sans-serif' }}>
                                                        {role.is_active ? 'نشط' : 'معطل'}
                                                    </span>
                                                    {role.is_default && (
                                                        <span className="px-2 py-1 text-xs bg-blue-500/20 text-blue-400 rounded-full" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                                            افتراضي
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                            {role.description && (
                                                <p className="text-sm text-gray-500 line-clamp-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                                    {role.description}
                                                </p>
                                            )}
                                            <div className="flex flex-wrap gap-1 mt-3">
                                                {Object.keys(role.permissions || {}).slice(0, 3).map(key => (
                                                    <span key={key} className="px-2 py-0.5 bg-gold-500/10 text-gold-500 rounded text-xs">
                                                        {key}
                                                    </span>
                                                ))}
                                                {Object.keys(role.permissions || {}).length > 3 && (
                                                    <span className="px-2 py-0.5 bg-gray-500/20 text-gray-400 rounded text-xs">
                                                        +{Object.keys(role.permissions || {}).length - 3}
                                                    </span>
                                                )}
                                            </div>
                                        </motion.div>
                                    ))}
                                </div>
                            )}
                        </div>

                        {/* Permissions Legend */}
                        <div className="backdrop-blur-xl bg-obsidian-800/70 border border-gold-500/20 rounded-xl p-6">
                            <h4 className="text-lg font-bold text-gold-500 mb-4" style={{ fontFamily: 'Cairo, sans-serif' }}>دليل الصلاحيات</h4>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                                <div className="flex items-center gap-2">
                                    <span className="w-3 h-3 bg-green-500 rounded"></span>
                                    <span className="text-gray-300" style={{ fontFamily: 'Cairo, sans-serif' }}>read - قراءة</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <span className="w-3 h-3 bg-blue-500 rounded"></span>
                                    <span className="text-gray-300" style={{ fontFamily: 'Cairo, sans-serif' }}>create - إنشاء</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <span className="w-3 h-3 bg-yellow-500 rounded"></span>
                                    <span className="text-gray-300" style={{ fontFamily: 'Cairo, sans-serif' }}>update - تحديث</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <span className="w-3 h-3 bg-red-500 rounded"></span>
                                    <span className="text-gray-300" style={{ fontFamily: 'Cairo, sans-serif' }}>delete - حذف</span>
                                </div>
                            </div>
                        </div>
                    </motion.div>
                )}

                {/* Technical Infrastructure Tab */}
                {activeTab === 'technical' && settings && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="space-y-6"
                    >
                        {/* Redis Configuration */}
                        <div className="backdrop-blur-xl bg-obsidian-800/70 border border-gold-500/20 rounded-xl p-6">
                            <h3 className="text-xl font-bold text-gold-500 mb-6 flex items-center gap-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                <Database className="w-5 h-5" />
                                إعدادات Redis Cache
                            </h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div className="flex items-center gap-3">
                                    <input
                                        type="checkbox"
                                        id="redis_enabled"
                                        checked={editedSettings.redis_enabled || false}
                                        onChange={(e) => setEditedSettings({ ...editedSettings, redis_enabled: e.target.checked })}
                                        className="w-5 h-5 rounded border-gold-500/30 bg-obsidian-900/50 text-gold-500 focus:ring-gold-500"
                                    />
                                    <label htmlFor="redis_enabled" className="text-sm font-medium text-gold-500" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                        تفعيل Redis
                                    </label>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>Redis Host</label>
                                    <input
                                        type="text"
                                        value={editedSettings.redis_host || ''}
                                        onChange={(e) => setEditedSettings({ ...editedSettings, redis_host: e.target.value })}
                                        className="w-full px-4 py-3 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white focus:outline-none focus:border-gold-500 transition-colors"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>Redis Port</label>
                                    <input
                                        type="number"
                                        value={editedSettings.redis_port || 6379}
                                        onChange={(e) => setEditedSettings({ ...editedSettings, redis_port: parseInt(e.target.value) })}
                                        className="w-full px-4 py-3 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white focus:outline-none focus:border-gold-500 transition-colors"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>Redis Password</label>
                                    <input
                                        type="password"
                                        value={editedSettings.redis_password || ''}
                                        onChange={(e) => setEditedSettings({ ...editedSettings, redis_password: e.target.value })}
                                        className="w-full px-4 py-3 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white focus:outline-none focus:border-gold-500 transition-colors"
                                    />
                                </div>
                            </div>
                        </div>

                        {/* AI Configuration */}
                        <div className="backdrop-blur-xl bg-obsidian-800/70 border border-gold-500/20 rounded-xl p-6">
                            <h3 className="text-xl font-bold text-gold-500 mb-6 flex items-center gap-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                <Zap className="w-5 h-5" />
                                إعدادات الذكاء الاصطناعي
                            </h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>AI Provider</label>
                                    <input
                                        type="text"
                                        value={editedSettings.ai_provider || ''}
                                        onChange={(e) => setEditedSettings({ ...editedSettings, ai_provider: e.target.value })}
                                        className="w-full px-4 py-3 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white focus:outline-none focus:border-gold-500 transition-colors"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>Model Name</label>
                                    <input
                                        type="text"
                                        value={editedSettings.ai_model_name || ''}
                                        onChange={(e) => setEditedSettings({ ...editedSettings, ai_model_name: e.target.value })}
                                        className="w-full px-4 py-3 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white focus:outline-none focus:border-gold-500 transition-colors"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>API URL</label>
                                    <input
                                        type="text"
                                        value={editedSettings.ai_api_url || ''}
                                        onChange={(e) => setEditedSettings({ ...editedSettings, ai_api_url: e.target.value })}
                                        className="w-full px-4 py-3 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white focus:outline-none focus:border-gold-500 transition-colors"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>API Key</label>
                                    <input
                                        type="password"
                                        value={editedSettings.ai_api_key || ''}
                                        onChange={(e) => setEditedSettings({ ...editedSettings, ai_api_key: e.target.value })}
                                        className="w-full px-4 py-3 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white focus:outline-none focus:border-gold-500 transition-colors"
                                    />
                                </div>
                            </div>
                        </div>
                    </motion.div>
                )}
            </div>
        </div>
    );
}
