import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Plus, Search, Phone, Mail, MapPin, FileText, Scale, User, ChevronLeft, ChevronRight } from 'lucide-react'
import { apiClient } from '../api/client'
import { useAuth } from '../contexts/AuthContext'
import { useBreadcrumb } from '../contexts/BreadcrumbContext'
import { toast } from 'sonner'
import { useAuditLog } from '../hooks/useAuditLog'
import { useInfiniteScroll } from '../hooks/useInfiniteScroll' // ✅ Import

interface Client {
    id: string
    lawyer_id: string
    full_name: string
    email: string | null
    phone: string | null
    national_id: string | null
    address: string | null
    notes: string | null
    has_power_of_attorney: boolean
    power_of_attorney_number: string | null
    power_of_attorney_image_url: string | null
    created_at: string
    updated_at: string
}

const CLIENTS_PER_PAGE = 12

export function ClientsPage() {
    const navigate = useNavigate()
    const { getEffectiveLawyerId } = useAuth()
    const { setPageTitle } = useBreadcrumb()
    const { logAction } = useAuditLog()
    const [searchQuery, setSearchQuery] = useState('')
    const [showCreateModal, setShowCreateModal] = useState(false)

    // ✅ Use Infinite Scroll Hook
    const {
        data: clients,
        loading,
        hasMore,
        loadMore,
        refresh,
        setParams,
        total
    } = useInfiniteScroll<Client>({
        endpoint: '/api/clients',
        limit: 12,
        initialParams: {}
    })

    // Update params when search changes
    useEffect(() => {
        setParams({
            search: searchQuery || undefined
        })
    }, [searchQuery, setParams])

    useEffect(() => {
        setPageTitle('الموكلون')
    }, [setPageTitle])


    // ✅ Observer
    const observer = useRef<IntersectionObserver | null>(null)
    const lastClientElementRef = useCallback((node: HTMLDivElement | null) => {
        if (loading) return
        if (observer.current) observer.current.disconnect()

        observer.current = new IntersectionObserver(entries => {
            if (entries[0].isIntersecting && hasMore) {
                loadMore()
            }
        })

        if (node) observer.current.observe(node)
    }, [loading, hasMore, loadMore])


    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <h1 className="text-3xl font-bold text-gold-500" style={{ fontFamily: 'Cairo, sans-serif' }}>
                    الموكلون
                </h1>
                <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => setShowCreateModal(true)}
                    className="flex items-center gap-2 px-6 py-3 bg-transparent border-2 border-gold-500 text-white font-bold rounded-lg hover:bg-gold-500/10 transition-all"
                    style={{ fontFamily: 'Cairo, sans-serif' }}
                >
                    <Plus className="w-5 h-5" />
                    <span>إضافة موكل جديد</span>
                </motion.button>
            </div>

            {/* Search Bar */}
            <div className="backdrop-blur-xl bg-obsidian-800/70 border border-gold-500/20 rounded-xl p-4">
                <div className="relative">
                    <Search className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="ابحث بالاسم، الهاتف، البريد، أو رقم الهوية..."
                        className="w-full pr-12 pl-4 py-3 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold-500 transition-colors"
                        style={{ fontFamily: 'Cairo, sans-serif' }}
                    />
                </div>
            </div>

            {/* Results Count */}
            {!loading && (
                <div className="text-sm text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>
                    عرض {clients.length} من {total} موكل
                </div>
            )}

            {/* Clients Grid */}
            {clients.length === 0 && !loading ? (
                <div className="text-center py-12 backdrop-blur-xl bg-obsidian-800/50 border border-gold-500/20 rounded-xl">
                    <User className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                    <h3 className="text-xl font-bold text-gray-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        لا يوجد موكلين
                    </h3>
                    <p className="text-gray-500" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        {searchQuery ? 'جرب تعديل البحث' : 'ابدأ بإضافة موكل جديد'}
                    </p>
                </div>
            ) : (
                <>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {clients.map((client: Client, index: number) => (
                            <motion.div
                                key={client.id}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: index * 0.05 }}
                                ref={index === clients.length - 1 ? lastClientElementRef : null} // ✅ Attach Observer
                                onClick={() => navigate(`/clients/${client.id}`)}
                                className="backdrop-blur-xl bg-obsidian-800/70 border border-gold-500/20 rounded-xl p-6 hover:border-gold-500/50 transition-all cursor-pointer group"
                            >
                                {/* Header */}
                                <div className="flex items-start justify-between mb-4">
                                    <div className="flex-1">
                                        <h3 className="text-xl font-bold text-white group-hover:text-gold-500 transition-colors mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                            {client.full_name}
                                        </h3>
                                        {client.has_power_of_attorney && (
                                            <span className="inline-flex items-center gap-1 px-2 py-1 bg-gold-500/20 text-gold-500 text-xs rounded-full">
                                                <Scale className="w-3 h-3" />
                                                <span style={{ fontFamily: 'Cairo, sans-serif' }}>موكّل</span>
                                            </span>
                                        )}
                                    </div>
                                </div>

                                {/* Contact Info */}
                                <div className="space-y-2 mb-4">
                                    {client.phone && (
                                        <div className="flex items-center gap-2 text-gray-300">
                                            <Phone className="w-4 h-4 text-gray-500" />
                                            <span className="text-sm" style={{ fontFamily: 'Cairo, sans-serif' }}>{client.phone}</span>
                                        </div>
                                    )}
                                    {client.email && (
                                        <div className="flex items-center gap-2 text-gray-300">
                                            <Mail className="w-4 h-4 text-gray-500" />
                                            <span className="text-sm" style={{ fontFamily: 'Cairo, sans-serif' }}>{client.email}</span>
                                        </div>
                                    )}
                                    {client.address && (
                                        <div className="flex items-center gap-2 text-gray-300">
                                            <MapPin className="w-4 h-4 text-gray-500" />
                                            <span className="text-sm line-clamp-1" style={{ fontFamily: 'Cairo, sans-serif' }}>{client.address}</span>
                                        </div>
                                    )}
                                </div>

                                {/* Footer */}
                                <div className="flex items-center justify-between pt-4 border-t border-gold-500/10">
                                    <span className="text-xs text-gray-500" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                        {new Date(client.created_at).toLocaleDateString('ar-EG')}
                                    </span>
                                    <button
                                        className="text-sm text-gold-500 hover:text-gold-400 font-medium flex items-center gap-1"
                                        style={{ fontFamily: 'Cairo, sans-serif' }}
                                    >
                                        <FileText className="w-4 h-4" />
                                        <span>عرض القضايا</span>
                                    </button>
                                </div>
                            </motion.div>
                        ))}
                    </div>
                </>
            )}

            {loading && (
                <div className="flex justify-center p-4">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gold-500"></div>
                </div>
            )}

            {/* Create Modal */}
            {showCreateModal && (
                <CreateClientModal
                    onClose={() => setShowCreateModal(false)}
                    onSuccess={() => {
                        setShowCreateModal(false)
                        refresh() // ✅ Refresh list
                    }}
                />
            )}
        </div>
    )
}

// Create Client Modal Component
interface CreateClientModalProps {
    onClose: () => void
    onSuccess: () => void
}

function CreateClientModal({ onClose, onSuccess }: CreateClientModalProps) {
    const { getEffectiveLawyerId } = useAuth()  // ✅ إضافة useAuth
    const [loading, setLoading] = useState(false)
    const [formData, setFormData] = useState({
        full_name: '',
        phone: '',
        email: '',
        national_id: '',
        address: '',
        occupation: '',
        notes: '',
        has_power_of_attorney: false,
        power_of_attorney_number: '',
        power_of_attorney_image_url: ''
    })



    const { logAction } = useAuditLog() // ✅

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()

        if (!formData.full_name) {
            toast.error('يرجى إدخال اسم الموكل')
            return
        }

        setLoading(true)

        try {
            const lawyerId = getEffectiveLawyerId() // ✅ استدعاء جديد داخل الدالة
            if (!lawyerId) {
                toast.error('تعذر تحديد هوية المحامي')
                return
            }

            // Create client via Backend API
            const payload = {
                full_name: formData.full_name,
                email: formData.email || null,
                phone: formData.phone || null,
                national_id: formData.national_id || null,
                address: formData.address || null,
                notes: formData.notes,
                has_power_of_attorney: formData.has_power_of_attorney,
                power_of_attorney_number: formData.power_of_attorney_number || null,
                power_of_attorney_image_url: formData.power_of_attorney_image_url || null
            }

            const response = await apiClient.post('/api/clients', payload)

            if (!response.success) throw new Error('Failed to create client')

            // Log action is handled by Backend usually? 
            // If we keep frontend logging, we need "data" from response.
            const newClient = response.client


            // ✅ تسجيل العملية - Optional if backend logs it, but keeping for now
            if (newClient) {
                await logAction(
                    'create',
                    'clients',
                    newClient.id,
                    null,
                    payload,
                    'إضافة موكل جديد'
                )
            }

            toast.success('تم إضافة الموكل بنجاح')
            onSuccess() // Keep onSuccess as it handles closing modal and fetching clients
            setFormData({
                full_name: '',
                email: '',
                phone: '',
                national_id: '',
                address: '',
                occupation: '', // Added back occupation
                notes: '', // Added back notes
                has_power_of_attorney: false,
                power_of_attorney_number: '',
                power_of_attorney_image_url: ''
            })
        } catch (error: any) {
            console.error('Error creating client:', error)
            toast.error('فشل إضافة الموكل')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="backdrop-blur-xl bg-obsidian-800/90 border border-gold-500/20 rounded-2xl p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto"
            >
                <h2 className="text-2xl font-bold text-gold-500 mb-6" style={{ fontFamily: 'Cairo, sans-serif' }}>
                    إضافة موكل جديد
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
                            className="w-full px-4 py-3 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold-500 transition-colors"
                            style={{ fontFamily: 'Cairo, sans-serif' }}
                            placeholder="أدخل الاسم الكامل"
                            required
                        />
                    </div>

                    {/* Phone and Email */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                رقم الهاتف
                            </label>
                            <input
                                type="tel"
                                value={formData.phone}
                                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                                className="w-full px-4 py-3 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold-500 transition-colors"
                                style={{ fontFamily: 'Cairo, sans-serif' }}
                                placeholder="05xxxxxxxx"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                البريد الإلكتروني
                            </label>
                            <input
                                type="email"
                                value={formData.email}
                                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                                className="w-full px-4 py-3 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold-500 transition-colors"
                                style={{ fontFamily: 'Cairo, sans-serif' }}
                                placeholder="example@email.com"
                            />
                        </div>
                    </div>

                    {/* National ID */}
                    <div>
                        <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            رقم الهوية
                        </label>
                        <input
                            type="text"
                            value={formData.national_id}
                            onChange={(e) => setFormData({ ...formData, national_id: e.target.value })}
                            className="w-full px-4 py-3 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold-500 transition-colors"
                            style={{ fontFamily: 'Cairo, sans-serif' }}
                            placeholder="1xxxxxxxxx"
                        />
                    </div>

                    {/* Address */}
                    <div>
                        <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            العنوان
                        </label>
                        <textarea
                            value={formData.address}
                            onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                            className="w-full px-4 py-3 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold-500 transition-colors resize-none"
                            style={{ fontFamily: 'Cairo, sans-serif' }}
                            placeholder="أدخل عنوان الموكل"
                            rows={2}
                        />
                    </div>

                    {/* Power of Attorney */}
                    <div className="border-t border-gold-500/20 pt-4">
                        <div className="flex items-center gap-3 mb-3">
                            <input
                                type="checkbox"
                                id="has_power_of_attorney"
                                checked={formData.has_power_of_attorney}
                                onChange={(e) => setFormData({ ...formData, has_power_of_attorney: e.target.checked })}
                                className="w-5 h-5 rounded border-gold-500/30 bg-obsidian-900/50 text-gold-500 focus:ring-gold-500 focus:ring-offset-0 cursor-pointer"
                            />
                            <label htmlFor="has_power_of_attorney" className="text-sm font-medium text-gold-500 cursor-pointer" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                يمتلك توكيل
                            </label>
                        </div>

                        {formData.has_power_of_attorney && (
                            <div className="space-y-3 pl-8">
                                <div>
                                    <label className="block text-sm font-medium text-gray-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                        رقم التوكيل
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.power_of_attorney_number}
                                        onChange={(e) => setFormData({ ...formData, power_of_attorney_number: e.target.value })}
                                        className="w-full px-4 py-2 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold-500 transition-colors text-sm"
                                        style={{ fontFamily: 'Cairo, sans-serif' }}
                                        placeholder="أدخل رقم التوكيل"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                        رابط صورة التوكيل
                                    </label>
                                    <input
                                        type="url"
                                        value={formData.power_of_attorney_image_url}
                                        onChange={(e) => setFormData({ ...formData, power_of_attorney_image_url: e.target.value })}
                                        className="w-full px-4 py-2 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold-500 transition-colors text-sm"
                                        style={{ fontFamily: 'Cairo, sans-serif' }}
                                        placeholder="https://..."
                                    />
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Notes */}
                    <div>
                        <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            ملاحظات
                        </label>
                        <textarea
                            value={formData.notes}
                            onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                            className="w-full px-4 py-3 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold-500 transition-colors resize-none"
                            style={{ fontFamily: 'Cairo, sans-serif' }}
                            placeholder="ملاحظات إضافية..."
                            rows={3}
                        />
                    </div>

                    {/* Buttons */}
                    <div className="flex gap-3 pt-4">
                        <button
                            type="submit"
                            disabled={loading}
                            className="flex-1 px-6 py-3 bg-transparent border-2 border-gold-500 text-white font-bold rounded-lg hover:bg-gold-500/10 transition-all disabled:opacity-50"
                            style={{ fontFamily: 'Cairo, sans-serif' }}
                        >
                            {loading ? 'جاري الحفظ...' : 'حفظ'}
                        </button>
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-6 py-3 bg-obsidian-700 text-white font-medium rounded-lg hover:bg-obsidian-600 transition-colors"
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
