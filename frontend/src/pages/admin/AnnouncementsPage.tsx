import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
    Bell,
    Plus,
    Edit3,
    Trash2,
    Calendar,
    Users,
    AlertTriangle,
    Info,
    AlertCircle,
    Sparkles,
    Eye,
    EyeOff,
    Save
} from 'lucide-react';
import { getAnnouncements, createAnnouncement, updateAnnouncement, deleteAnnouncement, SystemAnnouncement } from '../../api/admin';
import { toast } from 'sonner';

const announcementTypes = [
    { value: 'info', label: 'معلومات', icon: Info, color: 'bg-blue-500/20 text-blue-400' },
    { value: 'warning', label: 'تحذير', icon: AlertTriangle, color: 'bg-yellow-500/20 text-yellow-400' },
    { value: 'critical', label: 'هام', icon: AlertCircle, color: 'bg-red-500/20 text-red-400' },
    { value: 'feature', label: 'ميزة جديدة', icon: Sparkles, color: 'bg-green-500/20 text-green-400' }
];

const targetOptions = [
    { value: 'all', label: 'الجميع' },
    { value: 'lawyers', label: 'المحامين فقط' },
    { value: 'assistants', label: 'المساعدين فقط' }
];

export default function AnnouncementsPage() {
    const [announcements, setAnnouncements] = useState<SystemAnnouncement[]>([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [editingAnnouncement, setEditingAnnouncement] = useState<SystemAnnouncement | null>(null);
    const [formData, setFormData] = useState({
        title: '',
        content: '',
        announcement_type: 'info',
        target_audience: 'all',
        start_date: new Date().toISOString().slice(0, 16),
        end_date: '',
        is_active: true,
        is_dismissible: true,
        priority: 0
    });

    useEffect(() => {
        loadAnnouncements();
    }, []);

    const loadAnnouncements = async () => {
        try {
            setLoading(true);
            const data = await getAnnouncements();
            setAnnouncements(data);
        } catch (error) {
            console.error('Error loading announcements:', error);
            toast.error('فشل تحميل الإعلانات');
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async () => {
        if (!formData.title || !formData.content) {
            toast.error('يرجى ملء جميع الحقول المطلوبة');
            return;
        }

        try {
            const payload = {
                ...formData,
                start_date: formData.start_date || undefined,
                end_date: formData.end_date || undefined
            };

            if (editingAnnouncement) {
                await updateAnnouncement(editingAnnouncement.id, payload);
                toast.success('تم تحديث الإعلان');
            } else {
                await createAnnouncement(payload);
                toast.success('تم إنشاء الإعلان');
            }
            setShowModal(false);
            resetForm();
            loadAnnouncements();
        } catch (error) {
            console.error('Error saving announcement:', error);
            toast.error('فشل حفظ الإعلان');
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm('هل أنت متأكد من حذف هذا الإعلان؟')) return;

        try {
            await deleteAnnouncement(id);
            toast.success('تم حذف الإعلان');
            loadAnnouncements();
        } catch (error) {
            console.error('Error deleting announcement:', error);
            toast.error('فشل حذف الإعلان');
        }
    };

    const handleEdit = (announcement: SystemAnnouncement) => {
        setEditingAnnouncement(announcement);
        setFormData({
            title: announcement.title,
            content: announcement.content,
            announcement_type: announcement.announcement_type,
            target_audience: announcement.target_audience,
            start_date: announcement.start_date?.slice(0, 16) || '',
            end_date: announcement.end_date?.slice(0, 16) || '',
            is_active: announcement.is_active,
            is_dismissible: announcement.is_dismissible,
            priority: announcement.priority
        });
        setShowModal(true);
    };

    const resetForm = () => {
        setEditingAnnouncement(null);
        setFormData({
            title: '',
            content: '',
            announcement_type: 'info',
            target_audience: 'all',
            start_date: new Date().toISOString().slice(0, 16),
            end_date: '',
            is_active: true,
            is_dismissible: true,
            priority: 0
        });
    };

    const openCreateModal = () => {
        resetForm();
        setShowModal(true);
    };

    const getTypeInfo = (type: string) => {
        return announcementTypes.find(t => t.value === type) || announcementTypes[0];
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
                        <Bell className="w-7 h-7" />
                        الإعلانات والإشعارات
                    </h1>
                    <p className="text-gray-400 mt-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        إجمالي: {announcements.length} إعلان
                    </p>
                </div>
                <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={openCreateModal}
                    className="flex items-center gap-2 px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-all"
                    style={{ fontFamily: 'Cairo, sans-serif' }}
                >
                    <Plus className="w-5 h-5" />
                    إعلان جديد
                </motion.button>
            </div>

            {/* Announcements List */}
            {announcements.length === 0 ? (
                <div className="text-center py-12 backdrop-blur-xl bg-obsidian-800/50 border border-purple-500/20 rounded-xl">
                    <Bell className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                    <h3 className="text-xl font-bold text-gray-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        لا يوجد إعلانات
                    </h3>
                    <p className="text-gray-500" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        أنشئ إعلانًا جديدًا ليظهر للمستخدمين
                    </p>
                </div>
            ) : (
                <div className="space-y-4">
                    {announcements.map((announcement, index) => {
                        const typeInfo = getTypeInfo(announcement.announcement_type);
                        const TypeIcon = typeInfo.icon;

                        return (
                            <motion.div
                                key={announcement.id}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: index * 0.05 }}
                                className={`backdrop-blur-xl bg-obsidian-800/70 border rounded-xl p-6 ${announcement.is_active ? 'border-purple-500/30' : 'border-gray-600/30 opacity-60'
                                    }`}
                            >
                                <div className="flex items-start justify-between">
                                    <div className="flex items-start gap-4 flex-1">
                                        <div className={`p-3 rounded-lg ${typeInfo.color}`}>
                                            <TypeIcon className="w-6 h-6" />
                                        </div>
                                        <div className="flex-1">
                                            <div className="flex items-center gap-3 mb-2">
                                                <h3 className="text-lg font-bold text-white" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                                    {announcement.title}
                                                </h3>
                                                {!announcement.is_active && (
                                                    <span className="px-2 py-1 bg-gray-500/20 text-gray-400 rounded-full text-xs" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                                        غير نشط
                                                    </span>
                                                )}
                                            </div>
                                            <p className="text-gray-300 mb-3" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                                {announcement.content}
                                            </p>
                                            <div className="flex flex-wrap items-center gap-4 text-sm text-gray-500">
                                                <div className="flex items-center gap-1">
                                                    <Users className="w-4 h-4" />
                                                    <span style={{ fontFamily: 'Cairo, sans-serif' }}>
                                                        {targetOptions.find(t => t.value === announcement.target_audience)?.label || 'الجميع'}
                                                    </span>
                                                </div>
                                                <div className="flex items-center gap-1">
                                                    <Calendar className="w-4 h-4" />
                                                    <span>
                                                        {announcement.start_date ? new Date(announcement.start_date).toLocaleDateString('ar-SA') : 'بدون تاريخ'}
                                                    </span>
                                                </div>
                                                {announcement.end_date && (
                                                    <span className="text-gray-600">→ {new Date(announcement.end_date).toLocaleDateString('ar-SA')}</span>
                                                )}
                                            </div>
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-2">
                                        <button
                                            onClick={() => handleEdit(announcement)}
                                            className="p-2 text-gray-400 hover:text-purple-400 hover:bg-purple-500/10 rounded-lg transition-all"
                                        >
                                            <Edit3 className="w-5 h-5" />
                                        </button>
                                        <button
                                            onClick={() => handleDelete(announcement.id)}
                                            className="p-2 text-gray-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-all"
                                        >
                                            <Trash2 className="w-5 h-5" />
                                        </button>
                                    </div>
                                </div>
                            </motion.div>
                        );
                    })}
                </div>
            )}

            {/* Create/Edit Modal */}
            {showModal && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="backdrop-blur-xl bg-obsidian-800/95 border border-purple-500/20 rounded-2xl p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto"
                    >
                        <h2 className="text-2xl font-bold text-purple-500 mb-6" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            {editingAnnouncement ? 'تعديل الإعلان' : 'إعلان جديد'}
                        </h2>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-purple-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                    العنوان <span className="text-red-400">*</span>
                                </label>
                                <input
                                    type="text"
                                    value={formData.title}
                                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                                    className="w-full px-4 py-3 bg-obsidian-900/50 border border-purple-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors"
                                    style={{ fontFamily: 'Cairo, sans-serif' }}
                                    placeholder="عنوان الإعلان"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-purple-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                    المحتوى <span className="text-red-400">*</span>
                                </label>
                                <textarea
                                    value={formData.content}
                                    onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                                    rows={4}
                                    className="w-full px-4 py-3 bg-obsidian-900/50 border border-purple-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors resize-none"
                                    style={{ fontFamily: 'Cairo, sans-serif' }}
                                    placeholder="محتوى الإعلان..."
                                />
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-purple-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                        النوع
                                    </label>
                                    <select
                                        value={formData.announcement_type}
                                        onChange={(e) => setFormData({ ...formData, announcement_type: e.target.value })}
                                        className="w-full px-4 py-3 bg-obsidian-900/50 border border-purple-500/20 rounded-lg text-white focus:outline-none focus:border-purple-500 transition-colors"
                                        style={{ fontFamily: 'Cairo, sans-serif' }}
                                    >
                                        {announcementTypes.map(type => (
                                            <option key={type.value} value={type.value}>{type.label}</option>
                                        ))}
                                    </select>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-purple-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                        الجمهور المستهدف
                                    </label>
                                    <select
                                        value={formData.target_audience}
                                        onChange={(e) => setFormData({ ...formData, target_audience: e.target.value })}
                                        className="w-full px-4 py-3 bg-obsidian-900/50 border border-purple-500/20 rounded-lg text-white focus:outline-none focus:border-purple-500 transition-colors"
                                        style={{ fontFamily: 'Cairo, sans-serif' }}
                                    >
                                        {targetOptions.map(opt => (
                                            <option key={opt.value} value={opt.value}>{opt.label}</option>
                                        ))}
                                    </select>
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-purple-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                        تاريخ البدء
                                    </label>
                                    <input
                                        type="datetime-local"
                                        value={formData.start_date}
                                        onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                                        className="w-full px-4 py-3 bg-obsidian-900/50 border border-purple-500/20 rounded-lg text-white focus:outline-none focus:border-purple-500 transition-colors"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-purple-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                        تاريخ الانتهاء
                                    </label>
                                    <input
                                        type="datetime-local"
                                        value={formData.end_date}
                                        onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                                        className="w-full px-4 py-3 bg-obsidian-900/50 border border-purple-500/20 rounded-lg text-white focus:outline-none focus:border-purple-500 transition-colors"
                                    />
                                </div>
                            </div>

                            <div className="flex items-center gap-6">
                                <label className="flex items-center gap-2 cursor-pointer">
                                    <input
                                        type="checkbox"
                                        checked={formData.is_active}
                                        onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                                        className="w-5 h-5 rounded border-purple-500/30 bg-obsidian-900/50 text-purple-500 focus:ring-purple-500"
                                    />
                                    <span className="text-sm text-gray-300" style={{ fontFamily: 'Cairo, sans-serif' }}>نشط</span>
                                </label>

                                <label className="flex items-center gap-2 cursor-pointer">
                                    <input
                                        type="checkbox"
                                        checked={formData.is_dismissible}
                                        onChange={(e) => setFormData({ ...formData, is_dismissible: e.target.checked })}
                                        className="w-5 h-5 rounded border-purple-500/30 bg-obsidian-900/50 text-purple-500 focus:ring-purple-500"
                                    />
                                    <span className="text-sm text-gray-300" style={{ fontFamily: 'Cairo, sans-serif' }}>يمكن إغلاقه</span>
                                </label>
                            </div>

                            <div className="flex gap-3 pt-4">
                                <motion.button
                                    whileHover={{ scale: 1.02 }}
                                    whileTap={{ scale: 0.98 }}
                                    onClick={handleSubmit}
                                    className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-all"
                                    style={{ fontFamily: 'Cairo, sans-serif' }}
                                >
                                    <Save className="w-5 h-5" />
                                    {editingAnnouncement ? 'حفظ التعديلات' : 'إنشاء الإعلان'}
                                </motion.button>
                                <button
                                    onClick={() => setShowModal(false)}
                                    className="px-6 py-3 bg-obsidian-700 text-white rounded-lg hover:bg-obsidian-600 transition-colors"
                                    style={{ fontFamily: 'Cairo, sans-serif' }}
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
