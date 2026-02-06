import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Plus, Users, Mail, Lock, UserCheck, UserX, Shield, Eye, EyeOff } from 'lucide-react'
import { apiClient } from '../api/client'
import { useAuth } from '../contexts/AuthContext'
import { toast } from 'sonner'
import { Trash2, AlertTriangle } from 'lucide-react'

interface Assistant {
    id: string
    email: string
    full_name: string
    phone: string | null
    is_active: boolean
    created_at: string
    role?: {
        name_ar: string
        permissions: any
    }
}

export function AssistantsPage() {
    const { getEffectiveLawyerId, isLawyer, isAdmin } = useAuth()
    const [assistants, setAssistants] = useState<Assistant[]>([])
    const [loading, setLoading] = useState(true)
    const [showCreateModal, setShowCreateModal] = useState(false)
    const [limit, setLimit] = useState<{ current_count: number, max_limit: number } | null>(null)
    const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null)

    useEffect(() => {
        if (isLawyer || isAdmin) {
            fetchAssistants()
            fetchLimit()
        }
    }, [isLawyer, isAdmin])

    const fetchLimit = async () => {
        try {
            const data = await apiClient.get<any>('/api/assistants/limit')
            setLimit(data)
        } catch (error) {
            console.error('Error fetching limit:', error)
        }
    }

    const fetchAssistants = async () => {
        const lawyerId = getEffectiveLawyerId()
        if (!lawyerId) return

        try {
            setLoading(true)
            const data = await apiClient.get<Assistant[]>('/api/assistants')
            setAssistants(data || [])
        } catch (error) {
            console.error('Error fetching assistants:', error)
            toast.error('فشل تحميل المساعدين')
        } finally {
            setLoading(false)
        }
    }

    const toggleAssistantStatus = async (assistantId: string, currentStatus: boolean) => {
        try {
            await apiClient.put(`/api/assistants/${assistantId}/toggle-status`, {
                is_active: !currentStatus
            })

            toast.success(!currentStatus ? 'تم تفعيل المساعد' : 'تم تعطيل المساعد')
            fetchAssistants()
        } catch (error) {
            toast.error('فشل تحديث حالة المساعد')
        }
    }

    const deleteAssistant = async (id: string) => {
        try {
            await apiClient.delete(`/api/assistants/${id}`)
            toast.success('تم حذف المساعد بنجاح')
            setShowDeleteConfirm(null)
            fetchAssistants()
            fetchLimit()
        } catch (error) {
            toast.error('فشل حذف المساعد')
        }
    }

    // المحامون والآدمن فقط يمكنهم الوصول
    if (!isLawyer && !isAdmin) {
        return (
            <div className="text-center py-12">
                <Shield className="w-16 h-16 text-red-500 mx-auto mb-4" />
                <h3 className="text-xl font-bold text-white mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                    غير مصرح
                </h3>
                <p className="text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>
                    هذه الصفحة للمحامين والمشرفين فقط
                </p>
            </div>
        )
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-gold-500" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        المساعدون
                    </h1>
                    <p className="text-gray-400 text-sm mt-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        إدارة المساعدين في مكتبك
                    </p>
                </div>
                <button
                    onClick={() => setShowCreateModal(true)}
                    className="flex items-center gap-2 px-6 py-3 bg-transparent border-2 border-gold-500 text-white font-bold rounded-lg hover:bg-gold-500/10 transition-all"
                    style={{ fontFamily: 'Cairo, sans-serif' }}
                >
                    <Plus className="w-5 h-5" />
                    <span>إضافة مساعد</span>
                </button>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="backdrop-blur-xl bg-obsidian-800/70 border border-gold-500/20 rounded-xl p-6">
                    <h3 className="text-gray-400 text-sm mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>إجمالي المساعدين</h3>
                    <div className="flex items-baseline gap-2">
                        <p className="text-4xl font-bold text-white">{assistants.length}</p>
                        {limit && (
                            <p className="text-gray-500 text-lg">/ {limit.max_limit}</p>
                        )}
                    </div>
                </div>
                <div className="backdrop-blur-xl bg-obsidian-800/70 border border-green-500/20 rounded-xl p-6">
                    <h3 className="text-gray-400 text-sm mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>نشط</h3>
                    <p className="text-4xl font-bold text-green-400">
                        {assistants.filter(a => a.is_active).length}
                    </p>
                </div>
                <div className="backdrop-blur-xl bg-obsidian-800/70 border border-red-500/20 rounded-xl p-6">
                    <h3 className="text-gray-400 text-sm mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>معطل</h3>
                    <p className="text-4xl font-bold text-red-400">
                        {assistants.filter(a => !a.is_active).length}
                    </p>
                </div>
            </div>

            {/* Assistants List */}
            {loading ? (
                <div className="text-center py-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gold-500 mx-auto"></div>
                </div>
            ) : assistants.length === 0 ? (
                <div className="text-center py-12 backdrop-blur-xl bg-obsidian-800/50 border border-gold-500/20 rounded-xl">
                    <Users className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                    <h3 className="text-xl font-bold text-gray-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        لا يوجد مساعدين
                    </h3>
                    <p className="text-gray-500" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        قم بإضافة مساعد جديد للبدء
                    </p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {assistants.map((assistant, index) => (
                        <motion.div
                            key={assistant.id}
                            initial={{ opacity: 1, y: 0 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: index * 0.05 }}
                            className="backdrop-blur-xl bg-obsidian-800/70 border border-gold-500/20 rounded-xl p-6"
                        >
                            {/* Header */}
                            <div className="flex items-start justify-between mb-4">
                                <div className="flex-1">
                                    <h3 className="text-xl font-bold text-white mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                        {assistant.full_name}
                                    </h3>
                                    <span className={`inline-flex items-center gap-1 px-2 py-1 text-xs rounded-full ${assistant.is_active
                                        ? 'bg-green-500/20 text-green-400'
                                        : 'bg-red-500/20 text-red-400'
                                        }`}>
                                        {assistant.is_active ? <UserCheck className="w-3 h-3" /> : <UserX className="w-3 h-3" />}
                                        <span style={{ fontFamily: 'Cairo, sans-serif' }}>
                                            {assistant.is_active ? 'نشط' : 'معطل'}
                                        </span>
                                    </span>
                                </div>
                            </div>

                            {/* Info */}
                            <div className="space-y-2 mb-4">
                                <div className="flex items-center gap-2 text-gray-300">
                                    <Mail className="w-4 h-4 text-gray-500" />
                                    <span className="text-sm" style={{ fontFamily: 'Cairo, sans-serif' }}>{assistant.email}</span>
                                </div>
                                {assistant.phone && (
                                    <div className="flex items-center gap-2 text-gray-300">
                                        <span className="text-sm" style={{ fontFamily: 'Cairo, sans-serif' }}>{assistant.phone}</span>
                                    </div>
                                )}
                            </div>

                            {/* Actions */}
                            <div className="flex gap-2 pt-4 border-t border-gold-500/10">
                                <button
                                    onClick={() => toggleAssistantStatus(assistant.id, assistant.is_active)}
                                    className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors ${assistant.is_active
                                        ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30'
                                        : 'bg-green-500/20 text-green-400 hover:bg-green-500/30'
                                        }`}
                                    style={{ fontFamily: 'Cairo, sans-serif' }}
                                >
                                    {assistant.is_active ? 'تعطيل' : 'تفعيل'}
                                </button>
                                <button
                                    onClick={() => setShowDeleteConfirm(assistant.id)}
                                    className="p-2 bg-red-500/10 text-red-500 rounded-lg hover:bg-red-500/20 transition-colors"
                                    title="حذف المساعد"
                                >
                                    <Trash2 className="w-5 h-5" />
                                </button>
                            </div>
                        </motion.div>
                    ))}
                </div>
            )}

            {/* Delete Confirmation Modal */}
            {showDeleteConfirm && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[60] p-4">
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="backdrop-blur-xl bg-obsidian-800/95 border border-red-500/30 rounded-2xl p-8 max-w-sm w-full text-center"
                    >
                        <div className="w-16 h-16 bg-red-500/10 rounded-full flex items-center justify-center mx-auto mb-4">
                            <AlertTriangle className="w-8 h-8 text-red-500" />
                        </div>
                        <h2 className="text-xl font-bold text-white mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            تأكيد الحذف
                        </h2>
                        <p className="text-gray-400 mb-6" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            هل أنت متأكد من رغبتك في حذف هذا المساعد؟ لا يمكن التراجع عن هذا الإجراء وسيتم حذف جميع بيانات الدخول الخاصة به.
                        </p>
                        <div className="flex gap-3">
                            <button
                                onClick={() => deleteAssistant(showDeleteConfirm)}
                                className="flex-1 px-6 py-3 bg-red-500 text-white font-bold rounded-lg hover:bg-red-600 transition-colors"
                                style={{ fontFamily: 'Cairo, sans-serif' }}
                            >
                                حذف
                            </button>
                            <button
                                onClick={() => setShowDeleteConfirm(null)}
                                className="flex-1 px-6 py-3 bg-obsidian-700 text-white rounded-lg hover:bg-obsidian-600 transition-colors"
                                style={{ fontFamily: 'Cairo, sans-serif' }}
                            >
                                إلغاء
                            </button>
                        </div>
                    </motion.div>
                </div>
            )}

            {/* Create Modal */}
            {showCreateModal && (
                <CreateAssistantModal
                    onClose={() => setShowCreateModal(false)}
                    onSuccess={() => {
                        setShowCreateModal(false)
                        fetchAssistants()
                    }}
                />
            )}
        </div>
    )
}

// Create Assistant Modal
interface CreateAssistantModalProps {
    onClose: () => void
    onSuccess: () => void
}

function CreateAssistantModal({ onClose, onSuccess }: CreateAssistantModalProps) {
    const { getEffectiveLawyerId } = useAuth()
    const [loading, setLoading] = useState(false)
    const [showPassword, setShowPassword] = useState(false)
    const [formData, setFormData] = useState({
        email: '',
        password: '',
        full_name: '',
        phone: ''
    })

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()

        if (!formData.email || !formData.password || !formData.full_name) {
            toast.error('الإيميل والاسم وكلمة السر مطلوبة')
            return
        }

        const lawyerId = getEffectiveLawyerId()
        if (!lawyerId) {
            toast.error('خطأ في تحديد المكتب')
            return
        }

        setLoading(true)

        try {
            // ✅ FIXED: استخدام apiClient بدلاً من fetch المباشر
            await apiClient.post('/api/assistants/create', {
                email: formData.email,
                password: formData.password,
                full_name: formData.full_name,
                phone: formData.phone || null,
                office_id: lawyerId
            })

            toast.success('تم إضافة المساعد بنجاح')
            onSuccess()
        } catch (error: any) {
            console.error('Error creating assistant:', error)
            toast.error(error.message || 'فشل إضافة المساعد')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="backdrop-blur-xl bg-obsidian-800/90 border border-gold-500/20 rounded-2xl p-8 max-w-md w-full"
            >
                <h2 className="text-2xl font-bold text-gold-500 mb-6" style={{ fontFamily: 'Cairo, sans-serif' }}>
                    إضافة مساعد جديد
                </h2>

                <form onSubmit={handleSubmit} className="space-y-4">
                    {/* Full Name */}
                    <div>
                        <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            الاسم الكامل <span className="text-red-400">*</span>
                        </label>
                        <input
                            type="text"
                            value={formData.full_name}
                            onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                            className="w-full px-4 py-3 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white"
                            style={{ fontFamily: 'Cairo, sans-serif' }}
                            required
                        />
                    </div>

                    {/* Email */}
                    <div>
                        <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            البريد الإلكتروني <span className="text-red-400">*</span>
                        </label>
                        <div className="relative">
                            <Mail className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                            <input
                                type="email"
                                value={formData.email}
                                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                                className="w-full pr-10 px-4 py-3 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white"
                                placeholder="assistant@example.com"
                                required
                            />
                        </div>
                    </div>

                    {/* Password */}
                    <div>
                        <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            كلمة السر <span className="text-red-400">*</span>
                        </label>
                        <div className="relative">
                            <Lock className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                            <input
                                type={showPassword ? 'text' : 'password'}
                                value={formData.password}
                                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                                className="w-full pr-10 pl-10 px-4 py-3 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white"
                                placeholder="••••••••"
                                required
                                minLength={6}
                            />
                            <button
                                type="button"
                                onClick={() => setShowPassword(!showPassword)}
                                className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white"
                            >
                                {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                            </button>
                        </div>
                        <p className="text-xs text-gray-500 mt-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            على الأقل 6 أحرف
                        </p>
                    </div>

                    {/* Phone */}
                    <div>
                        <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            رقم الهاتف
                        </label>
                        <input
                            type="tel"
                            value={formData.phone}
                            onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                            className="w-full px-4 py-3 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white"
                            placeholder="05xxxxxxxx"
                            style={{ fontFamily: 'Cairo, sans-serif' }}
                        />
                    </div>

                    {/* Buttons */}
                    <div className="flex gap-3 pt-4">
                        <button
                            type="submit"
                            disabled={loading}
                            className="flex-1 px-6 py-3 bg-transparent border-2 border-gold-500 text-white font-bold rounded-lg hover:bg-gold-500/10 disabled:opacity-50"
                            style={{ fontFamily: 'Cairo, sans-serif' }}
                        >
                            {loading ? 'جاري الإضافة...' : 'إضافة'}
                        </button>
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-6 py-3 bg-obsidian-700 text-white rounded-lg"
                            style={{ fontFamily: 'Cairo, sans-serif' }}
                        >
                            إلغاء
                        </button>
                    </div>
                </form>
            </motion.div>
        </div>
    )
}
