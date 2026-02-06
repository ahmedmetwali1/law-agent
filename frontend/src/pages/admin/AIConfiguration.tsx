import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
    Brain,
    Save,
    RefreshCw,
    Cpu,
    Thermometer,
    Hash,
    Link,
    Key,
    Database,
    Volume2,
    Globe
} from 'lucide-react';
import { getPlatformSettings, updatePlatformSettings, PlatformSettings } from '../../api/admin';
import { toast } from 'sonner';

export default function AIConfiguration() {
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [settings, setSettings] = useState<Partial<PlatformSettings>>({});

    useEffect(() => {
        loadSettings();
    }, []);

    const loadSettings = async () => {
        try {
            setLoading(true);
            const data = await getPlatformSettings();
            setSettings(data);
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
            await updatePlatformSettings(settings);
            toast.success('تم حفظ الإعدادات بنجاح');
        } catch (error) {
            console.error('Error saving settings:', error);
            toast.error('فشل حفظ الإعدادات');
        } finally {
            setSaving(false);
        }
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
                        <Brain className="w-7 h-7" />
                        إعدادات الذكاء الاصطناعي
                    </h1>
                    <p className="text-gray-400 mt-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        تحكم في نموذج الذكاء الاصطناعي وإعدادات التكامل
                    </p>
                </div>
                <div className="flex gap-2">
                    <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={loadSettings}
                        className="flex items-center gap-2 px-4 py-2 bg-obsidian-800 border border-purple-500/30 text-white rounded-lg hover:bg-purple-500/10 transition-all"
                        style={{ fontFamily: 'Cairo, sans-serif' }}
                    >
                        <RefreshCw className="w-4 h-4" />
                        تحديث
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

            {/* AI Model Configuration */}
            <div className="backdrop-blur-xl bg-obsidian-800/70 border border-purple-500/20 rounded-xl p-6">
                <h3 className="text-lg font-bold text-purple-500 mb-6 flex items-center gap-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                    <Cpu className="w-5 h-5" />
                    إعدادات نموذج الذكاء الاصطناعي
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-purple-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            <span className="flex items-center gap-2"><Globe className="w-4 h-4" /> مزود الـ AI</span>
                        </label>
                        <select
                            value={settings.ai_provider || 'openwebui'}
                            onChange={(e) => setSettings({ ...settings, ai_provider: e.target.value })}
                            className="w-full px-4 py-3 bg-obsidian-900/50 border border-purple-500/20 rounded-lg text-white focus:outline-none focus:border-purple-500 transition-colors"
                            style={{ fontFamily: 'Cairo, sans-serif' }}
                        >
                            <option value="openwebui">Open WebUI</option>
                            <option value="openai">OpenAI</option>
                            <option value="anthropic">Anthropic</option>
                            <option value="ollama">Ollama</option>
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-purple-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            <span className="flex items-center gap-2"><Hash className="w-4 h-4" /> اسم النموذج</span>
                        </label>
                        <input
                            type="text"
                            value={settings.ai_model_name || ''}
                            onChange={(e) => setSettings({ ...settings, ai_model_name: e.target.value })}
                            placeholder="gpt-oss-120b"
                            className="w-full px-4 py-3 bg-obsidian-900/50 border border-purple-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-purple-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            <span className="flex items-center gap-2"><Link className="w-4 h-4" /> رابط الـ API</span>
                        </label>
                        <input
                            type="text"
                            value={settings.ai_api_url || ''}
                            onChange={(e) => setSettings({ ...settings, ai_api_url: e.target.value })}
                            placeholder="http://152.67.159.164:3000/api"
                            className="w-full px-4 py-3 bg-obsidian-900/50 border border-purple-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-purple-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            <span className="flex items-center gap-2"><Key className="w-4 h-4" /> مفتاح الـ API</span>
                        </label>
                        <input
                            type="password"
                            value={settings.ai_api_key || ''}
                            onChange={(e) => setSettings({ ...settings, ai_api_key: e.target.value })}
                            placeholder="••••••••••••"
                            className="w-full px-4 py-3 bg-obsidian-900/50 border border-purple-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-purple-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            <span className="flex items-center gap-2"><Thermometer className="w-4 h-4" /> Temperature ({settings.ai_temperature || 0.7})</span>
                        </label>
                        <input
                            type="range"
                            min="0"
                            max="1"
                            step="0.1"
                            value={settings.ai_temperature || 0.7}
                            onChange={(e) => setSettings({ ...settings, ai_temperature: parseFloat(e.target.value) })}
                            className="w-full h-2 bg-obsidian-900 rounded-lg appearance-none cursor-pointer accent-purple-500"
                        />
                        <div className="flex justify-between text-xs text-gray-500 mt-1">
                            <span>دقيق (0)</span>
                            <span>إبداعي (1)</span>
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-purple-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            <span className="flex items-center gap-2"><Hash className="w-4 h-4" /> Max Tokens</span>
                        </label>
                        <input
                            type="number"
                            value={settings.ai_max_tokens || 2000}
                            onChange={(e) => setSettings({ ...settings, ai_max_tokens: parseInt(e.target.value) })}
                            className="w-full px-4 py-3 bg-obsidian-900/50 border border-purple-500/20 rounded-lg text-white focus:outline-none focus:border-purple-500 transition-colors"
                        />
                    </div>
                </div>
            </div>

            {/* Embedding Configuration */}
            <div className="backdrop-blur-xl bg-obsidian-800/70 border border-purple-500/20 rounded-xl p-6">
                <h3 className="text-lg font-bold text-purple-500 mb-6 flex items-center gap-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                    <Database className="w-5 h-5" />
                    إعدادات الـ Embeddings
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-purple-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            مزود الـ Embedding
                        </label>
                        <select
                            value={settings.embedding_provider || 'openwebui'}
                            onChange={(e) => setSettings({ ...settings, embedding_provider: e.target.value })}
                            className="w-full px-4 py-3 bg-obsidian-900/50 border border-purple-500/20 rounded-lg text-white focus:outline-none focus:border-purple-500 transition-colors"
                            style={{ fontFamily: 'Cairo, sans-serif' }}
                        >
                            <option value="openwebui">Open WebUI</option>
                            <option value="openai">OpenAI</option>
                            <option value="local">Local (Ollama)</option>
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-purple-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            اسم نموذج الـ Embedding
                        </label>
                        <input
                            type="text"
                            value={settings.embedding_model_name || 'bge-m3-embeddings'}
                            onChange={(e) => setSettings({ ...settings, embedding_model_name: e.target.value })}
                            className="w-full px-4 py-3 bg-obsidian-900/50 border border-purple-500/20 rounded-lg text-white focus:outline-none focus:border-purple-500 transition-colors"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-purple-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            Embedding Dimensions
                        </label>
                        <input
                            type="number"
                            value={settings.embedding_dimensions || 1536}
                            onChange={(e) => setSettings({ ...settings, embedding_dimensions: parseInt(e.target.value) })}
                            className="w-full px-4 py-3 bg-obsidian-900/50 border border-purple-500/20 rounded-lg text-white focus:outline-none focus:border-purple-500 transition-colors"
                        />
                    </div>
                </div>
            </div>

            {/* Speech-to-Text Configuration */}
            <div className="backdrop-blur-xl bg-obsidian-800/70 border border-purple-500/20 rounded-xl p-6">
                <h3 className="text-lg font-bold text-purple-500 mb-6 flex items-center gap-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                    <Volume2 className="w-5 h-5" />
                    إعدادات تحويل الصوت إلى نص (STT)
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-purple-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            رابط API التحويل
                        </label>
                        <input
                            type="text"
                            value={settings.stt_api_url || ''}
                            onChange={(e) => setSettings({ ...settings, stt_api_url: e.target.value })}
                            placeholder="https://stt.example.com/v1/audio/transcriptions"
                            className="w-full px-4 py-3 bg-obsidian-900/50 border border-purple-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-purple-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            مفتاح API التحويل
                        </label>
                        <input
                            type="password"
                            value={settings.stt_api_key || ''}
                            onChange={(e) => setSettings({ ...settings, stt_api_key: e.target.value })}
                            placeholder="••••••••••••"
                            className="w-full px-4 py-3 bg-obsidian-900/50 border border-purple-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors"
                        />
                    </div>
                </div>
            </div>

            {/* Current Values Display */}
            <div className="backdrop-blur-xl bg-obsidian-800/70 border border-green-500/20 rounded-xl p-6">
                <h3 className="text-lg font-bold text-green-500 mb-4" style={{ fontFamily: 'Cairo, sans-serif' }}>
                    📋 القيم الحالية في النظام
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div className="p-3 bg-obsidian-900/50 rounded-lg">
                        <p className="text-gray-500" style={{ fontFamily: 'Cairo, sans-serif' }}>المزود</p>
                        <p className="text-white font-mono">{settings.ai_provider || 'غير محدد'}</p>
                    </div>
                    <div className="p-3 bg-obsidian-900/50 rounded-lg">
                        <p className="text-gray-500" style={{ fontFamily: 'Cairo, sans-serif' }}>النموذج</p>
                        <p className="text-white font-mono">{settings.ai_model_name || 'غير محدد'}</p>
                    </div>
                    <div className="p-3 bg-obsidian-900/50 rounded-lg">
                        <p className="text-gray-500" style={{ fontFamily: 'Cairo, sans-serif' }}>Temperature</p>
                        <p className="text-white font-mono">{settings.ai_temperature || 0.7}</p>
                    </div>
                    <div className="p-3 bg-obsidian-900/50 rounded-lg">
                        <p className="text-gray-500" style={{ fontFamily: 'Cairo, sans-serif' }}>Max Tokens</p>
                        <p className="text-white font-mono">{settings.ai_max_tokens || 2000}</p>
                    </div>
                </div>
            </div>
        </div>
    );
}
