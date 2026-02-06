import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
    Users,
    Search,
    UserCheck,
    UserX,
    Mail,
    Phone,
    Briefcase,
    Calendar,
    ToggleLeft,
    ToggleRight,
    ChevronLeft,
    ChevronRight,
    Eye,
    Globe,
    Linkedin,
    MapPin,
    Award,
    Clock,
    Languages,
    X
} from 'lucide-react';
import { getAllLawyers, toggleLawyerActivation, LawyerInfo } from '../../api/admin';
import { toast } from 'sonner';

const LAWYERS_PER_PAGE = 9;

export default function LawyersManagement() {
    const [lawyers, setLawyers] = useState<LawyerInfo[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [currentPage, setCurrentPage] = useState(1);
    const [togglingId, setTogglingId] = useState<string | null>(null);
    const [selectedLawyer, setSelectedLawyer] = useState<LawyerInfo | null>(null);

    useEffect(() => {
        loadLawyers();
    }, []);

    const loadLawyers = async () => {
        try {
            setLoading(true);
            const data = await getAllLawyers();
            setLawyers(data);
        } catch (error) {
            console.error('Error loading lawyers:', error);
            toast.error('فشل تحميل قائمة المحامين');
        } finally {
            setLoading(false);
        }
    };

    const handleToggleActivation = async (lawyer: LawyerInfo) => {
        const newStatus = !lawyer.is_active;
        const reason = newStatus ? undefined : prompt('سبب الإيقاف (اختياري):') || undefined;

        try {
            setTogglingId(lawyer.id);
            await toggleLawyerActivation(lawyer.id, newStatus, reason);

            // Update local state
            setLawyers(prev => prev.map(l =>
                l.id === lawyer.id ? { ...l, is_active: newStatus } : l
            ));

            toast.success(newStatus ? 'تم تفعيل الحساب' : 'تم إيقاف الحساب');
        } catch (error) {
            console.error('Error toggling activation:', error);
            toast.error('فشل تحديث حالة الحساب');
        } finally {
            setTogglingId(null);
        }
    };

    // Filter and paginate
    const filteredLawyers = lawyers.filter(lawyer =>
        lawyer.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        lawyer.email?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        lawyer.role?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const totalPages = Math.ceil(filteredLawyers.length / LAWYERS_PER_PAGE);
    const startIndex = (currentPage - 1) * LAWYERS_PER_PAGE;
    const currentLawyers = filteredLawyers.slice(startIndex, startIndex + LAWYERS_PER_PAGE);

    // Reset page on search
    useEffect(() => {
        setCurrentPage(1);
    }, [searchQuery]);

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
                        <Users className="w-7 h-7" />
                        إدارة المستخدمين
                    </h1>
                    <p className="text-gray-400 mt-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        إجمالي: {lawyers.length} مستخدم ({lawyers.filter(l => l.is_active).length} نشط)
                    </p>
                </div>
            </div>

            {/* Search */}
            <div className="backdrop-blur-xl bg-obsidian-800/70 border border-purple-500/20 rounded-xl p-4">
                <div className="relative">
                    <Search className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="بحث بالاسم أو البريد الإلكتروني أو الدور..."
                        className="w-full pr-12 pl-4 py-3 bg-obsidian-900/50 border border-purple-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors"
                        style={{ fontFamily: 'Cairo, sans-serif' }}
                    />
                </div>
            </div>

            {/* Results count */}
            <div className="text-sm text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>
                عرض {currentLawyers.length} من {filteredLawyers.length} مستخدم
            </div>

            {/* Lawyers Grid */}
            {currentLawyers.length === 0 ? (
                <div className="text-center py-12 backdrop-blur-xl bg-obsidian-800/50 border border-purple-500/20 rounded-xl">
                    <Users className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                    <h3 className="text-xl font-bold text-gray-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        لا يوجد مستخدمين
                    </h3>
                    <p className="text-gray-500" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        {searchQuery ? 'جرب تعديل البحث' : 'لم يتم التسجيل بعد'}
                    </p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {currentLawyers.map((lawyer, index) => (
                        <motion.div
                            key={lawyer.id}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: index * 0.05 }}
                            className="backdrop-blur-xl bg-obsidian-800/70 border border-purple-500/20 rounded-xl p-6 hover:border-purple-500/50 transition-all flex flex-col"
                        >
                            {/* Header */}
                            <div className="flex items-start justify-between mb-4">
                                <div className="flex items-center gap-3">
                                    <div className="w-12 h-12 rounded-full overflow-hidden border-2 border-purple-500/30 bg-obsidian-900 shrink-0">
                                        {lawyer.profile_image_url ? (
                                            <img
                                                src={lawyer.profile_image_url.startsWith('/') ? `http://localhost:8000${lawyer.profile_image_url}` : lawyer.profile_image_url}
                                                alt={lawyer.full_name}
                                                className="w-full h-full object-cover"
                                            />
                                        ) : (
                                            <div className="w-full h-full flex items-center justify-center bg-purple-500/10">
                                                <Users className="w-6 h-6 text-purple-500" />
                                            </div>
                                        )}
                                    </div>
                                    <div className="flex-1">
                                        <div className="flex items-center gap-2 mb-1">
                                            <h3 className="text-lg font-bold text-white leading-tight" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                                {lawyer.full_name}
                                            </h3>
                                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${lawyer.role === 'manager' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/20' :
                                                    lawyer.role === 'lawyer' ? 'bg-purple-500/20 text-purple-400 border border-purple-500/20' :
                                                        'bg-cobalt-500/20 text-cobalt-400 border border-cobalt-500/20'
                                                }`} style={{ fontFamily: 'Cairo, sans-serif' }}>
                                                {lawyer.role_info?.name_ar || (lawyer.role === 'manager' ? 'مدير' : lawyer.role === 'lawyer' ? 'محامي' : 'مساعد')}
                                            </span>
                                        </div>
                                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] ${lawyer.is_active
                                            ? 'bg-green-500/20 text-green-400'
                                            : 'bg-red-500/20 text-red-400'
                                            }`} style={{ fontFamily: 'Cairo, sans-serif' }}>
                                            {lawyer.is_active ? (
                                                <><UserCheck className="w-3 h-3" /> نشط</>
                                            ) : (
                                                <><UserX className="w-3 h-3" /> موقوف</>
                                            )}
                                        </span>
                                    </div>
                                </div>

                                {/* Toggle Button */}
                                <button
                                    onClick={() => handleToggleActivation(lawyer)}
                                    disabled={togglingId === lawyer.id}
                                    className={`p-2 rounded-lg transition-all ${lawyer.is_active
                                        ? 'text-green-400 hover:bg-green-500/10'
                                        : 'text-red-400 hover:bg-red-500/10'
                                        } disabled:opacity-50`}
                                    title={lawyer.is_active ? 'إيقاف الحساب' : 'تفعيل الحساب'}
                                >
                                    {togglingId === lawyer.id ? (
                                        <div className="w-6 h-6 border-2 border-current border-t-transparent rounded-full animate-spin" />
                                    ) : lawyer.is_active ? (
                                        <ToggleRight className="w-6 h-6" />
                                    ) : (
                                        <ToggleLeft className="w-6 h-6" />
                                    )}
                                </button>
                            </div>

                            {/* Info */}
                            <div className="space-y-2 mb-6 flex-1">
                                <div className="flex items-center gap-2 text-gray-300">
                                    <Award className="w-4 h-4 text-purple-400" />
                                    <span className="text-sm font-medium" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                        {lawyer.lawyer_license_type || 'درجة الترخيص غير محددة'}
                                    </span>
                                </div>
                                <div className="flex items-center gap-2 text-gray-400">
                                    <Briefcase className="w-4 h-4 text-gray-500" />
                                    <span className="text-sm" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                        {lawyer.specialization || 'التخصص غير محدد'}
                                    </span>
                                </div>
                                <div className="flex items-center gap-2 text-gray-400">
                                    <Mail className="w-4 h-4 text-gray-500" />
                                    <span className="text-sm truncate">{lawyer.email}</span>
                                </div>
                            </div>

                            {/* Footer Actions */}
                            <div className="flex items-center justify-between pt-4 border-t border-purple-500/10 mt-auto">
                                <div className="flex items-center gap-3">
                                    <div className="flex items-center gap-1 text-xs text-gray-500">
                                        <Briefcase className="w-3 h-3" />
                                        <span>{lawyer.total_cases || 0}</span>
                                    </div>
                                    <div className="flex items-center gap-1 text-xs text-gray-500">
                                        <Users className="w-3 h-3" />
                                        <span>{lawyer.total_clients || 0}</span>
                                    </div>
                                </div>

                                <button
                                    onClick={() => setSelectedLawyer(lawyer)}
                                    className="flex items-center gap-1 text-sm text-purple-400 hover:text-purple-300 transition-colors font-medium"
                                    style={{ fontFamily: 'Cairo, sans-serif' }}
                                >
                                    <Eye className="w-4 h-4" />
                                    عرض التفاصيل
                                </button>
                            </div>
                        </motion.div>
                    ))}
                </div>
            )}

            {/* Pagination */}
            {totalPages > 1 && (
                <div className="flex items-center justify-center gap-2 mt-8">
                    <button
                        onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                        disabled={currentPage === 1}
                        className="p-2 rounded-lg bg-obsidian-800 border border-purple-500/20 text-white hover:border-purple-500/50 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                    >
                        <ChevronRight className="w-5 h-5" />
                    </button>

                    <div className="flex items-center gap-2">
                        {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
                            <button
                                key={page}
                                onClick={() => setCurrentPage(page)}
                                className={`px-4 py-2 rounded-lg font-medium transition-all ${currentPage === page
                                    ? 'bg-purple-500 text-white'
                                    : 'bg-obsidian-800 border border-purple-500/20 text-white hover:border-purple-500/50'
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
                        className="p-2 rounded-lg bg-obsidian-800 border border-purple-500/20 text-white hover:border-purple-500/50 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                    >
                        <ChevronLeft className="w-5 h-5" />
                    </button>
                </div>
            )}

            {/* Modal */}
            {selectedLawyer && (
                <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="bg-obsidian-900 border border-purple-500/30 rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto"
                    >
                        {/* Modal Header */}
                        <div className="sticky top-0 bg-obsidian-900/90 backdrop-blur-md border-b border-purple-500/20 p-6 flex items-center justify-between z-10">
                            <div className="flex items-center gap-4">
                                <div className="w-16 h-16 rounded-full overflow-hidden border-2 border-purple-500/30 bg-black shrink-0">
                                    {selectedLawyer.profile_image_url ? (
                                        <img
                                            src={selectedLawyer.profile_image_url.startsWith('/') ? `http://localhost:8000${selectedLawyer.profile_image_url}` : selectedLawyer.profile_image_url}
                                            alt={selectedLawyer.full_name}
                                            className="w-full h-full object-cover"
                                        />
                                    ) : (
                                        <div className="w-full h-full flex items-center justify-center bg-purple-500/10 text-purple-500">
                                            <Users className="w-8 h-8" />
                                        </div>
                                    )}
                                </div>
                                <div>
                                    <h2 className="text-xl font-bold text-white mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>{selectedLawyer.full_name}</h2>
                                    <p className="text-gray-400 text-sm" style={{ fontFamily: 'Cairo, sans-serif' }}>{selectedLawyer.specialization || 'تخصص غير محدد'}</p>
                                </div>
                            </div>
                            <button
                                onClick={() => setSelectedLawyer(null)}
                                className="p-2 hover:bg-white/5 rounded-full transition-colors text-gray-400 hover:text-white"
                            >
                                <X className="w-6 h-6" />
                            </button>
                        </div>

                        {/* Modal Body */}
                        <div className="p-6 space-y-8" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            {/* Stats Grid */}
                            <div className="grid grid-cols-3 gap-4">
                                <div className="bg-obsidian-800/50 border border-purple-500/10 rounded-xl p-3 text-center">
                                    <Briefcase className="w-5 h-5 text-purple-400 mx-auto mb-1" />
                                    <div className="text-lg font-bold text-white">{selectedLawyer.total_cases || 0}</div>
                                    <div className="text-[10px] text-gray-500">إجمالي القضايا</div>
                                </div>
                                <div className="bg-obsidian-800/50 border border-purple-500/10 rounded-xl p-3 text-center">
                                    <Users className="w-5 h-5 text-blue-400 mx-auto mb-1" />
                                    <div className="text-lg font-bold text-white">{selectedLawyer.total_clients || 0}</div>
                                    <div className="text-[10px] text-gray-500">إجمالي الموكلين</div>
                                </div>
                                <div className="bg-obsidian-800/50 border border-purple-500/10 rounded-xl p-3 text-center">
                                    <Clock className="w-5 h-5 text-green-400 mx-auto mb-1" />
                                    <div className="text-lg font-bold text-white">{selectedLawyer.years_of_experience || 0}</div>
                                    <div className="text-[10px] text-gray-500">سنوات الخبرة</div>
                                </div>
                            </div>

                            {/* Professional Details */}
                            <div>
                                <h3 className="text-sm font-bold text-purple-400 uppercase tracking-wider mb-4 border-r-2 border-purple-500 pr-2">المعلومات المهنية</h3>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-obsidian-800/30 rounded-xl p-4 border border-white/5">
                                    <DetailItem
                                        icon={<Users className="w-4 h-4" />}
                                        label="نوع الحساب"
                                        value={selectedLawyer.role_info?.name_ar || (selectedLawyer.role === 'manager' ? 'مدير' : selectedLawyer.role === 'lawyer' ? 'محامي' : 'مساعد')}
                                    />
                                    <DetailItem icon={<Award className="w-4 h-4" />} label="درجة الترخيص" value={selectedLawyer.lawyer_license_type} />
                                    <DetailItem icon={<Award className="w-4 h-4" />} label="رقم الترخيص" value={selectedLawyer.license_number} />
                                    <DetailItem icon={<MapPin className="w-4 h-4" />} label="النقابة" value={selectedLawyer.bar_association} />
                                    <DetailItem icon={<Languages className="w-4 h-4" />} label="اللغات" value={selectedLawyer.languages?.join(', ')} />
                                </div>
                            </div>

                            {/* Contact & Presence */}
                            <div>
                                <h3 className="text-sm font-bold text-purple-400 uppercase tracking-wider mb-4 border-r-2 border-purple-500 pr-2">معلومات التواصل والتواجد</h3>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-obsidian-800/30 rounded-xl p-4 border border-white/5">
                                    <DetailItem icon={<Mail className="w-4 h-4" />} label="البريد الإلكتروني" value={selectedLawyer.email} />
                                    <DetailItem icon={<Phone className="w-4 h-4" />} label="رقم الهاتف" value={selectedLawyer.phone} />
                                    <DetailItem icon={<Globe className="w-4 h-4" />} label="الموقع الإلكتروني" value={selectedLawyer.website} isLink />
                                    <DetailItem icon={<Linkedin className="w-4 h-4" />} label="لينكد إن" value={selectedLawyer.linkedin_profile} isLink />
                                </div>
                            </div>

                            {/* Office Info */}
                            <div>
                                <h3 className="text-sm font-bold text-purple-400 uppercase tracking-wider mb-4 border-r-2 border-purple-500 pr-2">معلومات المكتب</h3>
                                <div className="bg-obsidian-800/30 rounded-xl p-4 border border-white/5 space-y-3">
                                    <DetailItem icon={<MapPin className="w-4 h-4" />} label="العنوان" value={selectedLawyer.office_address} />
                                    <div className="grid grid-cols-2 gap-4">
                                        <DetailItem label="المدينة" value={selectedLawyer.office_city} />
                                        <DetailItem label="الرمز البريدي" value={selectedLawyer.office_postal_code} />
                                    </div>
                                </div>
                            </div>

                            {/* Bio */}
                            {selectedLawyer.bio && (
                                <div>
                                    <h3 className="text-sm font-bold text-purple-400 uppercase tracking-wider mb-3 border-r-2 border-purple-500 pr-2">النبذة الشخصية</h3>
                                    <p className="bg-obsidian-800/30 rounded-xl p-4 border border-white/5 text-gray-300 leading-relaxed italic">
                                        "{selectedLawyer.bio}"
                                    </p>
                                </div>
                            )}

                            {/* Registration Info */}
                            <div className="pt-4 text-xs text-gray-500 text-center">
                                تاريخ التسجيل: {new Date(selectedLawyer.created_at).toLocaleString('ar-SA')}
                            </div>
                        </div>
                    </motion.div>
                </div>
            )}
        </div>
    );
}

// Helper component for detail items
function DetailItem({ icon, label, value, isLink }: { icon?: React.ReactNode, label: string, value?: any, isLink?: boolean }) {
    if (!value) return null;

    return (
        <div className="space-y-1">
            <span className="text-[10px] text-gray-500 block">{label}</span>
            <div className="flex items-center gap-2 text-white text-sm">
                {icon && <span className="text-purple-400/70">{icon}</span>}
                {isLink ? (
                    <a href={value.startsWith('http') ? value : `https://${value}`} target="_blank" rel="noopener noreferrer" className="text-purple-400 hover:underline truncate">
                        {value}
                    </a>
                ) : (
                    <span className="truncate">{value}</span>
                )}
            </div>
        </div>
    );
}
