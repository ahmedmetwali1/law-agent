import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
    Server,
    Save,
    RefreshCw,
    Database,
    Cpu,
    HardDrive,
    Mail,
    MessageSquare,
    ToggleLeft,
    ToggleRight,
    Key,
    Link as LinkIcon,
    Hash,
    AlertTriangle,
    CheckCircle,
    XCircle,
    Activity
} from 'lucide-react';
import { getPlatformSettings, updatePlatformSettings, getSystemHealth, PlatformSettings, SystemHealth } from '../../api/admin';
import { toast } from 'sonner';

export default function InfrastructurePage() {
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [settings, setSettings] = useState<Partial<PlatformSettings>>({});
    const [health, setHealth] = useState<SystemHealth | null>(null);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            setLoading(true);
            const [settingsData, healthData] = await Promise.all([
                getPlatformSettings(),
                getSystemHealth().catch(() => null)
            ]);
            setSettings(settingsData);
            setHealth(healthData);
        } catch (error) {
            console.error('Error loading data:', error);
            toast.error('فشل تحميل البيانات');
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        try {
            setSaving(true);
            await updatePlatformSettings(settings);
            toast.success('تم حفظ الإعدادات بنجاح');
        } catch (error) {
            console.error('Error saving settings:', error);
            toast.error('فشل حفظ الإعدادات');
        } finally {
            setSaving(false);
        }
    };

    const StatusBadge = ({ active, label }: { active: boolean, label?: string }) => (
        <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm ${active ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
            }`} style={{ fontFamily: 'Cairo, sans-serif' }}>
            {active ? <CheckCircle className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
            {label || (active ? 'متصل' : 'غير متصل')}
        </span>
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
                    <h1 className="text-2xl font-bold text-purple-500 flex items-center gap-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        <Server className="w-7 h-7" />
                        البنية التحتية
                    </h1>
                    <p className="text-gray-400 mt-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        إعدادات Redis, SMTP, Telegram وحالة النظام
                    </p>
                </div>
                <div className="flex gap-2">
                    <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={loadData}
                        className="flex items-center gap-2 px-4 py-2 bg-obsidian-800 border border-purple-500/30 text-white rounded-lg hover:bg-purple-500/10 transition-all"
                    >
                        <RefreshCw className="w-4 h-4" />
                    </motion.button>
                    <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={handleSave}
                        disabled={saving}
                        className="flex items-center gap-2 px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-all disabled:opacity-50"
                        style={{ fontFamily: 'Cairo, sans-serif' }}
                    >
                        <Save className="w-4 h-4" />
                        {saving ? 'جاري الحفظ...' : 'حفظ'}
                    </motion.button>
                </div>
            </div>

            {/* System Status */}
            <div className="backdrop-blur-xl bg-obsidian-800/70 border border-purple-500/20 rounded-xl p-6">
                <h3 className="text-lg font-bold text-purple-500 mb-6 flex items-center gap-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                    <Activity className="w-5 h-5" />
                    حالة النظام
                </h3>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="p-4 bg-obsidian-900/50 rounded-lg text-center">
                        <Database className="w-8 h-8 text-blue-400 mx-auto mb-2" />
                        <p className="text-sm text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>قاعدة البيانات</p>
                        <StatusBadge active={true} />
                        {health?.services?.database?.latency_ms && (
                            <p className="text-xs text-gray-500 mt-1">{health.services.database.latency_ms.toFixed(0)} ms</p>
                        )}
                    </div>

                    <div className="p-4 bg-obsidian-900/50 rounded-lg text-center">
                        <Cpu className="w-8 h-8 text-purple-400 mx-auto mb-2" />
                        <p className="text-sm text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>Redis Cache</p>
                        <StatusBadge active={health?.services?.cache?.available || false} />
                        {health?.services?.cache?.hit_rate !== undefined && (
                            <p className="text-xs text-gray-500 mt-1">Hit Rate: {(Number(health.services.cache.hit_rate) * 100).toFixed(0)}%</p>
                        )}
                    </div>

                    <div className="p-4 bg-obsidian-900/50 rounded-lg text-center">
                        <HardDrive className="w-8 h-8 text-green-400 mx-auto mb-2" />
                        <p className="text-sm text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>التخزين</p>
                        <StatusBadge active={true} label="متاح" />
                    </div>

                    <div className="p-4 bg-obsidian-900/50 rounded-lg text-center">
                        <Server className="w-8 h-8 text-yellow-400 mx-auto mb-2" />
                        <p className="text-sm text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>API Server</p>
                        <StatusBadge active={health?.status === 'healthy'} />
                    </div>
                </div>
            </div>

            {/* Redis Configuration */}
            <div className="backdrop-blur-xl bg-obsidian-800/70 border border-purple-500/20 rounded-xl p-6">
                <div className="flex items-center justify-between mb-6">
                    <h3 className="text-lg font-bold text-purple-500 flex items-center gap-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        <Cpu className="w-5 h-5" />
                        Redis Cache
                    </h3>
                    <button
                        onClick={() => setSettings({ ...settings, redis_enabled: !settings.redis_enabled })}
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${settings.redis_enabled
                            ? 'bg-green-500/20 text-green-400'
                            : 'bg-gray-500/20 text-gray-400'
                            }`}
                        style={{ fontFamily: 'Cairo, sans-serif' }}
                    >
                        {settings.redis_enabled ? <ToggleRight className="w-5 h-5" /> : <ToggleLeft className="w-5 h-5" />}
                        {settings.redis_enabled ? 'مفعّل' : 'معطّل'}
                    </button>
                </div>

                {settings.redis_enabled && (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-purple-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                Host
                            </label>
                            <input
                                type="text"
                                value={settings.redis_host || ''}
                                onChange={(e) => setSettings({ ...settings, redis_host: e.target.value })}
                                className="w-full px-4 py-3 bg-obsidian-900/50 border border-purple-500/20 rounded-lg text-white focus:outline-none focus:border-purple-500 transition-colors font-mono text-sm"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-purple-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                Port
                            </label>
                            <input
                                type="number"
                                value={settings.redis_port || 6379}
                                onChange={(e) => setSettings({ ...settings, redis_port: parseInt(e.target.value) })}
                                className="w-full px-4 py-3 bg-obsidian-900/50 border border-purple-500/20 rounded-lg text-white focus:outline-none focus:border-purple-500 transition-colors font-mono text-sm"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-purple-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                Password
                            </label>
                            <input
                                type="password"
                                value={settings.redis_password || ''}
                                onChange={(e) => setSettings({ ...settings, redis_password: e.target.value })}
                                className="w-full px-4 py-3 bg-obsidian-900/50 border border-purple-500/20 rounded-lg text-white focus:outline-none focus:border-purple-500 transition-colors"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-purple-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                TTL (seconds)
                            </label>
                            <input
                                type="number"
                                value={settings.redis_ttl_default || 300}
                                onChange={(e) => setSettings({ ...settings, redis_ttl_default: parseInt(e.target.value) })}
                                className="w-full px-4 py-3 bg-obsidian-900/50 border border-purple-500/20 rounded-lg text-white focus:outline-none focus:border-purple-500 transition-colors"
                            />
                        </div>
                    </div>
                )}
            </div>

            {/* SMTP Configuration */}
            <div className="backdrop-blur-xl bg-obsidian-800/70 border border-purple-500/20 rounded-xl p-6">
                <div className="flex items-center justify-between mb-6">
                    <h3 className="text-lg font-bold text-purple-500 flex items-center gap-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        <Mail className="w-5 h-5" />
                        SMTP Email
                    </h3>
                    <button
                        onClick={() => setSettings({ ...settings, smtp_enabled: !settings.smtp_enabled })}
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${settings.smtp_enabled
                            ? 'bg-green-500/20 text-green-400'
                            : 'bg-gray-500/20 text-gray-400'
                            }`}
                        style={{ fontFamily: 'Cairo, sans-serif' }}
                    >
                        {settings.smtp_enabled ? <ToggleRight className="w-5 h-5" /> : <ToggleLeft className="w-5 h-5" />}
                        {settings.smtp_enabled ? 'مفعّل' : 'معطّل'}
                    </button>
                </div>

                {settings.smtp_enabled && (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-purple-400 mb-2">Host</label>
                            <input
                                type="text"
                                value={settings.smtp_host || ''}
                                onChange={(e) => setSettings({ ...settings, smtp_host: e.target.value })}
                                placeholder="smtp.gmail.com"
                                className="w-full px-4 py-3 bg-obsidian-900/50 border border-purple-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-purple-400 mb-2">Port</label>
                            <input
                                type="number"
                                value={settings.smtp_port || 587}
                                onChange={(e) => setSettings({ ...settings, smtp_port: parseInt(e.target.value) })}
                                className="w-full px-4 py-3 bg-obsidian-900/50 border border-purple-500/20 rounded-lg text-white focus:outline-none focus:border-purple-500 transition-colors"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-purple-400 mb-2">Username</label>
                            <input
                                type="text"
                                value={settings.smtp_username || ''}
                                onChange={(e) => setSettings({ ...settings, smtp_username: e.target.value })}
                                className="w-full px-4 py-3 bg-obsidian-900/50 border border-purple-500/20 rounded-lg text-white focus:outline-none focus:border-purple-500 transition-colors"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-purple-400 mb-2">Password</label>
                            <input
                                type="password"
                                value={settings.smtp_password || ''}
                                onChange={(e) => setSettings({ ...settings, smtp_password: e.target.value })}
                                className="w-full px-4 py-3 bg-obsidian-900/50 border border-purple-500/20 rounded-lg text-white focus:outline-none focus:border-purple-500 transition-colors"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-purple-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>From Email</label>
                            <input
                                type="email"
                                value={settings.smtp_from_email || ''}
                                onChange={(e) => setSettings({ ...settings, smtp_from_email: e.target.value })}
                                className="w-full px-4 py-3 bg-obsidian-900/50 border border-purple-500/20 rounded-lg text-white focus:outline-none focus:border-purple-500 transition-colors"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-purple-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>From Name</label>
                            <input
                                type="text"
                                value={settings.smtp_from_name || ''}
                                onChange={(e) => setSettings({ ...settings, smtp_from_name: e.target.value })}
                                className="w-full px-4 py-3 bg-obsidian-900/50 border border-purple-500/20 rounded-lg text-white focus:outline-none focus:border-purple-500 transition-colors"
                                style={{ fontFamily: 'Cairo, sans-serif' }}
                            />
                        </div>
                    </div>
                )}
            </div>

            {/* Telegram Bot */}
            <div className="backdrop-blur-xl bg-obsidian-800/70 border border-purple-500/20 rounded-xl p-6">
                <div className="flex items-center justify-between mb-6">
                    <h3 className="text-lg font-bold text-purple-500 flex items-center gap-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        <MessageSquare className="w-5 h-5" />
                        Telegram Bot
                    </h3>
                    <button
                        onClick={() => setSettings({ ...settings, telegram_enabled: !settings.telegram_enabled })}
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${settings.telegram_enabled
                            ? 'bg-green-500/20 text-green-400'
                            : 'bg-gray-500/20 text-gray-400'
                            }`}
                        style={{ fontFamily: 'Cairo, sans-serif' }}
                    >
                        {settings.telegram_enabled ? <ToggleRight className="w-5 h-5" /> : <ToggleLeft className="w-5 h-5" />}
                        {settings.telegram_enabled ? 'مفعّل' : 'معطّل'}
                    </button>
                </div>

                {settings.telegram_enabled && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-purple-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                <span className="flex items-center gap-2"><Key className="w-4 h-4" /> Bot Token</span>
                            </label>
                            <input
                                type="password"
                                value={settings.telegram_bot_token || ''}
                                onChange={(e) => setSettings({ ...settings, telegram_bot_token: e.target.value })}
                                placeholder="123456789:ABCdefGhIJKlmNoPQRstuVWXyz"
                                className="w-full px-4 py-3 bg-obsidian-900/50 border border-purple-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors font-mono text-sm"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-purple-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                <span className="flex items-center gap-2"><Hash className="w-4 h-4" /> Chat ID</span>
                            </label>
                            <input
                                type="text"
                                value={settings.telegram_chat_id || ''}
                                onChange={(e) => setSettings({ ...settings, telegram_chat_id: e.target.value })}
                                placeholder="-1001234567890"
                                className="w-full px-4 py-3 bg-obsidian-900/50 border border-purple-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors font-mono text-sm"
                            />
                        </div>
                    </div>
                )}
            </div>

            {/* Maintenance Mode */}
            <div className="backdrop-blur-xl bg-obsidian-800/70 border border-yellow-500/20 rounded-xl p-6">
                <div className="flex items-center justify-between mb-6">
                    <h3 className="text-lg font-bold text-yellow-500 flex items-center gap-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        <AlertTriangle className="w-5 h-5" />
                        وضع الصيانة
                    </h3>
                    <button
                        onClick={() => setSettings({ ...settings, maintenance_mode_enabled: !settings.maintenance_mode_enabled })}
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${settings.maintenance_mode_enabled
                            ? 'bg-yellow-500/20 text-yellow-400'
                            : 'bg-gray-500/20 text-gray-400'
                            }`}
                        style={{ fontFamily: 'Cairo, sans-serif' }}
                    >
                        {settings.maintenance_mode_enabled ? <ToggleRight className="w-5 h-5" /> : <ToggleLeft className="w-5 h-5" />}
                        {settings.maintenance_mode_enabled ? 'مفعّل' : 'معطّل'}
                    </button>
                </div>

                {settings.maintenance_mode_enabled && (
                    <div className="p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg mb-4">
                        <p className="text-yellow-400 text-sm" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            ⚠️ تحذير: عند تفعيل وضع الصيانة، لن يتمكن المستخدمون من الوصول للمنصة
                        </p>
                    </div>
                )}

                <div className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-purple-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            رسالة الصيانة
                        </label>
                        <textarea
                            value={settings.maintenance_mode_message || ''}
                            onChange={(e) => setSettings({ ...settings, maintenance_mode_message: e.target.value })}
                            rows={3}
                            placeholder="المنصة تحت الصيانة حالياً. سنعود قريباً!"
                            className="w-full px-4 py-3 bg-obsidian-900/50 border border-purple-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors resize-none"
                            style={{ fontFamily: 'Cairo, sans-serif' }}
                        />
                    </div>
                </div>
            </div>
        </div>
    );
}
