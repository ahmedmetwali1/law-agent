import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
    Users,
    Briefcase,
    UserCheck,
    Activity,
    TrendingUp,
    Clock,
    AlertTriangle,
    CheckCircle,
    Server,
    Database,
    Cpu,
    RefreshCw
} from 'lucide-react';
import {
    getPlatformSettings,
    getAllLawyers,
    getLawyersStats,
    getSystemHealth,
    LawyersStats,
    SystemHealth,
    PlatformSettings
} from '../../api/admin';
import { toast } from 'sonner';

export default function AdminDashboard() {
    const [loading, setLoading] = useState(true);
    const [stats, setStats] = useState<LawyersStats | null>(null);
    const [health, setHealth] = useState<SystemHealth | null>(null);
    const [settings, setSettings] = useState<PlatformSettings | null>(null);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            setLoading(true);
            const [statsData, healthData, settingsData] = await Promise.all([
                getLawyersStats().catch(() => null),
                getSystemHealth().catch(() => null),
                getPlatformSettings().catch(() => null)
            ]);
            setStats(statsData);
            setHealth(healthData);
            setSettings(settingsData);
        } catch (error) {
            console.error('Error loading dashboard:', error);
            toast.error('فشل تحميل البيانات');
        } finally {
            setLoading(false);
        }
    };

    const StatCard = ({ title, value, icon: Icon, color, subtitle }: any) => (
        <motion.div
            whileHover={{ scale: 1.02 }}
            className="backdrop-blur-xl bg-obsidian-800/70 border border-purple-500/20 rounded-xl p-6 hover:border-purple-500/50 transition-all"
        >
            <div className="flex items-center justify-between">
                <div>
                    <p className="text-sm text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>{title}</p>
                    <p className="text-3xl font-bold text-white mt-1">{value}</p>
                    {subtitle && <p className="mt-2 text-sm text-gray-500" style={{ fontFamily: 'Cairo, sans-serif' }}>{subtitle}</p>}
                </div>
                <div className={`w-12 h-12 rounded-xl ${color} flex items-center justify-center`}>
                    <Icon className="w-6 h-6 text-white" />
                </div>
            </div>
        </motion.div>
    );

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[60vh]">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto"></div>
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
                    <h1 className="text-2xl font-bold text-purple-500" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        لوحة التحكم الرئيسية
                    </h1>
                    <p className="text-gray-400 mt-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        نظرة عامة على المنصة
                    </p>
                </div>
                <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={loadData}
                    className="flex items-center gap-2 px-4 py-2 bg-obsidian-800 border border-purple-500/30 text-white rounded-lg hover:bg-purple-500/10 transition-all"
                    style={{ fontFamily: 'Cairo, sans-serif' }}
                >
                    <RefreshCw className="w-4 h-4" />
                    تحديث
                </motion.button>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard
                    title="إجمالي المحامين"
                    value={stats?.total_lawyers || 0}
                    icon={Users}
                    color="bg-purple-500/20"
                    subtitle={`${stats?.active_lawyers || 0} نشط`}
                />
                <StatCard
                    title="إجمالي القضايا"
                    value={stats?.total_cases_all || 0}
                    icon={Briefcase}
                    color="bg-blue-500/20"
                />
                <StatCard
                    title="إجمالي الموكلين"
                    value={stats?.total_clients_all || 0}
                    icon={UserCheck}
                    color="bg-green-500/20"
                />
                <StatCard
                    title="حالة النظام"
                    value={health?.status === 'healthy' ? 'سليم ✓' : 'مشكلة ✗'}
                    icon={Activity}
                    color={health?.status === 'healthy' ? 'bg-green-500/20' : 'bg-red-500/20'}
                />
            </div>

            {/* System Health */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Services Status */}
                <div className="backdrop-blur-xl bg-obsidian-800/70 border border-purple-500/20 rounded-xl p-6">
                    <h3 className="text-lg font-bold text-purple-500 mb-4 flex items-center gap-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        <Server className="w-5 h-5" />
                        حالة الخدمات
                    </h3>
                    <div className="space-y-4">
                        {/* Database */}
                        <div className="flex items-center justify-between p-3 bg-obsidian-900/50 rounded-lg">
                            <div className="flex items-center gap-3">
                                <Database className="w-5 h-5 text-gray-400" />
                                <span className="font-medium text-white" style={{ fontFamily: 'Cairo, sans-serif' }}>قاعدة البيانات</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="text-sm text-gray-400">
                                    {health?.services?.database?.latency_ms?.toFixed(0) || 0} ms
                                </span>
                                <span className="px-2 py-1 bg-green-500/20 text-green-400 rounded-full text-xs" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                    متصل
                                </span>
                            </div>
                        </div>

                        {/* Redis */}
                        <div className="flex items-center justify-between p-3 bg-obsidian-900/50 rounded-lg">
                            <div className="flex items-center gap-3">
                                <Cpu className="w-5 h-5 text-gray-400" />
                                <span className="font-medium text-white" style={{ fontFamily: 'Cairo, sans-serif' }}>Redis Cache</span>
                            </div>
                            <span className={`px-2 py-1 rounded-full text-xs ${health?.services?.cache?.available
                                    ? 'bg-green-500/20 text-green-400'
                                    : 'bg-red-500/20 text-red-400'
                                }`} style={{ fontFamily: 'Cairo, sans-serif' }}>
                                {health?.services?.cache?.available ? 'متصل' : 'غير متصل'}
                            </span>
                        </div>

                        {/* AI Service */}
                        <div className="flex items-center justify-between p-3 bg-obsidian-900/50 rounded-lg">
                            <div className="flex items-center gap-3">
                                <TrendingUp className="w-5 h-5 text-gray-400" />
                                <span className="font-medium text-white" style={{ fontFamily: 'Cairo, sans-serif' }}>الذكاء الاصطناعي</span>
                            </div>
                            <span className="px-2 py-1 bg-green-500/20 text-green-400 rounded-full text-xs" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                {settings?.ai_provider || 'openwebui'}
                            </span>
                        </div>
                    </div>
                </div>

                {/* Platform Info */}
                <div className="backdrop-blur-xl bg-obsidian-800/70 border border-purple-500/20 rounded-xl p-6">
                    <h3 className="text-lg font-bold text-purple-500 mb-4 flex items-center gap-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        <Activity className="w-5 h-5" />
                        معلومات المنصة
                    </h3>
                    <div className="space-y-4">
                        <div className="p-3 bg-obsidian-900/50 rounded-lg">
                            <p className="text-sm text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>اسم المنصة</p>
                            <p className="text-white font-medium">{settings?.platform_name || 'منصة إدارة المكاتب القانونية'}</p>
                        </div>
                        <div className="p-3 bg-obsidian-900/50 rounded-lg">
                            <p className="text-sm text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>نموذج الذكاء الاصطناعي</p>
                            <p className="text-white font-medium">{settings?.ai_model_name || 'غير محدد'}</p>
                        </div>
                        <div className="p-3 bg-obsidian-900/50 rounded-lg">
                            <p className="text-sm text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>المنطقة الزمنية</p>
                            <p className="text-white font-medium">{settings?.timezone || 'Asia/Riyadh'}</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Quick Actions */}
            <div className="backdrop-blur-xl bg-obsidian-800/70 border border-purple-500/20 rounded-xl p-6">
                <h3 className="text-lg font-bold text-purple-500 mb-4" style={{ fontFamily: 'Cairo, sans-serif' }}>
                    إجراءات سريعة
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <motion.button
                        whileHover={{ scale: 1.02 }}
                        className="p-4 bg-obsidian-900/50 border border-purple-500/10 rounded-lg text-center hover:border-purple-500/30 transition-all"
                    >
                        <Users className="w-8 h-8 text-purple-500 mx-auto mb-2" />
                        <span className="text-sm text-gray-300" style={{ fontFamily: 'Cairo, sans-serif' }}>إدارة المحامين</span>
                    </motion.button>
                    <motion.button
                        whileHover={{ scale: 1.02 }}
                        className="p-4 bg-obsidian-900/50 border border-purple-500/10 rounded-lg text-center hover:border-purple-500/30 transition-all"
                    >
                        <AlertTriangle className="w-8 h-8 text-yellow-500 mx-auto mb-2" />
                        <span className="text-sm text-gray-300" style={{ fontFamily: 'Cairo, sans-serif' }}>إعلان جديد</span>
                    </motion.button>
                    <motion.button
                        whileHover={{ scale: 1.02 }}
                        className="p-4 bg-obsidian-900/50 border border-purple-500/10 rounded-lg text-center hover:border-purple-500/30 transition-all"
                    >
                        <CheckCircle className="w-8 h-8 text-green-500 mx-auto mb-2" />
                        <span className="text-sm text-gray-300" style={{ fontFamily: 'Cairo, sans-serif' }}>تذاكر الدعم</span>
                    </motion.button>
                    <motion.button
                        whileHover={{ scale: 1.02 }}
                        className="p-4 bg-obsidian-900/50 border border-purple-500/10 rounded-lg text-center hover:border-purple-500/30 transition-all"
                    >
                        <Clock className="w-8 h-8 text-blue-500 mx-auto mb-2" />
                        <span className="text-sm text-gray-300" style={{ fontFamily: 'Cairo, sans-serif' }}>سجل التدقيق</span>
                    </motion.button>
                </div>
            </div>
        </div>
    );
}
