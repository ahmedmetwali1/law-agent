import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowRight, Plus, Phone, Mail, MapPin, Scale, Briefcase, Calendar, FileText, Edit } from 'lucide-react'
import { supabase } from '../supabaseClient'
import { useAuth } from '../contexts/AuthContext'
import { useBreadcrumb } from '../contexts/BreadcrumbContext'
import { toast } from 'sonner'

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
    created_at: string
}

interface Case {
    id: string
    client_id: string
    case_number: string
    court_name: string | null
    court_circuit: string | null
    case_type: string | null
    subject: string | null
    status: string
    summary: string | null
    ai_summary: string | null
    case_year: string | null
    case_date: string | null
    client_capacity: string | null
    verdict_number: string | null
    verdict_year: string | null
    verdict_date: string | null
    created_at: string
    updated_at: string
}

export function ClientProfile() {
    const { id } = useParams<{ id: string }>()
    const navigate = useNavigate()
    const { getEffectiveLawyerId } = useAuth()
    const { setPageTitle } = useBreadcrumb()
    const [client, setClient] = useState<Client | null>(null)
    const [cases, setCases] = useState<Case[]>([])
    const [loading, setLoading] = useState(true)
    const [showCreateCaseModal, setShowCreateCaseModal] = useState(false)

    useEffect(() => {
        const lawyerId = getEffectiveLawyerId()
        if (id && lawyerId) {
            fetchClientAndCases()
        }
    }, [id, getEffectiveLawyerId])

    // Update breadcrumb when client data loads
    useEffect(() => {
        if (client) {
            setPageTitle(client.full_name)
        }
        return () => {
            setPageTitle(null) // Clear on unmount
        }
    }, [client, setPageTitle])

    const fetchClientAndCases = async () => {
        const lawyerId = getEffectiveLawyerId()
        if (!id || !lawyerId) return

        try {
            setLoading(true)

            // Fetch client
            const { data: clientData, error: clientError } = await supabase
                .from('clients')
                .select('*')
                .eq('id', id)
                .eq('lawyer_id', lawyerId)  // ✅ UPDATED for assistants
                .single()

            if (clientError) throw clientError
            setClient(clientData)

            // Fetch cases
            const { data: casesData, error: casesError } = await supabase
                .from('cases')
                .select('*')
                .eq('client_id', id)
                .eq('lawyer_id', lawyerId)  // ✅ UPDATED for assistants
                .order('created_at', { ascending: false })

            if (casesError) throw casesError
            setCases(casesData || [])
        } catch (error: any) {
            console.error('Error fetching data:', error)
            toast.error('فشل تحميل البيانات')
        } finally {
            setLoading(false)
        }
    }

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'active':
                return 'bg-green-500/20 text-green-500'
            case 'closed':
                return 'bg-gray-500/20 text-gray-500'
            case 'pending':
                return 'bg-yellow-500/20 text-yellow-500'
            default:
                return 'bg-blue-500/20 text-blue-500'
        }
    }

    const getStatusText = (status: string) => {
        switch (status) {
            case 'active':
                return 'نشطة'
            case 'closed':
                return 'مغلقة'
            case 'pending':
                return 'معلقة'
            default:
                return status
        }
    }

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gold-500"></div>
            </div>
        )
    }

    if (!client) {
        return (
            <div className="text-center py-12">
                <p className="text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>لم يتم العثور على الموكل</p>
                <button
                    onClick={() => navigate('/clients')}
                    className="mt-4 text-gold-500 hover:text-gold-400"
                    style={{ fontFamily: 'Cairo, sans-serif' }}
                >
                    العودة للموكلين
                </button>
            </div>
        )
    }

    return (
        <div className="space-y-6">
            {/* Header with Back Button */}
            <div className="flex items-center gap-4">
                <button
                    onClick={() => navigate('/clients')}
                    className="p-2 hover:bg-obsidian-700 rounded-lg transition"
                >
                    <ArrowRight className="w-5 h-5 text-gray-400" />
                </button>
                <h1 className="text-3xl font-bold text-gold-500" style={{ fontFamily: 'Cairo, sans-serif' }}>
                    {client.full_name}
                </h1>
            </div>

            {/* Client Details Card */}
            <div className="backdrop-blur-xl bg-obsidian-800/70 border border-gold-500/20 rounded-xl p-6">
                <div className="flex items-start justify-between mb-6">
                    <h2 className="text-xl font-bold text-white" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        معلومات الموكل
                    </h2>
                    {client.has_power_of_attorney && (
                        <span className="inline-flex items-center gap-1 px-3 py-1 bg-gold-500/20 text-gold-500 text-sm rounded-full">
                            <Scale className="w-4 h-4" />
                            <span style={{ fontFamily: 'Cairo, sans-serif' }}>يمتلك توكيل</span>
                        </span>
                    )}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {client.phone && (
                        <div className="flex items-center gap-3">
                            <Phone className="w-5 h-5 text-gray-500" />
                            <div>
                                <p className="text-xs text-gray-500" style={{ fontFamily: 'Cairo, sans-serif' }}>الهاتف</p>
                                <p className="text-white" style={{ fontFamily: 'Cairo, sans-serif' }}>{client.phone}</p>
                            </div>
                        </div>
                    )}

                    {client.email && (
                        <div className="flex items-center gap-3">
                            <Mail className="w-5 h-5 text-gray-500" />
                            <div>
                                <p className="text-xs text-gray-500" style={{ fontFamily: 'Cairo, sans-serif' }}>البريد الإلكتروني</p>
                                <p className="text-white" style={{ fontFamily: 'Cairo, sans-serif' }}>{client.email}</p>
                            </div>
                        </div>
                    )}

                    {client.national_id && (
                        <div className="flex items-center gap-3">
                            <FileText className="w-5 h-5 text-gray-500" />
                            <div>
                                <p className="text-xs text-gray-500" style={{ fontFamily: 'Cairo, sans-serif' }}>رقم الهوية</p>
                                <p className="text-white" style={{ fontFamily: 'Cairo, sans-serif' }}>{client.national_id}</p>
                            </div>
                        </div>
                    )}

                    {client.address && (
                        <div className="flex items-center gap-3">
                            <MapPin className="w-5 h-5 text-gray-500" />
                            <div>
                                <p className="text-xs text-gray-500" style={{ fontFamily: 'Cairo, sans-serif' }}>العنوان</p>
                                <p className="text-white" style={{ fontFamily: 'Cairo, sans-serif' }}>{client.address}</p>
                            </div>
                        </div>
                    )}

                    {client.power_of_attorney_number && (
                        <div className="flex items-center gap-3">
                            <Scale className="w-5 h-5 text-gold-500" />
                            <div>
                                <p className="text-xs text-gray-500" style={{ fontFamily: 'Cairo, sans-serif' }}>رقم التوكيل</p>
                                <p className="text-white" style={{ fontFamily: 'Cairo, sans-serif' }}>{client.power_of_attorney_number}</p>
                            </div>
                        </div>
                    )}
                </div>

                {client.notes && (
                    <div className="mt-4 pt-4 border-t border-gold-500/10">
                        <p className="text-xs text-gray-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>ملاحظات</p>
                        <p className="text-white" style={{ fontFamily: 'Cairo, sans-serif' }}>{client.notes}</p>
                    </div>
                )}
            </div>

            {/* Cases Section */}
            <div className="backdrop-blur-xl bg-obsidian-800/70 border border-gold-500/20 rounded-xl p-6">
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-3">
                        <Briefcase className="w-6 h-6 text-gold-500" />
                        <h2 className="text-xl font-bold text-white" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            القضايا ({cases.length})
                        </h2>
                    </div>
                    <button
                        onClick={() => setShowCreateCaseModal(true)}
                        className="flex items-center gap-2 px-4 py-2 bg-transparent border-2 border-gold-500 text-white font-bold rounded-lg hover:bg-gold-500/10 transition-all"
                        style={{ fontFamily: 'Cairo, sans-serif' }}
                    >
                        <Plus className="w-4 h-4" />
                        <span>إضافة قضية</span>
                    </button>
                </div>

                {cases.length === 0 ? (
                    <div className="text-center py-12">
                        <Briefcase className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                        <p className="text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            لا توجد قضايا لهذا الموكل
                        </p>
                        <button
                            onClick={() => setShowCreateCaseModal(true)}
                            className="mt-4 text-gold-500 hover:text-gold-400"
                            style={{ fontFamily: 'Cairo, sans-serif' }}
                        >
                            إضافة قضية جديدة
                        </button>
                    </div>
                ) : (
                    <div className="space-y-4">
                        {cases.map((caseItem, index) => (
                            <motion.div
                                key={caseItem.id}
                                initial={{ opacity: 1, y: 0 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: index * 0.05 }}
                                className="bg-obsidian-900/50 border border-gold-500/10 rounded-lg p-4 hover:border-gold-500/30 transition-all cursor-pointer"
                                onClick={() => navigate(`/cases/${caseItem.id}`)}
                            >
                                <div className="flex items-start justify-between mb-3">
                                    <div className="flex-1">
                                        <h3 className="text-lg font-bold text-white mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                            {caseItem.case_number}
                                        </h3>
                                        {caseItem.subject && (
                                            <p className="text-sm text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                                {caseItem.subject}
                                            </p>
                                        )}
                                    </div>
                                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(caseItem.status)}`} style={{ fontFamily: 'Cairo, sans-serif' }}>
                                        {getStatusText(caseItem.status)}
                                    </span>
                                </div>

                                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                                    {caseItem.court_name && (
                                        <div>
                                            <p className="text-gray-500 text-xs" style={{ fontFamily: 'Cairo, sans-serif' }}>المحكمة</p>
                                            <p className="text-white" style={{ fontFamily: 'Cairo, sans-serif' }}>{caseItem.court_name}</p>
                                        </div>
                                    )}
                                    {caseItem.case_type && (
                                        <div>
                                            <p className="text-gray-500 text-xs" style={{ fontFamily: 'Cairo, sans-serif' }}>نوع القضية</p>
                                            <p className="text-white" style={{ fontFamily: 'Cairo, sans-serif' }}>{caseItem.case_type}</p>
                                        </div>
                                    )}
                                    {caseItem.case_year && (
                                        <div>
                                            <p className="text-gray-500 text-xs" style={{ fontFamily: 'Cairo, sans-serif' }}>السنة</p>
                                            <p className="text-white" style={{ fontFamily: 'Cairo, sans-serif' }}>{caseItem.case_year}</p>
                                        </div>
                                    )}
                                    {caseItem.client_capacity && (
                                        <div>
                                            <p className="text-gray-500 text-xs" style={{ fontFamily: 'Cairo, sans-serif' }}>الصفة</p>
                                            <p className="text-white" style={{ fontFamily: 'Cairo, sans-serif' }}>{caseItem.client_capacity}</p>
                                        </div>
                                    )}
                                </div>
                            </motion.div>
                        ))}
                    </div>
                )}
            </div>

            {/* Create Case Modal */}
            {showCreateCaseModal && (
                <CreateCaseModal
                    clientId={client.id}
                    clientName={client.full_name}
                    onClose={() => setShowCreateCaseModal(false)}
                    onSuccess={() => {
                        setShowCreateCaseModal(false)
                        fetchClientAndCases()
                    }}
                />
            )}
        </div>
    )
}

// Create Case Modal Component
interface CreateCaseModalProps {
    clientId: string
    clientName: string
    onClose: () => void
    onSuccess: () => void
}

function CreateCaseModal({ clientId, clientName, onClose, onSuccess }: CreateCaseModalProps) {
    const { getEffectiveLawyerId } = useAuth()  // ✅ إضافة
    const [loading, setLoading] = useState(false)
    const [formData, setFormData] = useState({
        case_number: '',
        court_name: '',
        court_circuit: '',
        case_type: '',
        subject: '',
        status: 'active',
        summary: '',
        case_year: new Date().getFullYear().toString(),
        case_date: '',
        client_capacity: '',
        verdict_number: '',
        verdict_year: '',
        verdict_date: ''
    })

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()

        if (!formData.case_number.trim()) {
            toast.error('رقم القضية مطلوب')
            return
        }

        setLoading(true)

        try {
            const { error } = await supabase
                .from('cases')
                .insert({
                    client_id: clientId,
                    lawyer_id: getEffectiveLawyerId(),  // ✅ يُسجل للمحامي
                    case_number: formData.case_number,
                    court_name: formData.court_name || null,
                    court_circuit: formData.court_circuit || null,
                    case_type: formData.case_type || null,
                    subject: formData.subject || null,
                    status: formData.status,
                    summary: formData.summary || null,
                    case_year: formData.case_year || null,
                    case_date: formData.case_date || null,
                    client_capacity: formData.client_capacity || null,
                    verdict_number: formData.verdict_number || null,
                    verdict_year: formData.verdict_year || null,
                    verdict_date: formData.verdict_date || null
                })

            if (error) throw error

            toast.success('تمت إضافة القضية بنجاح')
            onSuccess()
        } catch (error: any) {
            console.error('Error creating case:', error)
            toast.error('فشل إضافة القضية: ' + error.message)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="backdrop-blur-xl bg-obsidian-800/90 border border-gold-500/20 rounded-2xl p-8 max-w-4xl w-full max-h-[90vh] overflow-y-auto"
            >
                <h2 className="text-2xl font-bold text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                    إضافة قضية جديدة
                </h2>
                <p className="text-gray-400 mb-6" style={{ fontFamily: 'Cairo, sans-serif' }}>
                    للموكل: {clientName}
                </p>

                <form onSubmit={handleSubmit} className="space-y-4">
                    {/* Case Number and Year */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                رقم القضية <span className="text-red-400">*</span>
                            </label>
                            <input
                                type="text"
                                value={formData.case_number}
                                onChange={(e) => setFormData({ ...formData, case_number: e.target.value })}
                                className="w-full px-4 py-3 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold-500 transition-colors"
                                style={{ fontFamily: 'Cairo, sans-serif' }}
                                placeholder="مثال: 123/2024"
                                required
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                سنة القضية
                            </label>
                            <input
                                type="text"
                                value={formData.case_year}
                                onChange={(e) => setFormData({ ...formData, case_year: e.target.value })}
                                className="w-full px-4 py-3 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold-500 transition-colors"
                                style={{ fontFamily: 'Cairo, sans-serif' }}
                                placeholder="2024"
                            />
                        </div>
                    </div>

                    {/* Court Name and Circuit */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                اسم المحكمة
                            </label>
                            <input
                                type="text"
                                value={formData.court_name}
                                onChange={(e) => setFormData({ ...formData, court_name: e.target.value })}
                                className="w-full px-4 py-3 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold-500 transition-colors"
                                style={{ fontFamily: 'Cairo, sans-serif' }}
                                placeholder="محكمة..."
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                الدائرة
                            </label>
                            <input
                                type="text"
                                value={formData.court_circuit}
                                onChange={(e) => setFormData({ ...formData, court_circuit: e.target.value })}
                                className="w-full px-4 py-3 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold-500 transition-colors"
                                style={{ fontFamily: 'Cairo, sans-serif' }}
                                placeholder="الدائرة..."
                            />
                        </div>
                    </div>

                    {/* Case Type and Client Capacity */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                نوع القضية
                            </label>
                            <input
                                type="text"
                                value={formData.case_type}
                                onChange={(e) => setFormData({ ...formData, case_type: e.target.value })}
                                className="w-full px-4 py-3 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold-500 transition-colors"
                                style={{ fontFamily: 'Cairo, sans-serif' }}
                                placeholder="مدني، جنائي، تجاري..."
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                صفة الموكل
                            </label>
                            <select
                                value={formData.client_capacity}
                                onChange={(e) => setFormData({ ...formData, client_capacity: e.target.value })}
                                className="w-full px-4 py-3 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white focus:outline-none focus:border-gold-500 transition-colors"
                                style={{ fontFamily: 'Cairo, sans-serif' }}
                            >
                                <option value="">اختر الصفة</option>
                                <option value="مدعي">مدعي</option>
                                <option value="مدعى عليه">مدعى عليه</option>
                                <option value="مستأنف">مستأنف</option>
                                <option value="مستأنف ضده">مستأنف ضده</option>
                            </select>
                        </div>
                    </div>

                    {/* Case Date and Status */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                تاريخ القضية
                            </label>
                            <input
                                type="date"
                                value={formData.case_date}
                                onChange={(e) => setFormData({ ...formData, case_date: e.target.value })}
                                className="w-full px-4 py-3 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white focus:outline-none focus:border-gold-500 transition-colors"
                                style={{ fontFamily: 'Cairo, sans-serif' }}
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                الحالة
                            </label>
                            <select
                                value={formData.status}
                                onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                                className="w-full px-4 py-3 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white focus:outline-none focus:border-gold-500 transition-colors"
                                style={{ fontFamily: 'Cairo, sans-serif' }}
                            >
                                <option value="active">نشطة</option>
                                <option value="pending">معلقة</option>
                                <option value="closed">مغلقة</option>
                            </select>
                        </div>
                    </div>

                    {/* Subject */}
                    <div>
                        <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            موضوع القضية
                        </label>
                        <input
                            type="text"
                            value={formData.subject}
                            onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                            className="w-full px-4 py-3 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold-500 transition-colors"
                            style={{ fontFamily: 'Cairo, sans-serif' }}
                            placeholder="وصف مختصر لموضوع القضية"
                        />
                    </div>

                    {/* Summary */}
                    <div>
                        <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            ملخص القضية
                        </label>
                        <textarea
                            value={formData.summary}
                            onChange={(e) => setFormData({ ...formData, summary: e.target.value })}
                            className="w-full px-4 py-3 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold-500 transition-colors resize-none"
                            style={{ fontFamily: 'Cairo, sans-serif' }}
                            placeholder="ملخص تفصيلي عن القضية..."
                            rows={3}
                        />
                    </div>

                    {/* Verdict Section */}
                    <div className="border-t border-gold-500/20 pt-4">
                        <h3 className="text-lg font-bold text-white mb-4" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            بيانات الحكم (اختياري)
                        </h3>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                    رقم الحكم
                                </label>
                                <input
                                    type="text"
                                    value={formData.verdict_number}
                                    onChange={(e) => setFormData({ ...formData, verdict_number: e.target.value })}
                                    className="w-full px-4 py-2 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold-500 transition-colors text-sm"
                                    style={{ fontFamily: 'Cairo, sans-serif' }}
                                    placeholder="رقم..."
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                    سنة الحكم
                                </label>
                                <input
                                    type="text"
                                    value={formData.verdict_year}
                                    onChange={(e) => setFormData({ ...formData, verdict_year: e.target.value })}
                                    className="w-full px-4 py-2 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold-500 transition-colors text-sm"
                                    style={{ fontFamily: 'Cairo, sans-serif' }}
                                    placeholder="2024"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                    تاريخ الحكم
                                </label>
                                <input
                                    type="date"
                                    value={formData.verdict_date}
                                    onChange={(e) => setFormData({ ...formData, verdict_date: e.target.value })}
                                    className="w-full px-4 py-2 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white focus:outline-none focus:border-gold-500 transition-colors text-sm"
                                    style={{ fontFamily: 'Cairo, sans-serif' }}
                                />
                            </div>
                        </div>
                    </div>

                    {/* Buttons */}
                    <div className="flex gap-3 pt-4">
                        <button
                            type="submit"
                            disabled={loading}
                            className="flex-1 px-6 py-3 bg-transparent border-2 border-gold-500 text-white font-bold rounded-lg hover:bg-gold-500/10 transition-all disabled:opacity-50"
                            style={{ fontFamily: 'Cairo, sans-serif' }}
                        >
                            {loading ? 'جاري الحفظ...' : 'حفظ القضية'}
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
