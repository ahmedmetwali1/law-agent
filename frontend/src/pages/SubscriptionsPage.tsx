import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    CreditCard,
    Star,
    Shield,
    CheckCircle,
    Clock,
    AlertTriangle,
    Database,
    Users,
    MessageSquare,
    ChevronRight,
    Copy,
    Phone,
    Calendar
} from 'lucide-react';
import { toast } from 'sonner';
import { apiClient } from '../api/client';
import { useBreadcrumb } from '../contexts/BreadcrumbContext';

interface Package {
    name: string;
    name_ar: string;
    color: string;
    description: string;
    description_ar: string;
    max_assistants: number;
    storage_mb: number;
    ai_words_monthly: number;
}

interface Country {
    currency_symbol: string;
    currency_name_ar: string;
}

interface Subscription {
    id: string;
    status: 'active' | 'trial' | 'expired' | 'renewal_requested';
    start_date: string;
    end_date: string;
    days_remaining: number;
    status_display: string;

    // Usage
    max_assistants: number;
    assistants_count: number;
    extra_assistants: number;

    storage_mb: number;
    storage_used_mb: number;
    extra_storage_mb: number;

    ai_words_monthly: number;
    words_used_this_month: number;
    extra_words: number;

    package: Package;
    country: Country;
}

interface PaymentInfo {
    bank_name: string;
    account_number: string;
    iban: string;
    account_name: string;
    contact_phone: string;
    instructions: string;
}

export function SubscriptionsPage() {
    const { setPageTitle } = useBreadcrumb();
    const [subscription, setSubscription] = useState<Subscription | null>(null);
    const [packages, setPackages] = useState<any[]>([]);
    const [paymentInfo, setPaymentInfo] = useState<PaymentInfo | null>(null);
    const [loading, setLoading] = useState(true);

    // Renewal Flow State
    const [showRenewalModal, setShowRenewalModal] = useState(false);
    const [step, setStep] = useState<'packages' | 'payment'>('packages');
    const [selectedPackage, setSelectedPackage] = useState<any | null>(null);
    const [requesting, setRequesting] = useState(false);

    useEffect(() => {
        setPageTitle('اشتراكاتي');
        loadSubscription();
        loadPackages();
    }, [setPageTitle]);

    const loadSubscription = async () => {
        try {
            const data = await apiClient.get<Subscription>('/api/subscriptions/me');
            setSubscription(data);
        } catch (error) {
            console.error('Error loading subscription:', error);
        } finally {
            setLoading(false);
        }
    };

    const loadPackages = async () => {
        try {
            const data = await apiClient.get('/api/subscriptions/packages');
            setPackages(data);
        } catch (error) {
            console.error('Error loading packages:', error);
        }
    };

    const [priceBreakdown, setPriceBreakdown] = useState<any>(null);
    const [customConfig, setCustomConfig] = useState({
        assistants: 0,
        storage_mb: 50,
        ai_words: 0,
        cycle: 'monthly' as 'monthly' | 'yearly'
    });

    useEffect(() => {
        if (packages && packages.length > 0) {
            const defaultPkg = packages.find(p => p.is_default) || packages[0];
            if (defaultPkg) {
                setCustomConfig(prev => ({
                    ...prev,
                    assistants: defaultPkg.max_assistants || 0,
                    storage_mb: defaultPkg.storage_mb || 50,
                    ai_words: defaultPkg.ai_words_monthly || 0
                }));
            }
        }
    }, [packages]);
    useEffect(() => {
        const timer = setTimeout(() => {
            calculatePrice();
        }, 500);
        return () => clearTimeout(timer);
    }, [customConfig]);

    const calculatePrice = async () => {
        try {
            const res = await apiClient.post('/api/subscriptions/calculate-price', customConfig);
            setPriceBreakdown(res);
        } catch (error) {
            console.error(error);
        }
    };

    const updateCustomConfig = (key: string, value: number) => {
        setCustomConfig(prev => ({ ...prev, [key]: value }));
    };

    const handleRenewalClick = async () => {
        // Prepare "Flexible" package object
        const flexiblePkg = packages.find(p => p.is_flexible) || {
            id: 'flexible',
            name: 'Flexible',
            name_ar: 'الباقة المرنة',
            price_monthly: priceBreakdown?.total_monthly,
            custom_config: customConfig
        };

        // Inject current calculated price and config into the selected package object
        const pkgWithConfig = {
            ...flexiblePkg,
            price_monthly: priceBreakdown?.total_monthly,
            custom_config: customConfig
        };

        setSelectedPackage(pkgWithConfig);
        setStep('payment'); // Go straight to payment/confirm

        if (!paymentInfo) {
            try {
                const info = await apiClient.get<PaymentInfo>('/api/subscriptions/config/payment-info');
                setPaymentInfo(info);
            } catch (error) {
                toast.error('فشل تحميل معلومات الدفع');
            }
        }
        setShowRenewalModal(true);
    };

    const handleViewPaymentInfo = async () => {
        setStep('payment');
        if (!paymentInfo) {
            try {
                const info = await apiClient.get<PaymentInfo>('/api/subscriptions/config/payment-info');
                setPaymentInfo(info);
            } catch (error) {
                toast.error('فشل تحميل معلومات الدفع');
                return;
            }
        }
        setShowRenewalModal(true);
    };

    const handlePackageSelect = (pkg: any) => {
        setSelectedPackage(pkg);
        setStep('payment');
    };

    const confirmRenewalRequest = async () => {
        if (!selectedPackage) return;

        setRequesting(true);
        try {
            await apiClient.post('/api/subscriptions/request-renewal', {
                package_id: selectedPackage.id,
                custom_config: selectedPackage.custom_config // Pass custom limits
            });
            toast.success(`تم طلب تجديد الاشتراك: ${selectedPackage.name_ar}`);
            setShowRenewalModal(false);
            loadSubscription();
        } catch (error) {
            toast.error('حدث خطأ أثناء إرسال الطلب');
        } finally {
            setRequesting(false);
        }
    };

    const copyToClipboard = (text: string) => {
        navigator.clipboard.writeText(text);
        toast.success('تم النسخ');
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[60vh]">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500"></div>
            </div>
        );
    }

    if (!subscription) {
        return (
            <div className="text-center py-20">
                <p className="text-gray-400">لا يوجد اشتراك فعال حالياً.</p>
                <button className="mt-4 px-6 py-2 bg-green-500 text-black rounded-lg font-bold">اشترك الآن</button>
            </div>
        );
    }

    const {
        package: pkg,
        // country, // Unused
        days_remaining,
        status,
        status_display
    } = subscription;

    const isTrial = status === 'trial';
    const isExpired = days_remaining < 0;
    const isRenewalRequested = status === 'renewal_requested';

    // Calculate Usage Percentages
    const assistantsUsed = subscription.assistants_count || 0;
    const assistantsLimit = (subscription.package?.max_assistants || 0) + (subscription.extra_assistants || 0);
    const assistantsPercent = Math.min(100, (assistantsUsed / (assistantsLimit || 1)) * 100);

    const storageUsedMB = subscription.storage_used_mb || 0;
    const storageLimitMB = (subscription.package?.storage_mb || 0) + (subscription.extra_storage_mb || 0);
    const storagePercent = Math.min(100, (storageUsedMB / (storageLimitMB || 1)) * 100);

    const wordsUsed = subscription.words_used_this_month || 0;
    const wordsLimit = (subscription.package?.ai_words_monthly || 0) + (subscription.extra_words || 0);
    const wordsPercent = Math.min(100, (wordsUsed / (wordsLimit || 1)) * 100);
    return (
        <div className="max-w-5xl mx-auto space-y-8 p-6 bg-obsidian-900/30 rounded-3xl border border-gray-800/50">
            {/* Header / Status Banner */}
            <div className="flex flex-col md:flex-row items-center justify-between gap-6">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
                        {isTrial ? <Star className="text-yellow-400 fill-yellow-400" /> : <Shield className="text-green-400" />}
                        {subscription.package?.name_ar || 'اشتراك'}
                    </h1>
                    <div className="flex flex-wrap gap-2">
                        <div className={`inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-sm font-bold ${isExpired ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                            isTrial ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30' :
                                'bg-green-500/20 text-green-400 border border-green-500/30'
                            }`}>
                            <Clock className="w-4 h-4" />
                            {status_display}
                        </div>

                        {days_remaining >= 0 && (
                            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-sm font-bold bg-obsidian-800 text-gray-300 border border-gray-700/50">
                                <Calendar size={14} className="text-gold-500" />
                                متبقي {days_remaining} يوم
                            </div>
                        )}
                    </div>
                </div>

                <div className="flex gap-3">
                    {isRenewalRequested ? (
                        <div className="flex flex-col md:flex-row gap-3">
                            <div className="px-6 py-3 bg-blue-500/20 text-blue-300 border border-blue-500/30 rounded-xl flex items-center gap-2">
                                <Clock className="w-5 h-5 animate-pulse" />
                                طلب التجديد قيد المراجعة
                            </div>
                            <button
                                onClick={handleViewPaymentInfo}
                                className="px-6 py-3 bg-obsidian-800 text-gold-500 border border-gold-500/30 rounded-xl hover:bg-gold-500/10 transition flex items-center gap-2"
                            >
                                <CreditCard className="w-5 h-5" />
                                عرض بيانات التحويل
                            </button>
                        </div>
                    ) : (
                        <motion.button
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            onClick={() => {
                                // Scroll to builder or just trigger it
                                document.getElementById('flexible-builder')?.scrollIntoView({ behavior: 'smooth' });
                            }}
                            className={`px-8 py-3 rounded-xl font-bold flex items-center gap-2 shadow-lg ${isExpired ? 'bg-red-600 hover:bg-red-700 text-white shadow-red-500/20' :
                                'bg-green-600 hover:bg-green-700 text-black shadow-green-500/20'
                                }`}
                        >
                            <CreditCard className="w-5 h-5" />
                            {isExpired ? 'تجديد الاشتراك الآن' : 'ترقية / تجديد'}
                        </motion.button>
                    )}
                </div>
            </div>

            {/* Usage Stats (Keep current status visible) */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-obsidian-800/50 rounded-2xl p-6 border border-gray-700/50">
                    <div className="flex justify-between mb-4">
                        <span className="text-gray-300">الذكاء الاصطناعي</span>
                        <span className="text-white font-mono">{wordsUsed.toLocaleString()} / {wordsLimit?.toLocaleString()}</span>
                    </div>
                    <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                        <div className="h-full bg-purple-500" style={{ width: `${wordsPercent}%` }}></div>
                    </div>
                </div>
                <div className="bg-obsidian-800/50 rounded-2xl p-6 border border-gray-700/50">
                    <div className="flex justify-between mb-4">
                        <span className="text-gray-300">التخزين</span>
                        <span className="text-white font-mono">{storageUsedMB.toLocaleString()} / {storageLimitMB.toLocaleString()} MB</span>
                    </div>
                    <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                        <div className="h-full bg-blue-500" style={{ width: `${storagePercent}%` }}></div>
                    </div>
                </div>
                <div className="bg-obsidian-800/50 rounded-2xl p-6 border border-gray-700/50">
                    <div className="flex justify-between mb-4">
                        <span className="text-gray-300">المساعدين</span>
                        <span className="text-white font-mono">{assistantsUsed} / {assistantsLimit}</span>
                    </div>
                    <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                        <div className="h-full bg-green-500" style={{ width: `${assistantsPercent}%` }}></div>
                    </div>
                </div>
            </div>

            {/* Standard Packages Grid - Hidden by User Request to focus on Flexible Builder */}
            {/* 
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
               ... (hidden)
            </div> 
            */}

            <div id="flexible-builder">
                {/* Flexible Plan Builder */}
                <div className="bg-obsidian-900 border border-gold-500/30 rounded-3xl p-8 mb-8 relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-gold-500/10 blur-3xl rounded-full translate-x-1/2 -translate-y-1/2"></div>

                    <h2 className="text-2xl font-bold text-white mb-2 flex items-center gap-2">
                        <Star className="text-gold-500 fill-gold-500" />
                        صمم باقتك بنفسك
                    </h2>
                    <p className="text-gray-400 mb-8">اختر ما يناسب حجم أعمالك وادفع فقط مقابل ما تحتاج.</p>

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
                        {/* Controls */}
                        <div className="space-y-8">
                            {/* 1. Base Included */}
                            <div className="flex items-center gap-4 p-4 bg-obsidian-800/50 rounded-xl border border-gray-700/50">
                                <Shield className="w-8 h-8 text-green-400" />
                                <div>
                                    <h3 className="text-white font-bold">النظام الإداري الأساسي</h3>
                                    <p className="text-sm text-gray-400">جميع مميزات إدارة القضايا والموكلين (بدون ذكاء اصطناعي)</p>
                                </div>
                                <div className="mr-auto">
                                    <CheckCircle className="w-6 h-6 text-green-500" />
                                </div>
                            </div>

                            {/* 2. Assistants Slider */}
                            <div>
                                <div className="flex justify-between mb-2">
                                    <label className="text-white font-bold flex items-center gap-2">
                                        <Users className="w-4 h-4 text-purple-400" />
                                        عدد المساعدين
                                    </label>
                                    <span className="text-gold-500 font-bold">{customConfig.assistants}</span>
                                </div>
                                <input
                                    type="range"
                                    min="0" max="20"
                                    value={customConfig.assistants}
                                    onChange={(e) => updateCustomConfig('assistants', parseInt(e.target.value))}
                                    className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-gold-500"
                                />
                                <p className="text-xs text-gray-500 mt-1">تتيح للموظفين الدخول للنظام بصلاحيات محددة.</p>
                            </div>

                            {/* 3. Storage Slider */}
                            <div>
                                <div className="flex justify-between mb-2">
                                    <label className="text-white font-bold flex items-center gap-2">
                                        <Database className="w-4 h-4 text-blue-400" />
                                        مساحة التخزين (MB)
                                    </label>
                                    <span className="text-gold-500 font-bold">{customConfig.storage_mb.toLocaleString()} MB</span>
                                </div>
                                <input
                                    type="range"
                                    min={(packages && packages.length > 0 ? packages.find(p => p.is_default)?.storage_mb : 50) || 50}
                                    max="5120"
                                    step="50"
                                    value={customConfig.storage_mb}
                                    onChange={(e) => updateCustomConfig('storage_mb', parseInt(e.target.value))}
                                    className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
                                />
                            </div>

                            {/* 4. AI Words Slider */}
                            <div>
                                <div className="flex justify-between mb-2">
                                    <label className="text-white font-bold flex items-center gap-2">
                                        <MessageSquare className="w-4 h-4 text-purple-400" />
                                        كلمات الذكاء الاصطناعي (شهرياً)
                                    </label>
                                    <span className="text-gold-500 font-bold">{customConfig.ai_words.toLocaleString()} كلمة</span>
                                </div>
                                <input
                                    type="range"
                                    min="0" max="1000000" step="5000"
                                    value={customConfig.ai_words}
                                    onChange={(e) => updateCustomConfig('ai_words', parseInt(e.target.value))}
                                    className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-purple-500"
                                />
                                <p className="text-xs text-gray-500 mt-1">تستخدم للتحليل القانوني وكتابة المذكرات.</p>
                            </div>
                        </div>

                        {/* Live Price Receipt */}
                        <div className="bg-gradient-to-br from-obsidian-800 to-obsidian-900 border border-gold-500/20 rounded-3xl p-8 flex flex-col justify-between">
                            <div>
                                <h3 className="text-xl font-bold text-white mb-6 border-b border-gray-700 pb-4">ملخص الباقة</h3>

                                <div className="space-y-4">
                                    <div className="flex justify-between text-gray-300">
                                        <span>النظام الأساسي</span>
                                        <span>{priceBreakdown?.currency_symbol || '$'}{priceBreakdown?.base_fee || 0}</span>
                                    </div>
                                    <div className="flex justify-between text-gray-300">
                                        <span>المساعدين ({customConfig.assistants})</span>
                                        <span>{priceBreakdown?.currency_symbol || '$'}{(priceBreakdown?.assistants_cost || 0).toFixed(2)}</span>
                                    </div>
                                    <div className="flex justify-between text-gray-300">
                                        <span>التخزين ({customConfig.storage_mb.toLocaleString()} MB)</span>
                                        <span>{priceBreakdown?.currency_symbol || '$'}{(priceBreakdown?.storage_cost || 0).toFixed(2)}</span>
                                    </div>
                                    <div className="flex justify-between text-gray-300">
                                        <span>الذكاء الاصطناعي ({customConfig.ai_words.toLocaleString()})</span>
                                        <span>{priceBreakdown?.currency_symbol || '$'}{(priceBreakdown?.ai_cost || 0).toFixed(2)}</span>
                                    </div>
                                </div>
                            </div>

                            <div className="mt-8 pt-8 border-t border-gray-700/50">
                                <div className="flex justify-between items-end mb-6">
                                    <span className="text-gray-400">الإجمالي الشهري</span>
                                    <div className="text-right">
                                        <span className="text-4xl font-bold text-white">
                                            {priceBreakdown?.currency_symbol || '$'}{priceBreakdown?.total_monthly?.toFixed(2) || '0.00'}
                                        </span>
                                        <span className="text-gray-500 text-sm block">/ شهر</span>
                                    </div>
                                </div>

                                <button
                                    onClick={handleRenewalClick}
                                    className="w-full py-3 bg-gold-500 hover:bg-gold-600 text-black font-bold rounded-xl transition shadow-lg shadow-gold-500/20"
                                >
                                    {isExpired ? 'تجديد الآن' : 'تحديث الباقة'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            {/* End Flexible Builder */}

            {/* Existing SubscriptionsPage Logic Helper */}
            {/* We need to inject the logic for `updateCustomConfig` and `priceBreakdown` state */}
            {/* And hide the old Packages Grid if Flexible is active, or keep it as legacy */}

            {/* Renewal & Package Selection Modal */}
            <AnimatePresence>
                {showRenewalModal && (
                    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                        <motion.div
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.9 }}
                            className="bg-obsidian-900 border border-gold-500/20 rounded-3xl max-w-4xl w-full max-h-[85vh] overflow-y-auto shadow-2xl shadow-gold-900/10 custom-scrollbar"
                        >

                            {/* Step 2: Payment Details */}
                            {step === 'payment' && paymentInfo && (
                                <div className="p-6">
                                    <div className="flex items-center gap-2 mb-6 text-gold-500 cursor-pointer" onClick={() => setStep('packages')}>
                                        <ChevronRight className="w-5 h-5" />
                                        <span className="text-sm font-bold">عودة للباقات</span>
                                    </div>

                                    <h2 className="text-2xl font-bold text-white mb-2 flex items-center gap-2">
                                        <CreditCard className="w-6 h-6 text-green-400" />
                                        إتمام عملية الدفع
                                    </h2>
                                    <p className="text-gray-400 text-sm mb-6">
                                        أنت على وشك الاشتراك في <span className="text-white font-bold">{selectedPackage?.name_ar}</span>.
                                        علماً أن الاشتراك صالح لمدة <span className="text-white font-bold">30 يوماً فقط</span> من تاريخ التفعيل وينتهي تلقائياً.
                                        يرجى تحويل مبلغ <span className="text-green-400 font-bold font-mono text-lg mx-1">{priceBreakdown?.currency_symbol || ''} {priceBreakdown?.final_price}</span>
                                        إلى الحساب التالي:
                                    </p>

                                    <div className="bg-black/40 rounded-xl p-4 border border-gray-700/50 space-y-3 mb-6">
                                        <div className="flex justify-between items-center">
                                            <span className="text-gray-400 text-sm">البنك</span>
                                            <span className="text-white font-bold">{paymentInfo.bank_name}</span>
                                        </div>
                                        <div className="flex justify-between items-center">
                                            <span className="text-gray-400 text-sm">اسم المستفيد</span>
                                            <span className="text-white font-bold">{paymentInfo.account_name}</span>
                                        </div>
                                        <div className="mt-2 pt-2 border-t border-gray-700/50">
                                            <span className="text-gray-400 text-xs block mb-1">رقم الحساب / IBAN</span>
                                            <div className="flex items-center justify-between bg-obsidian-800 p-2 rounded-lg">
                                                <code className="text-green-400 font-mono text-sm">{paymentInfo.iban || paymentInfo.account_number}</code>
                                                <button
                                                    onClick={() => copyToClipboard(paymentInfo.iban || paymentInfo.account_number)}
                                                    className="p-1 hover:bg-white/10 rounded transition"
                                                >
                                                    <Copy className="w-4 h-4 text-gray-400" />
                                                </button>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="bg-blue-500/10 border border-blue-500/20 p-4 rounded-xl flex gap-3 text-sm text-blue-300 mb-6">
                                        <Phone className="w-5 h-5 shrink-0" />
                                        <div>
                                            <p className="font-bold mb-1">تواصل معنا بعد التحويل</p>
                                            <p>{paymentInfo.instructions}</p>
                                        </div>
                                    </div>

                                    <div className="flex gap-3">
                                        <button
                                            onClick={() => setShowRenewalModal(false)}
                                            className="flex-1 px-4 py-3 rounded-xl text-gray-400 hover:bg-white/5 font-bold transition"
                                        >
                                            إلغاء
                                        </button>
                                        <button
                                            onClick={confirmRenewalRequest}
                                            disabled={requesting}
                                            className="flex-[2] px-4 py-3 bg-green-600 hover:bg-green-700 text-white rounded-xl font-bold transition shadow-lg shadow-green-500/20 flex items-center justify-center gap-2"
                                        >
                                            {requesting ? (
                                                <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                            ) : (
                                                <>
                                                    <CheckCircle className="w-5 h-5" />
                                                    تأكيد طلب الاشتراك
                                                </>
                                            )}
                                        </button>
                                    </div>
                                </div>
                            )}
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>
        </div>
    );
}
