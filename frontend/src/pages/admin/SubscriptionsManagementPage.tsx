import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Search,
    Filter,
    CheckCircle,
    XCircle,
    AlertTriangle,
    CreditCard,
    Clock,
    Calendar,
    ArrowUpCircle,
    Download,
    Globe,
    DollarSign,
    Users,
    Database,
    MessageSquare,
    Save,
    Plus,
    Trash2,
    Settings,
    Edit3,
    Flag,
    Package
} from 'lucide-react';
import { toast } from 'sonner';
import { apiClient } from '../../api/client';

interface Subscription {
    id: string;
    lawyer_id: string;
    lawyer_name: string;
    package_name: string;
    status: 'active' | 'expired' | 'trial' | 'renewal_requested' | 'none';
    start_date: string;
    end_date: string;
    auto_renew: boolean;
    amount_paid?: number;
    payment_method?: string;
    requested_assistants?: number;
    requested_storage?: number;
    requested_ai_words?: number;
    // New Metrics
    words_used?: number;
    storage_used?: number;
    assistants_count?: number;
    max_words?: number;
    max_storage?: number;
    max_assistants?: number;
    is_flagged?: boolean;
    last_login?: string;
    updated_at?: string;
}

interface Country {
    id: string;
    code: string;
    name_ar: string;
    currency: string;
    currency_symbol: string;
    is_default: boolean;
}

interface CountryPricing {
    id?: string;
    country_id: string;
    base_platform_fee: number;
    price_per_assistant: number;
    price_per_gb_monthly: number; // Changed from MB to GB
    price_per_1000_words: number;
    yearly_discount_percent: number;
    free_storage_gb: number; // Added
    free_words_monthly: number; // Added
}

interface DefaultPackage {
    id: string;
    max_assistants: number;
    storage_mb: number; // Changed from storage_gb to storage_mb
    ai_words_monthly: number;
    is_active: boolean;
}

export default function SubscriptionsManagementPage() {
    const [activeTab, setActiveTab] = useState<'requests' | 'pricing' | 'default_package'>('requests');
    const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
    const [countries, setCountries] = useState<Country[]>([]);
    const [countryPricing, setCountryPricing] = useState<CountryPricing[]>([]);
    const [globalPricing, setGlobalPricing] = useState<any>(null);
    const [defaultPackage, setDefaultPackage] = useState<DefaultPackage | null>(null); // Updated type
    const [isSavingPackage, setIsSavingPackage] = useState(false);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [statusFilter, setStatusFilter] = useState<string>('all');

    // Actions State
    const [selectedSub, setSelectedSub] = useState<Subscription | null>(null);
    const [isActionModalOpen, setIsActionModalOpen] = useState(false);
    const [isEditResourcesModalOpen, setIsEditResourcesModalOpen] = useState(false);
    const [actionType, setActionType] = useState<'activate' | 'extend'>('activate');

    // Resource Override Form State
    const [editForm, setEditForm] = useState({
        extra_assistants: 0,
        extra_storage_mb: 0,
        extra_words: 0,
        status: '',
        end_date: ''
    });

    useEffect(() => {
        loadAllData();
    }, []);

    const loadAllData = async () => {
        try {
            setLoading(true);
            const [subsRes, countriesRes, pricingRes, globalRes, packageRes] = await Promise.all([
                apiClient.get('/api/admin/subscriptions'),
                apiClient.get('/api/countries'), // Corrected: Public endpoint is better
                apiClient.get('/api/admin/pricing/country'), // Now exists
                apiClient.get('/api/admin/pricing/global'), // Now exists
                apiClient.get('/api/admin/default-package')
            ]);

            if (subsRes) setSubscriptions(subsRes); // apiClient.get returns data directly
            if (countriesRes) setCountries(countriesRes);
            if (pricingRes) setCountryPricing(pricingRes);
            if (globalRes) setGlobalPricing(globalRes);
            if (packageRes) setDefaultPackage(packageRes);
        } catch (error) {
            console.error('Error loading admin data:', error);
            toast.error('فشل تحميل البيانات من السيرفر');
        } finally {
            setLoading(false);
        }
    };

    const handleAction = async () => {
        if (!selectedSub) return;
        try {
            let endpoint = '';
            let payload = {};

            if (actionType === 'activate') {
                endpoint = `/api/admin/subscriptions/${selectedSub.id}/activate`;
                payload = { duration_months: 1 };
            } else if (actionType === 'extend') {
                endpoint = `/api/admin/subscriptions/${selectedSub.id}/extend`;
                payload = { days: 30 };
            }

            if (endpoint) {
                await apiClient.post(endpoint, payload);
                toast.success('تم تنفيذ العملية بنجاح');
                setIsActionModalOpen(false);
                loadAllData();
            }
        } catch (error) {
            toast.error('حدث خطأ أثناء تنفيذ العملية');
        }
    };

    const handleUpdateCountryPricing = async (data: CountryPricing) => {
        try {
            await apiClient.patch(`/api/admin/pricing/country/${data.id}`, data);
            toast.success('تم تحديث التسعير بنجاح');
            loadAllData();
        } catch (error) {
            toast.error('فشل تحديث التسعير');
        }
    };

    const handleUpdateGlobalPricing = async (data: any) => {
        try {
            await apiClient.patch(`/api/admin/pricing/global/${data.id}`, data);
            toast.success('تم تحديث التسعير العالمي بنجاح');
            loadAllData();
        } catch (error) {
            toast.error('فشل تحديث التسعير العالمي');
        }
    };

    const handleUpdateStarterPackage = async () => {
        if (!defaultPackage) return;
        try {
            setIsSavingPackage(true);
            await apiClient.patch(`/api/admin/default-package`, defaultPackage);
            toast.success('تم تحديث حدود الباقة الافتراضية بنجاح');
            loadAllData();
        } catch (error) {
            toast.error('فشل تحديث الباقة');
        } finally {
            setIsSavingPackage(false);
        }
    };

    useEffect(() => {
        if (selectedSub && isEditResourcesModalOpen) {
            setEditForm({
                extra_assistants: selectedSub.requested_assistants || 0,
                extra_storage_mb: selectedSub.requested_storage || 0,
                extra_words: selectedSub.requested_ai_words || 0,
                status: selectedSub.status,
                end_date: selectedSub.end_date
            });
        }
    }, [selectedSub, isEditResourcesModalOpen]);

    const handleUpdateResources = async () => {
        if (!selectedSub) return;
        try {
            await apiClient.patch(`/api/admin/subscriptions/${selectedSub.id}/resources`, editForm);
            toast.success('تم تحديث الموارد بنجاح');
            setIsEditResourcesModalOpen(false);
            loadAllData();
        } catch (error) {
            toast.error('فشل تحديث الموارد');
        }
    };

    const handleResetUsage = async (subId: string) => {
        try {
            await apiClient.post(`/api/admin/subscriptions/${subId}/reset-usage`);
            toast.success('تم تصفير عداد الكلمات لهذا الشهر');
            loadAllData();
        } catch (error) {
            toast.error('فشل تصفير العداد');
        }
    };

    const getStatusBadge = (status: string) => {
        switch (status) {
            case 'active':
                return <span className="px-2 py-1 rounded-full text-[10px] bg-green-500/10 text-green-500 border border-green-500/20 flex items-center gap-1 font-bold whitespace-nowrap"><CheckCircle className="w-3 h-3" /> خطة مفعلة</span>;
            case 'trial':
                return <span className="px-2 py-1 rounded-full text-[10px] bg-blue-500/10 text-blue-500 border border-blue-500/20 flex items-center gap-1 font-bold whitespace-nowrap"><Clock className="w-3 h-3" /> فترة تجريبية</span>;
            case 'renewal_requested':
                return <span className="px-2 py-1 rounded-full text-[10px] bg-yellow-500/10 text-yellow-100 border border-yellow-500/50 flex items-center gap-1 font-bold animate-pulse whitespace-nowrap"><AlertTriangle className="w-3 h-3" /> طلب ترقية</span>;
            case 'expired':
                return <span className="px-2 py-1 rounded-full text-[10px] bg-red-500/10 text-red-500 border border-red-500/20 flex items-center gap-1 font-bold whitespace-nowrap"><XCircle className="w-3 h-3" /> منتهي</span>;
            case 'none':
                return <span className="px-2 py-1 rounded-full text-[10px] bg-gray-500/10 text-gray-400 border border-gray-500/20 flex items-center gap-1 font-bold whitespace-nowrap"><AlertTriangle className="w-3 h-3" /> بدون باقة</span>;
            default:
                return status;
        }
    };

    const getUsageColor = (percent: number) => {
        if (percent >= 90) return 'bg-red-500';
        if (percent >= 70) return 'bg-yellow-500';
        return 'bg-blue-500';
    };

    const UsageBar = ({ current, total, label, unit = "" }: { current: number, total: number, label: string, unit?: string }) => {
        const percent = total > 0 ? Math.min(100, (current / total) * 100) : 0;
        return (
            <div className="flex flex-col gap-1 min-w-[120px]">
                <div className="flex justify-between text-[10px] font-bold">
                    <span className="text-gray-400">{label}</span>
                    <span className={percent >= 90 ? 'text-red-400' : 'text-gray-300'}>
                        {current.toLocaleString()}{unit} / {total.toLocaleString()}{unit}
                    </span>
                </div>
                <div className="h-1.5 w-full bg-obsidian-900 rounded-full overflow-hidden border border-white/5">
                    <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${percent}%` }}
                        className={`h-full ${getUsageColor(percent)} rounded-full shadow-[0_0_8px] ${percent >= 90 ? 'shadow-red-500/50' : 'shadow-blue-500/20'}`}
                    />
                </div>
            </div>
        );
    };

    const filteredSubs = subscriptions.filter(sub => {
        const matchesSearch = sub.lawyer_name?.toLowerCase().includes(searchQuery.toLowerCase());
        const matchesStatus = statusFilter === 'all' || sub.status === statusFilter;
        return matchesSearch && matchesStatus;
    });

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-white mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        مركز إدارة الاشتراكات والتسعير
                    </h1>
                    <p className="text-gray-400">تحكم كامل في طلبات المحامين وقواعد التسعير الدولية</p>
                </div>

                <div className="flex bg-obsidian-800 p-1 rounded-xl border border-gold-500/10 self-start">
                    <button
                        onClick={() => setActiveTab('requests')}
                        className={`px-6 py-2 rounded-lg text-sm font-bold transition-all flex items-center gap-2 ${activeTab === 'requests' ? 'bg-gold-500 text-black shadow-lg shadow-gold-500/20' : 'text-gray-400 hover:text-white'}`}
                        style={{ fontFamily: 'Cairo, sans-serif' }}
                    >
                        <CreditCard className="w-4 h-4" />
                        طلبات التفعيل ({subscriptions.filter(s => s.status === 'renewal_requested').length})
                    </button>
                    <button
                        onClick={() => setActiveTab('pricing')}
                        className={`px-6 py-2 rounded-lg text-sm font-bold transition-all flex items-center gap-2 ${activeTab === 'pricing' ? 'bg-gold-500 text-black shadow-lg shadow-gold-500/20' : 'text-gray-400 hover:text-white'}`}
                        style={{ fontFamily: 'Cairo, sans-serif' }}
                    >
                        <Globe className="w-4 h-4" />
                        هيكل التسعير
                    </button>
                    <button
                        onClick={() => setActiveTab('default_package')}
                        className={`px-6 py-2 rounded-lg text-sm font-bold transition-all flex items-center gap-2 ${activeTab === 'default_package' ? 'bg-gold-500 text-black shadow-lg shadow-gold-500/20' : 'text-gray-400 hover:text-white'}`}
                        style={{ fontFamily: 'Cairo, sans-serif' }}
                    >
                        <Package className="w-4 h-4" />
                        الباقة الافتراضية
                    </button>
                </div>
            </div>

            <AnimatePresence mode="wait">
                {activeTab === 'requests' && (
                    <motion.div
                        key="requests"
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: 20 }}
                        className="space-y-6"
                    >
                        {/* Filters */}
                        <div className="glass-card p-4 flex flex-wrap gap-4 items-center justify-between">
                            <div className="relative flex-1 min-w-[300px]">
                                <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                                <input
                                    type="text"
                                    placeholder="بحث باسم المحامي..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    className="w-full bg-obsidian-900 border border-gold-500/10 rounded-lg pr-10 pl-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-gold-500/30"
                                />
                            </div>

                            <div className="flex gap-2">
                                {['all', 'renewal_requested', 'active', 'trial', 'expired', 'none'].map((status) => (
                                    <button
                                        key={status}
                                        onClick={() => setStatusFilter(status)}
                                        className={`px-4 py-2 rounded-lg text-sm font-bold transition-all ${statusFilter === status
                                            ? 'bg-purple-600 text-white shadow-lg shadow-purple-600/20'
                                            : 'bg-obsidian-800 text-gray-400 hover:text-white'
                                            }`}
                                        style={{ fontFamily: 'Cairo, sans-serif' }}
                                    >
                                        {status === 'all' ? 'الكل' :
                                            status === 'renewal_requested' ? 'طلبات التجديد' :
                                                status === 'active' ? 'باقات مدفوعة' :
                                                    status === 'trial' ? 'الباقة المجانية' :
                                                        status === 'none' ? 'بدون باقة' : 'منتهي'}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Subscriptions Table */}
                        <div className="glass-card overflow-hidden">
                            <table className="w-full text-right">
                                <thead>
                                    <tr className="border-b border-gold-500/10 bg-obsidian-900/50">
                                        <th className="px-6 py-4 text-sm font-bold text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>المحامي</th>
                                        <th className="px-6 py-4 text-sm font-bold text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>ما تم طلبه (الموارد)</th>
                                        <th className="px-6 py-4 text-sm font-bold text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>تاريخ الانتهاء</th>
                                        <th className="px-6 py-4 text-sm font-bold text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>الحالة</th>
                                        <th className="px-6 py-4 text-sm font-bold text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>إجراءات</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gold-500/5">
                                    {loading ? (
                                        <tr><td colSpan={5} className="px-6 py-12 text-center text-gray-500">جاري التحميل...</td></tr>
                                    ) : filteredSubs.length === 0 ? (
                                        <tr><td colSpan={5} className="px-6 py-12 text-center text-gray-500">لا توجد اشتراكات</td></tr>
                                    ) : (
                                        filteredSubs.map((sub) => (
                                            <tr key={sub.id} className={`hover:bg-gold-500/5 transition-colors group border-b border-gold-500/5 ${sub.is_flagged ? 'bg-red-500/5' : ''}`}>
                                                <td className="px-6 py-4">
                                                    <div className="flex items-center gap-3">
                                                        <div className={`relative w-10 h-10 rounded-xl flex items-center justify-center font-bold border ${sub.is_flagged ? 'bg-red-500/20 text-red-400 border-red-500/30' : 'bg-purple-500/10 text-purple-400 border-purple-500/20'}`}>
                                                            {sub.lawyer_name?.charAt(0)}
                                                            {sub.is_flagged && (
                                                                <div className="absolute -top-1 -right-1 bg-red-500 text-white p-0.5 rounded-full animate-bounce shadow-lg shadow-red-500/50">
                                                                    <AlertTriangle className="w-3 h-3" />
                                                                </div>
                                                            )}
                                                        </div>
                                                        <div className="flex flex-col">
                                                            <div className="flex items-center gap-2">
                                                                <span className="text-white font-bold">{sub.lawyer_name}</span>
                                                                {sub.is_flagged && <span className="text-[10px] bg-red-500 text-white px-1.5 py-0.5 rounded-md font-bold">مشبوه</span>}
                                                            </div>
                                                            <span className="text-xs text-gray-500 flex items-center gap-1">
                                                                <Clock className="w-3 h-3" />
                                                                آخر دخول: {sub.last_login ? new Date(sub.last_login).toLocaleDateString('ar-EG') : 'غير متوفر'}
                                                            </span>
                                                        </div>
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4">
                                                    <div className="flex flex-col gap-3">
                                                        <UsageBar
                                                            label="المساحة"
                                                            current={sub.storage_used || 0}
                                                            total={sub.max_storage || 0}
                                                            unit="MB"
                                                        />
                                                        <UsageBar
                                                            label="الذكاء الاصطناعي"
                                                            current={sub.words_used || 0}
                                                            total={sub.max_words || 0}
                                                            unit=" كلمة"
                                                        />
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4">
                                                    <div className="flex flex-col">
                                                        <span className="text-gray-300 font-mono text-xs" dir="ltr">{sub.end_date}</span>
                                                        <span className="text-[10px] text-gray-500">تم التحديث: {sub.updated_at ? new Date(sub.updated_at).toLocaleDateString('ar-EG') : '-'}</span>
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4">{getStatusBadge(sub.status)}</td>
                                                <td className="px-6 py-4">
                                                    <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                                        {sub.status === 'renewal_requested' && (
                                                            <button
                                                                onClick={() => { setSelectedSub(sub); setActionType('activate'); setIsActionModalOpen(true); }}
                                                                className="px-4 py-2 bg-green-500 text-black font-bold rounded-lg text-xs hover:bg-green-400 transition shadow-lg shadow-green-500/20"
                                                            >
                                                                موافقة
                                                            </button>
                                                        )}
                                                        {sub.status === 'none' && (
                                                            <button
                                                                onClick={async () => {
                                                                    try {
                                                                        await apiClient.post(`/api/admin/lawyers/${sub.lawyer_id}/activate-trial`);
                                                                        toast.success('تم تفعيل الباقة التجريبية');
                                                                        loadAllData();
                                                                    } catch (e) { toast.error('فشل التفعيل'); }
                                                                }}
                                                                className="px-4 py-2 bg-gold-500 text-black font-bold rounded-lg text-xs hover:bg-gold-400 transition"
                                                            >
                                                                تفعيل تجريبي
                                                            </button>
                                                        )}
                                                        <button
                                                            onClick={() => { setSelectedSub(sub); setActionType('extend'); setIsActionModalOpen(true); }}
                                                            className="p-2 bg-obsidian-700 text-gray-400 hover:text-white rounded-lg transition border border-white/5"
                                                            title="تمديد الاشتراك"
                                                        >
                                                            <Calendar className="w-4 h-4" />
                                                        </button>
                                                        <button
                                                            onClick={() => { setSelectedSub(sub); setIsEditResourcesModalOpen(true); }}
                                                            className="p-2 bg-obsidian-700 text-gray-400 hover:text-gold-500 rounded-lg transition border border-white/5"
                                                            title="تعديل يدوي للموارد"
                                                        >
                                                            <Edit3 className="w-4 h-4" />
                                                        </button>
                                                    </div>
                                                </td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </motion.div>
                )}

                {activeTab === 'pricing' && (
                    <motion.div
                        key="pricing"
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -20 }}
                        className="space-y-8"
                    >
                        {/* Global Pricing Summary */}
                        {globalPricing && (
                            <div className="glass-card p-6 border-gold-500/30 bg-gold-500/5 relative overflow-hidden group">
                                <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                                    <Globe className="w-20 h-20 text-gold-500" />
                                </div>
                                <div className="relative z-10">
                                    <div className="flex items-center gap-3 mb-6">
                                        <div className="p-2 bg-gold-500/20 rounded-lg">
                                            <DollarSign className="w-5 h-5 text-gold-500" />
                                        </div>
                                        <h3 className="text-xl font-bold text-white" style={{ fontFamily: 'Cairo, sans-serif' }}>التسعير العالمي الافتراضي</h3>
                                    </div>

                                    <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
                                        <div className="space-y-1">
                                            <span className="text-[10px] text-gray-500 font-bold uppercase block">رسوم المنصة</span>
                                            <input
                                                type="number"
                                                value={globalPricing.base_platform_fee}
                                                onChange={(e) => setGlobalPricing({ ...globalPricing, base_platform_fee: parseFloat(e.target.value) })}
                                                className="w-full bg-obsidian-900 border border-gold-500/10 rounded px-2 py-1 text-sm text-white outline-none focus:border-gold-500/50"
                                            />
                                        </div>
                                        <div className="space-y-1">
                                            <span className="text-[10px] text-gray-500 font-bold uppercase block">لكل مساعد</span>
                                            <input
                                                type="number"
                                                value={globalPricing.price_per_assistant}
                                                onChange={(e) => setGlobalPricing({ ...globalPricing, price_per_assistant: parseFloat(e.target.value) })}
                                                className="w-full bg-obsidian-900 border border-gold-500/10 rounded px-2 py-1 text-sm text-white outline-none focus:border-gold-500/50"
                                            />
                                        </div>
                                        <div className="space-y-1">
                                            <span className="text-[10px] text-gray-500 font-bold uppercase block">لكل جيجا (GB)</span>
                                            <input
                                                type="number"
                                                step="0.01"
                                                value={globalPricing.price_per_gb_monthly}
                                                onChange={(e) => setGlobalPricing({ ...globalPricing, price_per_gb_monthly: parseFloat(e.target.value) })}
                                                className="w-full bg-obsidian-900 border border-gold-500/10 rounded px-2 py-1 text-sm text-white outline-none focus:border-gold-500/50"
                                            />
                                        </div>
                                        <div className="space-y-1">
                                            <span className="text-[10px] text-gray-500 font-bold uppercase block">لكل 1000 كلمة</span>
                                            <input
                                                type="number"
                                                value={globalPricing.price_per_1000_words}
                                                onChange={(e) => setGlobalPricing({ ...globalPricing, price_per_1000_words: parseFloat(e.target.value) })}
                                                className="w-full bg-obsidian-900 border border-gold-500/10 rounded px-2 py-1 text-sm text-white outline-none focus:border-gold-500/50"
                                            />
                                        </div>
                                        <div className="space-y-1">
                                            <span className="text-[10px] text-gray-500 font-bold uppercase block">مساحة مجانية (GB)</span>
                                            <input
                                                type="number"
                                                value={globalPricing.free_storage_gb}
                                                onChange={(e) => setGlobalPricing({ ...globalPricing, free_storage_gb: parseFloat(e.target.value) })}
                                                className="w-full bg-obsidian-900 border border-gold-500/10 rounded px-2 py-1 text-sm text-white outline-none focus:border-gold-500/50"
                                            />
                                        </div>
                                        <div className="flex items-end">
                                            <button
                                                onClick={() => handleUpdateGlobalPricing(globalPricing)}
                                                className="w-full bg-gold-500 hover:bg-gold-400 text-black font-bold py-1 rounded text-xs transition-all shadow-lg shadow-gold-500/20"
                                            >
                                                تحديث افتراضي
                                            </button>
                                        </div>
                                    </div>
                                    <p className="mt-4 text-[10px] text-gray-500 italic">
                                        * هذه القيم تُستخدم كنقاط انطلاق للدول التي ليس لها تسعير مخصص.
                                    </p>
                                </div>
                            </div>
                        )}

                        {/* Country Specific Table */}
                        <div className="flex items-center justify-between mb-2">
                            <h2 className="text-xl font-bold text-white flex items-center gap-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                <Globe className="w-6 h-6 text-purple-400" />
                                تسعير الخدمات حسب الدولة
                            </h2>
                            <p className="text-sm text-gray-500">يتم تطبيق هذه الأسعار بناءً على دولة اشتراك المحامي</p>
                        </div>

                        <div className="glass-card overflow-hidden">
                            <table className="w-full text-right">
                                <thead>
                                    <tr className="border-b border-gold-500/10 bg-obsidian-900/50">
                                        <th className="px-6 py-4 text-sm font-bold text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>الدولة</th>
                                        <th className="px-6 py-4 text-sm font-bold text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>رسوم المنصة</th>
                                        <th className="px-6 py-4 text-sm font-bold text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>سعر المساعد</th>
                                        <th className="px-6 py-4 text-sm font-bold text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>سعر الميجا</th>
                                        <th className="px-6 py-4 text-sm font-bold text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>سعر 1000 كلمة</th>
                                        <th className="px-6 py-4 text-sm font-bold text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>خصم السنوي</th>
                                        <th className="px-6 py-4 text-sm font-bold text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>حفظ</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gold-500/5">
                                    {countries.map(country => {
                                        const pricing = countryPricing.find(p => p.country_id === country.id) || {
                                            country_id: country.id,
                                            base_platform_fee: globalPricing?.base_platform_fee || 0,
                                            price_per_assistant: globalPricing?.price_per_assistant || 0,
                                            price_per_gb_monthly: globalPricing?.price_per_gb_monthly || 0,
                                            price_per_1000_words: globalPricing?.price_per_1000_words || 0,
                                            yearly_discount_percent: globalPricing?.yearly_discount_percent || 0,
                                            free_storage_gb: globalPricing?.free_storage_gb || 0,
                                            free_words_monthly: globalPricing?.free_words_monthly || 0
                                        };

                                        return (
                                            <CountryPricingRow
                                                key={country.id}
                                                country={country}
                                                initialPricing={pricing}
                                                onSave={handleUpdateCountryPricing}
                                            />
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    </motion.div>
                )}

                {activeTab === 'default_package' && defaultPackage && (
                    <motion.div
                        key="default_package"
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="glass-card p-8 max-w-2xl mx-auto border-gold-500/20"
                    >
                        <div className="flex items-center gap-4 mb-8">
                            <div className="w-16 h-16 rounded-2xl bg-gold-500/10 flex items-center justify-center border border-gold-500/30">
                                <Settings className="w-8 h-8 text-gold-500" />
                            </div>
                            <div>
                                <h2 className="text-2xl font-bold text-white" style={{ fontFamily: 'Cairo, sans-serif' }}>تحكم بحدود الباقة الافتراضية</h2>
                                <p className="text-gray-400">تعديل الموارد الافتراضية الممنوحة للمحامين الجدد (Trial)</p>
                            </div>
                        </div>

                        <div className="space-y-6">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div className="space-y-2">
                                    <label className="text-sm font-bold text-gray-400 block" style={{ fontFamily: 'Cairo, sans-serif' }}>عدد المساعدين</label>
                                    <div className="relative">
                                        <Users className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-purple-400" />
                                        <input
                                            type="number"
                                            value={defaultPackage.max_assistants}
                                            onChange={(e) => setDefaultPackage({ ...defaultPackage, max_assistants: parseInt(e.target.value) || 0 })}
                                            className="w-full bg-obsidian-900 border border-gold-500/10 rounded-xl pl-4 pr-10 py-3 text-white focus:border-gold-500/50 outline-none"
                                        />
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <label className="text-sm font-bold text-gray-400 block" style={{ fontFamily: 'Cairo, sans-serif' }}>مساحة التخزين (MB)</label>
                                    <div className="relative">
                                        <Database className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-blue-400" />
                                        <input
                                            type="number"
                                            value={defaultPackage.storage_mb}
                                            onChange={(e) => setDefaultPackage({ ...defaultPackage, storage_mb: parseInt(e.target.value) || 0 })}
                                            className="w-full bg-obsidian-900 border border-gold-500/10 rounded-xl pl-4 pr-10 py-3 text-white focus:border-gold-500/50 outline-none"
                                        />
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <label className="text-sm font-bold text-gray-400 block" style={{ fontFamily: 'Cairo, sans-serif' }}>كلمات الذكاء الاصطناعي شهرية</label>
                                    <div className="relative">
                                        <MessageSquare className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gold-400" />
                                        <input
                                            type="number"
                                            value={defaultPackage.ai_words_monthly}
                                            onChange={(e) => setDefaultPackage({ ...defaultPackage, ai_words_monthly: parseInt(e.target.value) || 0 })}
                                            className="w-full bg-obsidian-900 border border-gold-500/10 rounded-xl pl-4 pr-10 py-3 text-white focus:border-gold-500/50 outline-none"
                                        />
                                    </div>
                                </div>
                            </div>

                            <div className="pt-6 border-t border-gold-500/10">
                                <button
                                    onClick={handleUpdateStarterPackage}
                                    disabled={isSavingPackage}
                                    className="w-full bg-gradient-to-r from-gold-600 to-gold-500 hover:from-gold-500 hover:to-gold-400 disabled:from-gray-700 disabled:to-gray-800 text-black font-bold py-4 rounded-xl shadow-lg shadow-gold-500/20 transition-all flex items-center justify-center gap-3"
                                    style={{ fontFamily: 'Cairo, sans-serif' }}
                                >
                                    {isSavingPackage ? (
                                        <span className="animate-spin rounded-full h-5 w-5 border-b-2 border-black"></span>
                                    ) : (
                                        <Save className="w-5 h-5" />
                                    )}
                                    حفظ إعدادات الباقة الافتراضية
                                </button>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Existing Activation Modal */}
            {isActionModalOpen && selectedSub && (
                <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="bg-obsidian-800 border border-gold-500/20 rounded-2xl w-full max-w-md overflow-hidden shadow-2xl"
                    >
                        <div className="p-8">
                            <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                {actionType === 'activate' ? <CheckCircle className="text-green-500" /> : <Calendar className="text-blue-500" />}
                                {actionType === 'activate' ? 'تفعيل اشتراك المحامي' : 'تمديد الاشتراك'}
                            </h2>

                            <div className="space-y-6">
                                <p className="text-gray-300 leading-relaxed">
                                    هل أنت متأكد من {actionType === 'activate' ? 'تفعيل' : 'تطبيق تمديد'} اشتراك المحامي:
                                    <span className="text-gold-400 font-bold block mt-1 text-lg">{selectedSub.lawyer_name}</span>
                                </p>

                                {actionType === 'activate' && (
                                    <div className="bg-green-500/10 border border-green-500/20 rounded-xl p-4 space-y-4">
                                        <p className="text-xs text-green-400 font-bold uppercase tracking-wider">تفاصيل التفعيل المخصص</p>
                                        <div className="grid grid-cols-3 gap-3 text-center">
                                            <div className="bg-obsidian-900 p-2 rounded-lg border border-green-500/20">
                                                <span className="block text-[10px] text-gray-500 mb-1">المساعدين</span>
                                                <span className="text-white font-bold text-sm">{selectedSub.requested_assistants || 0}</span>
                                            </div>
                                            <div className="bg-obsidian-900 p-2 rounded-lg border border-green-500/20">
                                                <span className="block text-[10px] text-gray-500 mb-1">التخزين</span>
                                                <span className="text-white font-bold text-sm">{(selectedSub.requested_storage || 0).toLocaleString()}MB</span>
                                            </div>
                                            <div className="bg-obsidian-900 p-2 rounded-lg border border-green-500/20">
                                                <span className="block text-[10px] text-gray-500 mb-1">الكلمات</span>
                                                <span className="text-white font-bold text-sm">{((selectedSub.requested_ai_words || 0) / 1000).toLocaleString()}k</span>
                                            </div>
                                        </div>
                                        <p className="text-[10px] text-green-500/70 italic text-center">
                                            * سيتم ضبط تاريخ الانتهاء ليكون 30 يوماً من الآن وتصفير عداد الكلمات.
                                        </p>
                                    </div>
                                )}
                            </div>

                            <div className="flex gap-3 mt-8">
                                <button
                                    onClick={handleAction}
                                    className="flex-1 bg-gradient-to-r from-gold-600 to-gold-500 hover:from-gold-500 hover:to-gold-400 text-black font-bold py-3 rounded-xl transition-all shadow-lg shadow-gold-500/20"
                                >
                                    تأكيد المتابعة
                                </button>
                                <button
                                    onClick={() => setIsActionModalOpen(false)}
                                    className="flex-1 bg-obsidian-700 hover:bg-obsidian-600 text-white font-bold py-3 rounded-xl transition-all"
                                >
                                    إلغاء
                                </button>
                            </div>
                        </div>
                    </motion.div>
                </div>
            )}
            {/* Manual Resource Edit Modal (Redesigned Control Panel) */}
            {isEditResourcesModalOpen && selectedSub && (
                <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="bg-obsidian-800 border border-gold-500/20 rounded-2xl w-full max-w-4xl overflow-hidden shadow-2xl flex flex-col md:flex-row h-[80vh] md:h-auto"
                    >
                        {/* Left Side: Summary & Details */}
                        <div className="md:w-1/3 bg-obsidian-900/50 border-l border-gold-500/10 p-8 flex flex-col gap-6 relative overflow-hidden">
                            <div className="absolute top-0 right-0 p-4 opacity-5">
                                <Package className="w-64 h-64 text-gold-500" />
                            </div>

                            <div className="relative z-10">
                                <h3 className="text-gray-400 text-xs font-bold uppercase tracking-wider mb-2">ملف المحامي</h3>
                                <div className="flex items-center gap-3 mb-1">
                                    <div className={`w-12 h-12 rounded-xl flex items-center justify-center font-bold text-xl border ${selectedSub.is_flagged ? 'bg-red-500/10 text-red-500 border-red-500/30' : 'bg-gold-500/10 text-gold-500 border-gold-500/30'}`}>
                                        {selectedSub.lawyer_name?.charAt(0)}
                                    </div>
                                    <div>
                                        <h2 className="text-xl font-bold text-white leading-tight">{selectedSub.lawyer_name}</h2>
                                        <span className="text-xs text-gray-500">ID: {selectedSub.lawyer_id.substring(0, 8)}...</span>
                                    </div>
                                </div>
                                {getStatusBadge(selectedSub.status)}
                            </div>

                            <div className="space-y-4 relative z-10">
                                <div className="bg-black/20 rounded-xl p-4 border border-white/5">
                                    <h4 className="text-xs text-gold-500 font-bold uppercase mb-3 flex items-center gap-2">
                                        <Package className="w-3 h-3" /> تفاصيل الباقة الأساسية
                                    </h4>
                                    <div className="space-y-2">
                                        <div className="flex justify-between text-sm">
                                            <span className="text-gray-400">الباقة الحالية</span>
                                            <span className="text-white font-bold">{selectedSub.package_name}</span>
                                        </div>
                                        <div className="flex justify-between text-sm">
                                            <span className="text-gray-400">تاريخ البدء</span>
                                            <span className="text-gray-300 font-mono text-xs">{selectedSub.start_date || '-'}</span>
                                        </div>
                                        <div className="flex justify-between text-sm">
                                            <span className="text-gray-400">تاريخ الانتهاء</span>
                                            <span className="text-gray-300 font-mono text-xs">{selectedSub.end_date || '-'}</span>
                                        </div>
                                    </div>
                                </div>

                                <div className="bg-blue-500/5 rounded-xl p-4 border border-blue-500/10">
                                    <h4 className="text-xs text-blue-400 font-bold uppercase mb-3 flex items-center gap-2">
                                        <Clock className="w-3 h-3" /> الاستهلاك الحالي
                                    </h4>
                                    <div className="space-y-3">
                                        <div>
                                            <div className="flex justify-between text-[10px] mb-1">
                                                <span className="text-gray-400">الذكاء الاصطناعي</span>
                                                <span className="text-blue-300">{selectedSub.words_used?.toLocaleString()} من {selectedSub.max_words?.toLocaleString()}</span>
                                            </div>
                                            <div className="h-1 w-full bg-black/50 rounded-full overflow-hidden">
                                                <div
                                                    className="h-full bg-blue-500 rounded-full"
                                                    style={{ width: `${Math.min(100, ((selectedSub.words_used || 0) / (selectedSub.max_words || 1)) * 100)}%` }}
                                                />
                                            </div>
                                        </div>
                                        <div>
                                            <div className="flex justify-between text-[10px] mb-1">
                                                <span className="text-gray-400">التخزين</span>
                                                <span className="text-purple-300">{selectedSub.storage_used}MB من {selectedSub.max_storage}MB</span>
                                            </div>
                                            <div className="h-1 w-full bg-black/50 rounded-full overflow-hidden">
                                                <div
                                                    className="h-full bg-purple-500 rounded-full"
                                                    style={{ width: `${Math.min(100, ((selectedSub.storage_used || 0) / (selectedSub.max_storage || 1)) * 100)}%` }}
                                                />
                                            </div>
                                        </div>
                                    </div>
                                    <button
                                        onClick={() => handleResetUsage(selectedSub.id)}
                                        className="mt-4 w-full py-2 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 text-[10px] font-bold rounded-lg border border-blue-500/20 transition flex items-center justify-center gap-2"
                                    >
                                        <Clock className="w-3 h-3" /> تصفير عداد الشهر
                                    </button>
                                </div>
                            </div>
                        </div>

                        {/* Right Side: Controls */}
                        <div className="flex-1 p-8 overflow-y-auto">
                            <div className="flex items-center justify-between mb-8">
                                <h2 className="text-xl font-bold text-white flex items-center gap-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                    <Settings className="w-6 h-6 text-gold-500" />
                                    تعديل الصلاحيات والموارد
                                </h2>
                                <button onClick={() => setIsEditResourcesModalOpen(false)} className="text-gray-500 hover:text-white transition">
                                    <XCircle className="w-6 h-6" />
                                </button>
                            </div>

                            <div className="space-y-8">
                                {/* Date Control */}
                                <div className="space-y-2">
                                    <label className="text-sm font-bold text-gray-400 flex items-center gap-2">
                                        <Calendar className="w-4 h-4" /> تمديد الاشتراك (تاريخ الانتهاء)
                                    </label>
                                    <div className="relative group">
                                        <input
                                            type="date"
                                            value={editForm.end_date}
                                            onChange={(e) => setEditForm({ ...editForm, end_date: e.target.value })}
                                            className="w-full bg-obsidian-900 border border-gold-500/10 rounded-xl px-4 py-3 text-white focus:border-gold-500/50 outline-none transition-all group-hover:border-gold-500/30"
                                        />
                                        <div className="absolute left-3 top-1/2 -translate-y-1/2 text-xs text-gold-500 font-bold pointer-events-none bg-obsidian-900 px-2">
                                            {editForm.end_date ? new Date(editForm.end_date) > new Date() ? 'ساري' : 'منتهي' : '-'}
                                        </div>
                                    </div>
                                </div>

                                <div className="h-px bg-white/5 my-4" />

                                {/* Resource Controls */}
                                <div className="grid grid-cols-1 gap-6">
                                    {/* Storage Control */}
                                    <div className="bg-obsidian-900/30 p-4 rounded-xl border border-white/5 hover:border-gold-500/20 transition-colors">
                                        <div className="flex items-center justify-between mb-4">
                                            <label className="text-sm font-bold text-gray-300 flex items-center gap-2">
                                                <Database className="w-4 h-4 text-blue-400" />
                                                مساحة التخزين الإضافية
                                            </label>
                                            <span className="text-xs text-blue-400 bg-blue-500/10 px-2 py-1 rounded">
                                                الإجمالي: {((selectedSub.max_storage || 0) - (selectedSub.requested_storage || 0) + editForm.extra_storage_mb).toLocaleString()} MB
                                            </span>
                                        </div>
                                        <div className="flex items-center gap-4">
                                            <input
                                                type="range"
                                                min="0"
                                                max="10240"
                                                step="128"
                                                value={editForm.extra_storage_mb}
                                                onChange={(e) => setEditForm({ ...editForm, extra_storage_mb: parseInt(e.target.value) })}
                                                className="flex-1 h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
                                            />
                                            <div className="w-24 relative">
                                                <input
                                                    type="number"
                                                    value={editForm.extra_storage_mb}
                                                    onChange={(e) => setEditForm({ ...editForm, extra_storage_mb: parseInt(e.target.value) })}
                                                    className="w-full bg-black/30 border border-white/10 rounded px-2 py-1 text-sm text-center text-white focus:border-blue-500"
                                                />
                                                <span className="absolute left-1 top-1/2 -translate-y-1/2 text-[10px] text-gray-500">MB</span>
                                            </div>
                                        </div>
                                    </div>

                                    {/* AI Words Control */}
                                    <div className="bg-obsidian-900/30 p-4 rounded-xl border border-white/5 hover:border-gold-500/20 transition-colors">
                                        <div className="flex items-center justify-between mb-4">
                                            <label className="text-sm font-bold text-gray-300 flex items-center gap-2">
                                                <MessageSquare className="w-4 h-4 text-purple-400" />
                                                كلمات الذكاء الاصطناعي الإضافية
                                            </label>
                                            <span className="text-xs text-purple-400 bg-purple-500/10 px-2 py-1 rounded">
                                                الإجمالي: {(((selectedSub.max_words || 0) - (selectedSub.requested_ai_words || 0) + editForm.extra_words) / 1000).toFixed(1)}k كلمة
                                            </span>
                                        </div>
                                        <div className="flex items-center gap-4">
                                            <input
                                                type="range"
                                                min="0"
                                                max="1000000"
                                                step="5000"
                                                value={editForm.extra_words}
                                                onChange={(e) => setEditForm({ ...editForm, extra_words: parseInt(e.target.value) })}
                                                className="flex-1 h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-purple-500"
                                            />
                                            <div className="w-24 relative">
                                                <input
                                                    type="number"
                                                    value={editForm.extra_words}
                                                    onChange={(e) => setEditForm({ ...editForm, extra_words: parseInt(e.target.value) })}
                                                    className="w-full bg-black/30 border border-white/10 rounded px-2 py-1 text-sm text-center text-white focus:border-purple-500"
                                                />
                                                <span className="absolute left-1 top-1/2 -translate-y-1/2 text-[10px] text-gray-500">كلمة</span>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Assistants Control */}
                                    <div className="bg-obsidian-900/30 p-4 rounded-xl border border-white/5 hover:border-gold-500/20 transition-colors">
                                        <div className="flex items-center justify-between mb-4">
                                            <label className="text-sm font-bold text-gray-300 flex items-center gap-2">
                                                <Users className="w-4 h-4 text-green-400" />
                                                مساعدين إضافيين
                                            </label>
                                            <span className="text-xs text-green-400 bg-green-500/10 px-2 py-1 rounded">
                                                الإجمالي: {(selectedSub.max_assistants || 0) - (selectedSub.requested_assistants || 0) + editForm.extra_assistants}
                                            </span>
                                        </div>
                                        <div className="flex items-center gap-4">
                                            <button
                                                onClick={() => setEditForm(prev => ({ ...prev, extra_assistants: Math.max(0, prev.extra_assistants - 1) }))}
                                                className="w-8 h-8 rounded-lg bg-gray-700 flex items-center justify-center hover:bg-gray-600 transition"
                                            >
                                                -
                                            </button>
                                            <span className="text-xl font-bold text-white w-12 text-center">{editForm.extra_assistants}</span>
                                            <button
                                                onClick={() => setEditForm(prev => ({ ...prev, extra_assistants: prev.extra_assistants + 1 }))}
                                                className="w-8 h-8 rounded-lg bg-green-600 flex items-center justify-center hover:bg-green-500 transition text-black font-bold"
                                            >
                                                +
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div className="flex gap-4 mt-8 pt-6 border-t border-white/10">
                                <button
                                    onClick={handleUpdateResources}
                                    className="flex-1 bg-gradient-to-r from-gold-600 to-gold-500 hover:from-gold-500 hover:to-gold-400 text-black font-bold py-4 rounded-xl shadow-lg shadow-gold-500/20 transition-all flex items-center justify-center gap-2"
                                >
                                    <Save className="w-5 h-5" />
                                    حفظ التحديثات
                                </button>
                                <button
                                    onClick={() => setIsEditResourcesModalOpen(false)}
                                    className="px-8 bg-obsidian-700 hover:bg-obsidian-600 text-white font-bold py-4 rounded-xl transition-all"
                                >
                                    إلغاء
                                </button>
                            </div>
                        </div>
                    </motion.div>
                </div>
            )}
        </div>
    );
}

function CountryPricingRow({ country, initialPricing, onSave }: { country: Country, initialPricing: CountryPricing, onSave: (d: CountryPricing) => void }) {
    const [pricing, setPricing] = useState(initialPricing);
    const [isDirty, setIsDirty] = useState(false);

    const handleChange = (field: keyof CountryPricing, val: number) => {
        setPricing({ ...pricing, [field]: val });
        setIsDirty(true);
    };

    return (
        <tr className="hover:bg-gold-500/5 transition-colors">
            <td className="px-6 py-4 text-white font-bold">{country.name_ar}</td>
            <td className="px-6 py-4">
                <div className="flex items-center gap-2">
                    <input
                        type="number"
                        value={pricing.base_platform_fee}
                        onChange={(e) => handleChange('base_platform_fee', parseFloat(e.target.value))}
                        className="w-20 bg-obsidian-900 border border-gold-500/10 rounded p-1 text-sm text-white focus:border-gold-500/50 outline-none"
                    />
                    <span className="text-gray-500 text-xs">{country.currency_symbol}</span>
                </div>
            </td>
            <td className="px-6 py-4">
                <div className="flex items-center gap-2">
                    <input
                        type="number"
                        value={pricing.price_per_assistant}
                        onChange={(e) => handleChange('price_per_assistant', parseFloat(e.target.value))}
                        className="w-24 bg-obsidian-900 border border-gold-500/10 rounded p-1 text-sm text-white focus:border-gold-500/50 outline-none"
                    />
                    <span className="text-gray-500 text-xs">{country.currency_symbol}</span>
                </div>
            </td>
            <td className="px-6 py-4">
                <div className="flex items-center gap-2">
                    <input
                        type="number"
                        step="0.01"
                        value={pricing.price_per_gb_monthly}
                        onChange={(e) => handleChange('price_per_gb_monthly', parseFloat(e.target.value))}
                        className="w-24 bg-obsidian-900 border border-gold-500/10 rounded p-1 text-sm text-white focus:border-gold-500/50 outline-none"
                    />
                    <span className="text-gray-500 text-xs">{country.currency_symbol}</span>
                </div>
            </td>
            <td className="px-6 py-4">
                <div className="flex items-center gap-2">
                    <input
                        type="number"
                        value={pricing.price_per_1000_words}
                        onChange={(e) => handleChange('price_per_1000_words', parseFloat(e.target.value))}
                        className="w-24 bg-obsidian-900 border border-gold-500/10 rounded p-1 text-sm text-white focus:border-gold-500/50 outline-none"
                    />
                    <span className="text-gray-500 text-xs">{country.currency_symbol}</span>
                </div>
            </td>
            <td className="px-6 py-4">
                <div className="flex items-center gap-2">
                    <input
                        type="number"
                        value={pricing.yearly_discount_percent}
                        onChange={(e) => handleChange('yearly_discount_percent', parseFloat(e.target.value))}
                        className="w-24 bg-obsidian-900 border border-gold-500/10 rounded p-1 text-sm text-white focus:border-gold-500/50 outline-none"
                    />
                    <span className="text-gray-500 text-xs">%</span>
                </div>
            </td>
            <td className="px-6 py-4">
                <button
                    disabled={!isDirty}
                    onClick={() => { onSave(pricing); setIsDirty(false); }}
                    className={`p-2 rounded-lg transition ${isDirty ? 'bg-gold-500 text-black hover:bg-gold-400' : 'bg-gray-800 text-gray-600 cursor-not-allowed'}`}
                >
                    <Save className="w-4 h-4" />
                </button>
            </td>
        </tr>
    );
}
