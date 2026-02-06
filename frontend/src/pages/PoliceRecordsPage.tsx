
import { useState, useEffect } from 'react'
import { apiClient } from '../api/client'
import { toast } from 'sonner'
import {
    Plus, Search, Filter, FileText, Trash2, Edit, AlertCircle, Eye, Paperclip
} from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { useBreadcrumb } from '../contexts/BreadcrumbContext'
import { motion, AnimatePresence } from 'framer-motion'

interface PoliceRecord {
    id: string
    record_number: string
    record_year: string
    record_type: string
    police_station: string
    complainant_name: string
    accused_name: string
    subject: string
    decision: string
    created_at: string
    case_id: string | null
    file_url: string | null
    ai_analysis: string | null
    case?: {
        case_number: string
    }
}

export function PoliceRecordsPage() {
    const { getEffectiveLawyerId } = useAuth()
    const { setPageTitle } = useBreadcrumb()
    const [records, setRecords] = useState<PoliceRecord[]>([])
    const [loading, setLoading] = useState(true)
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
    const [isEditModalOpen, setIsEditModalOpen] = useState(false)
    const [selectedRecord, setSelectedRecord] = useState<PoliceRecord | null>(null)
    const [searchQuery, setSearchQuery] = useState('')

    // Form States
    const [formData, setFormData] = useState({
        record_number: '',
        record_year: new Date().getFullYear().toString(),
        record_type: '',
        police_station: '',
        complainant_name: '',
        accused_name: '',
        subject: '',
        decision: ''
    })

    useEffect(() => {
        setPageTitle('محاضر الشرطة')
        fetchRecords()
    }, [])

    const fetchRecords = async () => {
        try {
            // ✅ BFF Pattern: استخدام apiClient - Backend يتولى فلترة lawyer_id
            const params = searchQuery ? `?search=${encodeURIComponent(searchQuery)}` : ''
            const data = await apiClient.get<PoliceRecord[]>(`/api/police-records${params}`)
            setRecords(data || [])
        } catch (error) {
            console.error('Error fetching records:', error)
            toast.error('فشل تحميل المحاضر')
        } finally {
            setLoading(false)
        }
    }

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault()
        try {
            // ✅ BFF Pattern: Backend يتولى تعيين user_id من JWT وتسجيل التدقيق
            await apiClient.post('/api/police-records', formData)

            toast.success('تم إضافة المحضر بنجاح')
            setIsCreateModalOpen(false)
            setFormData({
                record_number: '',
                record_year: new Date().getFullYear().toString(),
                record_type: '',
                police_station: '',
                complainant_name: '',
                accused_name: '',
                subject: '',
                decision: ''
            })
            fetchRecords()
        } catch (error) {
            console.error('Error creating record:', error)
            toast.error('فشل حفظ المحضر')
        }
    }

    const handleUpdate = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!selectedRecord) return

        try {
            // ✅ BFF Pattern: Backend يتولى التحقق من الملكية وتسجيل التدقيق
            await apiClient.put(`/api/police-records/${selectedRecord.id}`, formData)

            toast.success('تم تحديث المحضر بنجاح')
            setIsEditModalOpen(false)
            fetchRecords()
        } catch (error) {
            console.error('Error updating record:', error)
            toast.error('فشل تحديث المحضر')
        }
    }

    const handleDelete = async (id: string) => {
        if (!confirm('هل أنت متأكد من حذف هذا المحضر؟')) return

        try {
            // ✅ BFF Pattern: Backend يتولى التحقق من الملكية وتسجيل التدقيق
            await apiClient.delete(`/api/police-records/${id}`)

            toast.success('تم حذف المحضر')
            fetchRecords()
        } catch (error) {
            console.error('Error deleting record:', error)
            toast.error('فشل حذف المحضر')
        }
    }

    const openEditModal = (record: PoliceRecord) => {
        setSelectedRecord(record)
        setFormData({
            record_number: record.record_number,
            record_year: record.record_year || '',
            record_type: record.record_type || '',
            police_station: record.police_station || '',
            complainant_name: record.complainant_name || '',
            accused_name: record.accused_name || '',
            subject: record.subject || '',
            decision: record.decision || ''
        })
        setIsEditModalOpen(true)
    }

    return (
        <div className="space-y-6 p-6">
            {/* Header */}
            <div className="flex justify-between items-center">
                <h1 className="text-3xl font-bold bg-gradient-to-l from-gold-400 to-gold-600 bg-clip-text text-transparent">
                    محاضر الشرطة
                </h1>
                <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => setIsCreateModalOpen(true)}
                    className="flex items-center gap-2 bg-gradient-to-r from-cobalt-600 to-cobalt-500 text-white px-4 py-2 rounded-lg shadow-lg hover:shadow-cobalt-500/25 transition-all"
                >
                    <Plus className="w-5 h-5" />
                    <span>إضافة محضر جديد</span>
                </motion.button>
            </div>

            {/* Filters */}
            <div className="flex gap-4 mb-6">
                <div className="relative flex-1">
                    <Search className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
                    <input
                        type="text"
                        placeholder="بحث برقم المحضر، القسم، أو الأسماء..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && fetchRecords()}
                        className="w-full bg-obsidian-800 border-2 border-obsidian-700/50 rounded-xl py-2 pr-10 pl-4 text-gray-200 placeholder-gray-500 focus:border-gold-500/50 focus:outline-none transition-all"
                    />
                </div>
                <button
                    onClick={() => fetchRecords()}
                    className="bg-obsidian-800 border border-obsidian-700 text-gray-300 px-4 py-2 rounded-xl hover:bg-obsidian-700"
                >
                    <Filter className="w-5 h-5" />
                </button>
            </div>

            {/* Records Grid */}
            {loading ? (
                <div className="text-center py-12 text-gray-500">جاري التحميل...</div>
            ) : records.length === 0 ? (
                <div className="text-center py-12 bg-obsidian-800/30 rounded-2xl border border-dashed border-gray-700">
                    <FileText className="w-16 h-16 mx-auto text-gray-600 mb-4" />
                    <h3 className="text-xl font-bold text-gray-400">لا توجد محاضر مسجلة</h3>
                    <p className="text-gray-500 mt-2">ابدأ بإضافة أول محضر شرطة</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {records.map(record => (
                        <motion.div
                            key={record.id}
                            initial={{ opacity: 1, y: 0 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="glass-card p-5 group relative overflow-hidden"
                        >
                            {/* Decorative Top Border */}
                            <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-red-500/50 to-transparent opacity-50" />

                            <div className="flex justify-between items-start mb-4">
                                <div>
                                    <div className="flex items-center gap-2">
                                        <span className="text-xs font-mono bg-red-500/10 text-red-400 px-2 py-1 rounded">
                                            {record.record_type || 'محضر'}
                                        </span>
                                        <h3 className="text-lg font-bold text-gray-100">
                                            {record.record_number} لسنة {record.record_year}
                                        </h3>
                                    </div>
                                    <p className="text-sm text-gray-400 mt-1 flex items-center gap-1">
                                        <AlertCircle className="w-3 h-3" />
                                        {record.police_station}
                                    </p>
                                </div>
                                <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                    <button
                                        onClick={() => openEditModal(record)}
                                        className="p-2 hover:bg-blue-500/20 text-blue-400 rounded-lg transition-colors"
                                    >
                                        <Edit className="w-4 h-4" />
                                    </button>
                                    <button
                                        onClick={() => handleDelete(record.id)}
                                        className="p-2 hover:bg-red-500/20 text-red-400 rounded-lg transition-colors"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                </div>
                            </div>

                            <div className="space-y-3">
                                <div className="flex justify-between text-sm py-2 border-b border-gray-800">
                                    <span className="text-gray-500">الشاكي:</span>
                                    <span className="text-gray-200">{record.complainant_name}</span>
                                </div>
                                <div className="flex justify-between text-sm py-2 border-b border-gray-800">
                                    <span className="text-gray-500">المشكو في حقه:</span>
                                    <span className="text-gray-200">{record.accused_name}</span>
                                </div>
                                {record.subject && (
                                    <div className="text-sm bg-obsidian-900/50 p-3 rounded-lg border border-gray-800">
                                        <p className="text-gray-400 line-clamp-2">{record.subject}</p>
                                    </div>
                                )}
                                {record.case && (
                                    <div className="flex items-center gap-2 text-xs text-gold-500 mt-2">
                                        <Paperclip className="w-3 h-3" />
                                        مرتبط بالقضية رقم: {record.case.case_number}
                                    </div>
                                )}
                            </div>
                        </motion.div>
                    ))}
                </div>
            )}

            {/* Create Modal */}
            <AnimatePresence>
                {isCreateModalOpen && (
                    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.95 }}
                            className="bg-obsidian-900 border border-gray-700 rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl"
                        >
                            <div className="p-6 border-b border-gray-800 flex justify-between items-center">
                                <h2 className="text-xl font-bold text-white">إضافة محضر جديد</h2>
                                <button onClick={() => setIsCreateModalOpen(false)} className="text-gray-400 hover:text-white">✕</button>
                            </div>
                            <form onSubmit={handleCreate} className="p-6 space-y-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm text-gray-400 mb-1">رقم المحضر</label>
                                        <input required type="text" value={formData.record_number} onChange={e => setFormData({ ...formData, record_number: e.target.value })} className="w-full bg-obsidian-800 border border-gray-700 rounded-lg p-2 text-white" />
                                    </div>
                                    <div>
                                        <label className="block text-sm text-gray-400 mb-1">السنة</label>
                                        <input type="text" value={formData.record_year} onChange={e => setFormData({ ...formData, record_year: e.target.value })} className="w-full bg-obsidian-800 border border-gray-700 rounded-lg p-2 text-white" />
                                    </div>
                                    <div>
                                        <label className="block text-sm text-gray-400 mb-1">نوع المحضر</label>
                                        <input type="text" placeholder="إداري، جنح..." value={formData.record_type} onChange={e => setFormData({ ...formData, record_type: e.target.value })} className="w-full bg-obsidian-800 border border-gray-700 rounded-lg p-2 text-white" />
                                    </div>
                                    <div>
                                        <label className="block text-sm text-gray-400 mb-1">القسم / المركز</label>
                                        <input type="text" value={formData.police_station} onChange={e => setFormData({ ...formData, police_station: e.target.value })} className="w-full bg-obsidian-800 border border-gray-700 rounded-lg p-2 text-white" />
                                    </div>
                                    <div>
                                        <label className="block text-sm text-gray-400 mb-1">الشاكي</label>
                                        <input type="text" value={formData.complainant_name} onChange={e => setFormData({ ...formData, complainant_name: e.target.value })} className="w-full bg-obsidian-800 border border-gray-700 rounded-lg p-2 text-white" />
                                    </div>
                                    <div>
                                        <label className="block text-sm text-gray-400 mb-1">المشكو في حقه</label>
                                        <input type="text" value={formData.accused_name} onChange={e => setFormData({ ...formData, accused_name: e.target.value })} className="w-full bg-obsidian-800 border border-gray-700 rounded-lg p-2 text-white" />
                                    </div>
                                </div>
                                <div>
                                    <label className="block text-sm text-gray-400 mb-1">الموضوع</label>
                                    <textarea rows={3} value={formData.subject} onChange={e => setFormData({ ...formData, subject: e.target.value })} className="w-full bg-obsidian-800 border border-gray-700 rounded-lg p-2 text-white" />
                                </div>
                                <div>
                                    <label className="block text-sm text-gray-400 mb-1">القرار</label>
                                    <textarea rows={3} placeholder="قرار النيابة أو الشرطة..." value={formData.decision} onChange={e => setFormData({ ...formData, decision: e.target.value })} className="w-full bg-obsidian-800 border border-gray-700 rounded-lg p-2 text-white" />
                                </div>
                                <div className="flex justify-end gap-3 mt-6">
                                    <button type="button" onClick={() => setIsCreateModalOpen(false)} className="px-4 py-2 text-gray-400 hover:text-white">إلغاء</button>
                                    <button type="submit" className="bg-gold-500 hover:bg-gold-600 text-black font-bold px-6 py-2 rounded-lg">حفظ</button>
                                </div>
                            </form>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>

            {/* Edit Modal */}
            <AnimatePresence>
                {isEditModalOpen && (
                    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.95 }}
                            className="bg-obsidian-900 border border-gray-700 rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl"
                        >
                            <div className="p-6 border-b border-gray-800 flex justify-between items-center">
                                <h2 className="text-xl font-bold text-white">تعديل المحضر</h2>
                                <button onClick={() => setIsEditModalOpen(false)} className="text-gray-400 hover:text-white">✕</button>
                            </div>
                            <form onSubmit={handleUpdate} className="p-6 space-y-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm text-gray-400 mb-1">رقم المحضر</label>
                                        <input required type="text" value={formData.record_number} onChange={e => setFormData({ ...formData, record_number: e.target.value })} className="w-full bg-obsidian-800 border border-gray-700 rounded-lg p-2 text-white" />
                                    </div>
                                    <div>
                                        <label className="block text-sm text-gray-400 mb-1">السنة</label>
                                        <input type="text" value={formData.record_year} onChange={e => setFormData({ ...formData, record_year: e.target.value })} className="w-full bg-obsidian-800 border border-gray-700 rounded-lg p-2 text-white" />
                                    </div>
                                    <div>
                                        <label className="block text-sm text-gray-400 mb-1">نوع المحضر</label>
                                        <input type="text" value={formData.record_type} onChange={e => setFormData({ ...formData, record_type: e.target.value })} className="w-full bg-obsidian-800 border border-gray-700 rounded-lg p-2 text-white" />
                                    </div>
                                    <div>
                                        <label className="block text-sm text-gray-400 mb-1">القسم / المركز</label>
                                        <input type="text" value={formData.police_station} onChange={e => setFormData({ ...formData, police_station: e.target.value })} className="w-full bg-obsidian-800 border border-gray-700 rounded-lg p-2 text-white" />
                                    </div>
                                    <div>
                                        <label className="block text-sm text-gray-400 mb-1">الشاكي</label>
                                        <input type="text" value={formData.complainant_name} onChange={e => setFormData({ ...formData, complainant_name: e.target.value })} className="w-full bg-obsidian-800 border border-gray-700 rounded-lg p-2 text-white" />
                                    </div>
                                    <div>
                                        <label className="block text-sm text-gray-400 mb-1">المشكو في حقه</label>
                                        <input type="text" value={formData.accused_name} onChange={e => setFormData({ ...formData, accused_name: e.target.value })} className="w-full bg-obsidian-800 border border-gray-700 rounded-lg p-2 text-white" />
                                    </div>
                                </div>
                                <div>
                                    <label className="block text-sm text-gray-400 mb-1">الموضوع</label>
                                    <textarea rows={3} value={formData.subject} onChange={e => setFormData({ ...formData, subject: e.target.value })} className="w-full bg-obsidian-800 border border-gray-700 rounded-lg p-2 text-white" />
                                </div>
                                <div>
                                    <label className="block text-sm text-gray-400 mb-1">القرار</label>
                                    <textarea rows={3} placeholder="قرار النيابة أو الشرطة..." value={formData.decision} onChange={e => setFormData({ ...formData, decision: e.target.value })} className="w-full bg-obsidian-800 border border-gray-700 rounded-lg p-2 text-white" />
                                </div>
                                <div className="flex justify-end gap-3 mt-6">
                                    <button type="button" onClick={() => setIsEditModalOpen(false)} className="px-4 py-2 text-gray-400 hover:text-white">إلغاء</button>
                                    <button type="submit" className="bg-gold-500 hover:bg-gold-600 text-black font-bold px-6 py-2 rounded-lg">حفظ التغييرات</button>
                                </div>
                            </form>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>
        </div>
    )
}
