import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
    Settings,
    Save,
    RefreshCw,
    Building,
    Globe,
    FileText,
    Mail,
    Phone,
    MessageCircle,
    Link as LinkIcon,
    Image,
    Clock
} from 'lucide-react';
import { getPlatformSettings, updatePlatformSettings, PlatformSettings as PlatformSettingsType } from '../../api/admin';
import { toast } from 'sonner';

export default function PlatformSettings() {
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [settings, setSettings] = useState<Partial<PlatformSettingsType>>({});
    const [footerLinks, setFooterLinks] = useState<Array<{ text: string, url: string }>>([]);

    useEffect(() => {
        loadSettings();
    }, []);

    const loadSettings = async () => {
        try {
            setLoading(true);
            const data = await getPlatformSettings();
            setSettings(data);
            // Parse footer links
            if (data.footer_links) {
                try {
                    const links = typeof data.footer_links === 'string'
                        ? JSON.parse(data.footer_links)
                        : data.footer_links;
                    setFooterLinks(links || []);
                } catch {
                    setFooterLinks([]);
                }
            }
        } catch (error) {
            console.error('Error loading settings:', error);
            toast.error('فشل تحميل الإعدادات');
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        try {
            setSaving(true);
            const updatedSettings = {
                ...settings,
                footer_links: footerLinks
            };
            await updatePlatformSettings(updatedSettings);
            toast.success('تم حفظ الإعدادات بنجاح');
        } catch (error) {
            console.error('Error saving settings:', error);
            toast.error('فشل حفظ الإعدادات');
        } finally {
            setSaving(false);
        }
    };

    const addFooterLink = () => {
        setFooterLinks([...footerLinks, { text: '', url: '' }]);
    };

    const updateFooterLink = (index: number, field: 'text' | 'url', value: string) => {
        const updated = [...footerLinks];
        updated[index][field] = value;
        setFooterLinks(updated);
    };

    const removeFooterLink = (index: number) => {
        setFooterLinks(footerLinks.filter((_, i) => i !== index));
    };

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
                        <Settings className="w-7 h-7" />
                        إعدادات المنصة
                    </h1>
                    <p className="text-gray-400 mt-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        إعدادات عامة للمنصة والتخصيص
                    </p>
                </div>
                <div className="flex gap-2">
                    <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={loadSettings}
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
                        {saving ? 'جاري الحفظ...' : 'حفظ التغييرات'}
                    </motion.button>
                </div>
            </div>

            {/* Platform Info */}
            <div className="backdrop-blur-xl bg-obsidian-800/70 border border-purple-500/20 rounded-xl p-6">
                <h3 className="text-lg font-bold text-purple-500 mb-6 flex items-center gap-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                    <Building className="w-5 h-5" />
                    معلومات المنصة
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-purple-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            اسم المنصة (عربي)
                        </label>
                        <input
                            type="text"
                            value={settings.platform_name || ''}
                            onChange={(e) => setSettings({ ...settings, platform_name: e.target.value })}
                            className="w-full px-4 py-3 bg-obsidian-900/50 border border-purple-500/20 rounded-lg text-white focus:outline-none focus:border-purple-500 transition-colors"
                            style={{ fontFamily: 'Cairo, sans-serif' }}
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-purple-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            اسم المنصة (English)
                        </label>
                        <input
                            type="text"
                            value={settings.platform_name_en || ''}
                            onChange={(e) => setSettings({ ...settings, platform_name_en: e.target.value })}
                            className="w-full px-4 py-3 bg-obsidian-900/50 border border-purple-500/20 rounded-lg text-white focus:outline-none focus:border-purple-500 transition-colors"
                        />
                    </div>

                    <div className="md:col-span-2">
                        <label className="block text-sm font-medium text-purple-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            وصف المنصة
                        </label>
                        <textarea
                            value={settings.platform_description || ''}
                            onChange={(e) => setSettings({ ...settings, platform_description: e.target.value })}
                            rows={3}
                            className="w-full px-4 py-3 bg-obsidian-900/50 border border-purple-500/20 rounded-lg text-white focus:outline-none focus:border-purple-500 transition-colors resize-none"
                            style={{ fontFamily: 'Cairo, sans-serif' }}
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-purple-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            <span className="flex items-center gap-2"><Image className="w-4 h-4" /> رابط الشعار</span>
                        </label>
                        <input
                            type="text"
                            value={settings.platform_logo_url || ''}
                            onChange={(e) => setSettings({ ...settings, platform_logo_url: e.target.value })}
                            placeholder="https://..."
                            className="w-full px-4 py-3 bg-obsidian-900/50 border border-purple-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-purple-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            <span className="flex items-center gap-2"><Globe className="w-4 h-4" /> رابط الأيقونة (Favicon)</span>
                        </label>
                        <input
                            type="text"
                            value={settings.platform_favicon_url || ''}
                            onChange={(e) => setSettings({ ...settings, platform_favicon_url: e.target.value })}
                            placeholder="https://..."
                            className="w-full px-4 py-3 bg-obsidian-900/50 border border-purple-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors"
                        />
                    </div>
                </div>
            </div>

            {/* Footer Settings */}
            <div className="backdrop-blur-xl bg-obsidian-800/70 border border-purple-500/20 rounded-xl p-6">
                <h3 className="text-lg font-bold text-purple-500 mb-6 flex items-center gap-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                    <FileText className="w-5 h-5" />
                    إعدادات الفوتر
                </h3>

                <div className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-purple-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            نص حقوق النشر
                        </label>
                        <input
                            type="text"
                            value={settings.footer_copyright_text || ''}
                            onChange={(e) => setSettings({ ...settings, footer_copyright_text: e.target.value })}
                            placeholder="© 2026 جميع الحقوق محفوظة"
                            className="w-full px-4 py-3 bg-obsidian-900/50 border border-purple-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors"
                            style={{ fontFamily: 'Cairo, sans-serif' }}
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-purple-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            Powered By
                        </label>
                        <input
                            type="text"
                            value={settings.footer_powered_by || ''}
                            onChange={(e) => setSettings({ ...settings, footer_powered_by: e.target.value })}
                            className="w-full px-4 py-3 bg-obsidian-900/50 border border-purple-500/20 rounded-lg text-white focus:outline-none focus:border-purple-500 transition-colors"
                        />
                    </div>

                    <div>
                        <div className="flex items-center justify-between mb-2">
                            <label className="text-sm font-medium text-purple-400" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                روابط الفوتر
                            </label>
                            <button
                                onClick={addFooterLink}
                                className="text-purple-400 hover:text-purple-300 text-sm"
                                style={{ fontFamily: 'Cairo, sans-serif' }}
                            >
                                + إضافة رابط
                            </button>
                        </div>
                        <div className="space-y-2">
                            {footerLinks.map((link, index) => (
                                <div key={index} className="flex gap-2">
                                    <input
                                        type="text"
                                        value={link.text}
                                        onChange={(e) => updateFooterLink(index, 'text', e.target.value)}
                                        placeholder="النص"
                                        className="flex-1 px-3 py-2 bg-obsidian-900/50 border border-purple-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors text-sm"
                                        style={{ fontFamily: 'Cairo, sans-serif' }}
                                    />
                                    <input
                                        type="text"
                                        value={link.url}
                                        onChange={(e) => updateFooterLink(index, 'url', e.target.value)}
                                        placeholder="/path أو https://..."
                                        className="flex-1 px-3 py-2 bg-obsidian-900/50 border border-purple-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors text-sm"
                                    />
                                    <button
                                        onClick={() => removeFooterLink(index)}
                                        className="px-3 text-red-400 hover:text-red-300"
                                    >
                                        ✕
                                    </button>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            {/* Contact Info */}
            <div className="backdrop-blur-xl bg-obsidian-800/70 border border-purple-500/20 rounded-xl p-6">
                <h3 className="text-lg font-bold text-purple-500 mb-6 flex items-center gap-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                    <Phone className="w-5 h-5" />
                    معلومات التواصل
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-purple-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            <span className="flex items-center gap-2"><Mail className="w-4 h-4" /> البريد الإلكتروني</span>
                        </label>
                        <input
                            type="email"
                            value={settings.contact_email || ''}
                            onChange={(e) => setSettings({ ...settings, contact_email: e.target.value })}
                            className="w-full px-4 py-3 bg-obsidian-900/50 border border-purple-500/20 rounded-lg text-white focus:outline-none focus:border-purple-500 transition-colors"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-purple-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            <span className="flex items-center gap-2"><Phone className="w-4 h-4" /> الهاتف</span>
                        </label>
                        <input
                            type="tel"
                            value={settings.contact_phone || ''}
                            onChange={(e) => setSettings({ ...settings, contact_phone: e.target.value })}
                            className="w-full px-4 py-3 bg-obsidian-900/50 border border-purple-500/20 rounded-lg text-white focus:outline-none focus:border-purple-500 transition-colors"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-purple-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            <span className="flex items-center gap-2"><MessageCircle className="w-4 h-4" /> واتساب</span>
                        </label>
                        <input
                            type="tel"
                            value={settings.contact_whatsapp || ''}
                            onChange={(e) => setSettings({ ...settings, contact_whatsapp: e.target.value })}
                            className="w-full px-4 py-3 bg-obsidian-900/50 border border-purple-500/20 rounded-lg text-white focus:outline-none focus:border-purple-500 transition-colors"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-purple-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            <span className="flex items-center gap-2"><Clock className="w-4 h-4" /> ساعات الدعم</span>
                        </label>
                        <input
                            type="text"
                            value={settings.support_hours || ''}
                            onChange={(e) => setSettings({ ...settings, support_hours: e.target.value })}
                            placeholder="الأحد - الخميس: 9:00 ص - 5:00 م"
                            className="w-full px-4 py-3 bg-obsidian-900/50 border border-purple-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors"
                            style={{ fontFamily: 'Cairo, sans-serif' }}
                        />
                    </div>
                </div>
            </div>

            {/* Timezone & Language */}
            <div className="backdrop-blur-xl bg-obsidian-800/70 border border-purple-500/20 rounded-xl p-6">
                <h3 className="text-lg font-bold text-purple-500 mb-6 flex items-center gap-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                    <Globe className="w-5 h-5" />
                    اللغة والتوقيت
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-purple-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            المنطقة الزمنية
                        </label>
                        <select
                            value={settings.timezone || 'Asia/Riyadh'}
                            onChange={(e) => setSettings({ ...settings, timezone: e.target.value })}
                            className="w-full px-4 py-3 bg-obsidian-900/50 border border-purple-500/20 rounded-lg text-white focus:outline-none focus:border-purple-500 transition-colors"
                        >
                            <option value="Asia/Riyadh">الرياض (GMT+3)</option>
                            <option value="Asia/Dubai">دبي (GMT+4)</option>
                            <option value="Africa/Cairo">القاهرة (GMT+2)</option>
                            <option value="Asia/Kuwait">الكويت (GMT+3)</option>
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-purple-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            اللغة الافتراضية
                        </label>
                        <select
                            value={settings.default_language || 'ar'}
                            onChange={(e) => setSettings({ ...settings, default_language: e.target.value })}
                            className="w-full px-4 py-3 bg-obsidian-900/50 border border-purple-500/20 rounded-lg text-white focus:outline-none focus:border-purple-500 transition-colors"
                            style={{ fontFamily: 'Cairo, sans-serif' }}
                        >
                            <option value="ar">العربية</option>
                            <option value="en">English</option>
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-purple-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            العملة
                        </label>
                        <select
                            value={settings.currency || 'SAR'}
                            onChange={(e) => setSettings({ ...settings, currency: e.target.value })}
                            className="w-full px-4 py-3 bg-obsidian-900/50 border border-purple-500/20 rounded-lg text-white focus:outline-none focus:border-purple-500 transition-colors"
                        >
                            <option value="SAR">ريال سعودي (SAR)</option>
                            <option value="AED">درهم إماراتي (AED)</option>
                            <option value="EGP">جنيه مصري (EGP)</option>
                            <option value="USD">دولار أمريكي (USD)</option>
                        </select>
                    </div>
                </div>
            </div>
        </div>
    );
}
