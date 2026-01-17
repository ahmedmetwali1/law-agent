import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Plus, Search, Briefcase, Calendar, X, UserPlus, Trash2 } from 'lucide-react'
import { supabase } from '../supabaseClient'
import { useAuth } from '../contexts/AuthContext'
import { toast } from 'sonner'
import { useAuditLog } from '../hooks/useAuditLog'

interface Client {
    id: string
    full_name: string
}

interface Opponent {
    id?: string
    full_name: string
    national_id: string
    capacity: string
}

interface Case {
    id: string
    lawyer_id: string
    client_id: string
    case_number: string
    court_name: string | null
    court_circuit: string | null
    case_type: string | null
    subject: string | null
    status: string
    summary: string | null
    case_year: string | null
    case_date: string | null
    client_capacity: string | null
    verdict_number: string | null
    verdict_year: string | null
    verdict_date: string | null
    created_at: string
    clients?: { full_name: string }
}

export function CasesPage() {
    const navigate = useNavigate()
    const { getEffectiveLawyerId } = useAuth()
    const [cases, setCases] = useState<Case[]>([])
    const [clients, setClients] = useState<Client[]>([])
    const [loading, setLoading] = useState(true)
    const [searchQuery, setSearchQuery] = useState('')
    const [showCreateModal, setShowCreateModal] = useState(false)
    const [preselectedClientId, setPreselectedClientId] = useState<string | null>(null)

    useEffect(() => {
        const lawyerId = getEffectiveLawyerId()
        if (lawyerId) {
            fetchCases()
            fetchClients()
        }
    }, [getEffectiveLawyerId])

    const fetchCases = async () => {
        const lawyerId = getEffectiveLawyerId()
        if (!lawyerId) return

        try {
            setLoading(true)
            const { data, error } = await supabase
                .from('cases')
                .select('*, clients(full_name)')
                .eq('lawyer_id', lawyerId)  // ✅ UPDATED for assistants
                .order('created_at', { ascending: false })

            if (error) throw error
            setCases(data || [])
        } catch (error) {
            console.error('Error fetching cases:', error)
            toast.error('فشل تحميل القضايا')
        } finally {
            setLoading(false)
        }
    }

    const fetchClients = async () => {
        const lawyerId = getEffectiveLawyerId()
        if (!lawyerId) return

        try {
            const { data, error } = await supabase
                .from('clients')
                .select('id, full_name')
                .eq('lawyer_id', lawyerId)  // ✅ UPDATED for assistants
                .order('full_name', { ascending: true })

            if (error) throw error
            setClients(data || [])
        } catch (error) {
            console.error('Error fetching clients:', error)
        }
    }

    const filteredCases = cases.filter(c => {
        const search = searchQuery.toLowerCase()
        return (
            c.case_number.toLowerCase().includes(search) ||
            c.clients?.full_name.toLowerCase().includes(search) ||
            c.subject?.toLowerCase().includes(search) ||
            c.court_name?.toLowerCase().includes(search)
        )
    })

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'active': return 'bg-green-500/20 text-green-400'
            case 'closed': return 'bg-gray-500/20 text-gray-400'
            case 'pending': return 'bg-yellow-500/20 text-yellow-400'
            default: return 'bg-blue-500/20 text-blue-400'
        }
    }

    const getStatusText = (status: string) => {
        switch (status) {
            case 'active': return 'نشطة'
            case 'closed': return 'مغلقة'
            case 'pending': return 'معلقة'
            default: return status
        }
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <h1 className="text-3xl font-bold text-gold-500" style={{ fontFamily: 'Cairo, sans-serif' }}>
                    القضايا
                </h1>
                <button
                    onClick={() => setShowCreateModal(true)}
                    className="flex items-center gap-2 px-6 py-3 bg-transparent border-2 border-gold-500 text-white font-bold rounded-lg hover:bg-gold-500/10 transition-all"
                    style={{ fontFamily: 'Cairo, sans-serif' }}
                >
                    <Plus className="w-5 h-5" />
                    <span>إضافة قضية</span>
                </button>
            </div>

            {/* Search */}
            <div className="backdrop-blur-xl bg-obsidian-800/70 border border-gold-500/20 rounded-xl p-4">
                <div className="relative">
                    <Search className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="ابحث برقم القضية، الموكل، الموضوع، أو المحكمة..."
                        className="w-full pr-12 pl-4 py-3 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold-500 transition-colors"
                        style={{ fontFamily: 'Cairo, sans-serif' }}
                    />
                </div>
            </div>

            {/* Cases List */}
            {loading ? (
                <div className="text-center py-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gold-500 mx-auto"></div>
                </div>
            ) : filteredCases.length === 0 ? (
                <div className="text-center py-12 backdrop-blur-xl bg-obsidian-800/50 border border-gold-500/20 rounded-xl">
                    <Briefcase className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                    <p className="text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        {searchQuery ? 'لا توجد نتائج' : 'لا توجد قضايا'}
                    </p>
                </div>
            ) : (
                <div className="grid grid-cols-1 gap-4">
                    {filteredCases.map((caseItem, index) => (
                        <motion.div
                            key={caseItem.id}
                            initial={{ opacity: 1, y: 0 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: index * 0.03 }}
                            onClick={() => navigate(`/cases/${caseItem.id}`)}
                            className="backdrop-blur-xl bg-obsidian-800/70 border border-gold-500/20 rounded-xl p-5 hover:border-gold-500/50 transition-all cursor-pointer"
                        >
                            <div className="flex items-start justify-between mb-3">
                                <div className="flex-1">
                                    <div className="flex items-center gap-3 mb-2">
                                        <h3 className="text-xl font-bold text-gold-500" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                            {caseItem.case_number}
                                        </h3>
                                        <span className={`px-2 py-1 rounded-full text-xs ${getStatusColor(caseItem.status)}`} style={{ fontFamily: 'Cairo, sans-serif' }}>
                                            {getStatusText(caseItem.status)}
                                        </span>
                                    </div>
                                    {caseItem.subject && (
                                        <p className="text-gray-300 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                            {caseItem.subject}
                                        </p>
                                    )}
                                </div>
                            </div>

                            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                                <div>
                                    <p className="text-gray-500 text-xs mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>الموكل</p>
                                    <p className="text-white" style={{ fontFamily: 'Cairo, sans-serif' }}>{caseItem.clients?.full_name}</p>
                                </div>
                                {caseItem.court_name && (
                                    <div>
                                        <p className="text-gray-500 text-xs mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>المحكمة</p>
                                        <p className="text-white" style={{ fontFamily: 'Cairo, sans-serif' }}>{caseItem.court_name}</p>
                                    </div>
                                )}
                                {caseItem.case_type && (
                                    <div>
                                        <p className="text-gray-500 text-xs mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>النوع</p>
                                        <p className="text-white" style={{ fontFamily: 'Cairo, sans-serif' }}>{caseItem.case_type}</p>
                                    </div>
                                )}
                                {caseItem.case_year && (
                                    <div>
                                        <p className="text-gray-500 text-xs mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>السنة</p>
                                        <p className="text-white" style={{ fontFamily: 'Cairo, sans-serif' }}>{caseItem.case_year}</p>
                                    </div>
                                )}
                            </div>
                        </motion.div>
                    ))}
                </div>
            )}

            {/* Create Modal */}
            {showCreateModal && (
                <CreateCaseModal
                    clients={clients}
                    preselectedClientId={preselectedClientId}
                    onClose={() => {
                        setShowCreateModal(false)
                        setPreselectedClientId(null)
                    }}
                    onSuccess={() => {
                        setShowCreateModal(false)
                        setPreselectedClientId(null)
                        fetchCases()
                    }}
                />
            )}
        </div>
    )
}

// Create Case Modal
interface CreateCaseModalProps {
    clients: Client[]
    preselectedClientId: string | null
    onClose: () => void
    onSuccess: () => void
}

function CreateCaseModal({ clients, preselectedClientId, onClose, onSuccess }: CreateCaseModalProps) {
    const { getEffectiveLawyerId } = useAuth()  // ✅ إضافة
    const { logAction } = useAuditLog()
    const [loading, setLoading] = useState(false)
    const [opponents, setOpponents] = useState<Opponent[]>([])
    const [formData, setFormData] = useState({
        client_id: preselectedClientId || '',
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

    const addOpponent = () => {
        setOpponents([...opponents, { full_name: '', national_id: '', capacity: '' }])
    }

    const removeOpponent = (index: number) => {
        setOpponents(opponents.filter((_, i) => i !== index))
    }

    const updateOpponent = (index: number, field: keyof Opponent, value: string) => {
        const updated = [...opponents]
        updated[index] = { ...updated[index], [field]: value }
        setOpponents(updated)
    }


    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()

        if (!formData.case_number.trim() || !formData.client_id) {
            toast.error('رقم القضية والموكل مطلوبان')
            return
        }

        setLoading(true)

        try {
            const lawyerId = getEffectiveLawyerId()
            if (!lawyerId) {
                toast.error('تعذر تحديد هوية المحامي')
                return
            }

            // Insert case
            const caseDataValues = {
                lawyer_id: lawyerId,  // ✅ يُسجل للمحامي
                client_id: formData.client_id,
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
            }

            const { data: caseData, error: caseError } = await supabase
                .from('cases')
                .insert(caseDataValues)
                .select()
                .single()

            if (caseError) throw caseError

            // ✅ تسجيل إنشاء القضية
            await logAction(
                'create',
                'cases',
                caseData.id,
                null,
                caseDataValues,
                'إنشاء قضية جديدة'
            )

            // Insert opponents if any
            if (opponents.length > 0 && caseData) {
                const opponentsData = opponents
                    .filter(o => o.full_name.trim())
                    .map(o => ({
                        case_id: caseData.id,
                        full_name: o.full_name,
                        national_id: o.national_id || null,
                        capacity: o.capacity || null
                    }))

                if (opponentsData.length > 0) {
                    const { error: opponentsError } = await supabase
                        .from('opponents')
                        .insert(opponentsData)

                    if (opponentsError) console.error('Error adding opponents:', opponentsError)

                    // ✅ تسجيل إضافة الخصوم
                    await logAction(
                        'create',
                        'opponents',
                        caseData.id,
                        null,
                        { count: opponentsData.length, names: opponentsData.map(o => o.full_name).join(', ') },
                        'إضافة خصوم للقضية'
                    )
                }
            }

            toast.success('تمت إضافة القضية بنجاح')
            onSuccess()
        } catch (error: any) {
            console.error('Error creating case:', error)
            toast.error('فشل إضافة القضية')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4 overflow-y-auto">
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="backdrop-blur-xl bg-obsidian-800/90 border border-gold-500/20 rounded-2xl p-6 max-w-5xl w-full my-8"
            >
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-bold text-gold-500" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        إضافة قضية جديدة
                    </h2>
                    <button onClick={onClose} className="text-gray-400 hover:text-white">
                        <X className="w-6 h-6" />
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    {/* Row 1: Client, Case Number, Year */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                        <div>
                            <label className="block text-xs font-medium text-gold-500 mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                الموكل <span className="text-red-400">*</span>
                            </label>
                            <select
                                value={formData.client_id}
                                onChange={(e) => setFormData({ ...formData, client_id: e.target.value })}
                                className="w-full px-3 py-2 text-sm bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white focus:outline-none focus:border-gold-500"
                                style={{ fontFamily: 'Cairo, sans-serif' }}
                                required
                            >
                                <option value="">اختر موكل</option>
                                {clients.map(client => (
                                    <option key={client.id} value={client.id}>{client.full_name}</option>
                                ))}
                            </select>
                        </div>

                        <div>
                            <label className="block text-xs font-medium text-gold-500 mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                رقم القضية <span className="text-red-400">*</span>
                            </label>
                            <input
                                type="text"
                                value={formData.case_number}
                                onChange={(e) => setFormData({ ...formData, case_number: e.target.value })}
                                className="w-full px-3 py-2 text-sm bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold-500"
                                style={{ fontFamily: 'Cairo, sans-serif' }}
                                placeholder="123/2024"
                                required
                            />
                        </div>

                        <div>
                            <label className="block text-xs font-medium text-gold-500 mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                السنة
                            </label>
                            <input
                                type="text"
                                value={formData.case_year}
                                onChange={(e) => setFormData({ ...formData, case_year: e.target.value })}
                                className="w-full px-3 py-2 text-sm bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold-500"
                                style={{ fontFamily: 'Cairo, sans-serif' }}
                            />
                        </div>
                    </div>

                    {/* Row 2: Court, Circuit, Type */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                        <div>
                            <label className="block text-xs font-medium text-gold-500 mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                المحكمة
                            </label>
                            <input
                                type="text"
                                value={formData.court_name}
                                onChange={(e) => setFormData({ ...formData, court_name: e.target.value })}
                                className="w-full px-3 py-2 text-sm bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold-500"
                                style={{ fontFamily: 'Cairo, sans-serif' }}
                            />
                        </div>

                        <div>
                            <label className="block text-xs font-medium text-gold-500 mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                الدائرة
                            </label>
                            <input
                                type="text"
                                value={formData.court_circuit}
                                onChange={(e) => setFormData({ ...formData, court_circuit: e.target.value })}
                                className="w-full px-3 py-2 text-sm bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold-500"
                                style={{ fontFamily: 'Cairo, sans-serif' }}
                            />
                        </div>

                        <div>
                            <label className="block text-xs font-medium text-gold-500 mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                نوع القضية
                            </label>
                            <input
                                type="text"
                                value={formData.case_type}
                                onChange={(e) => setFormData({ ...formData, case_type: e.target.value })}
                                className="w-full px-3 py-2 text-sm bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold-500"
                                style={{ fontFamily: 'Cairo, sans-serif' }}
                                placeholder="مدني، جنائي..."
                            />
                        </div>
                    </div>

                    {/* Row 3: Client Capacity, Case Date, Status */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                        <div>
                            <label className="block text-xs font-medium text-gold-500 mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                صفة الموكل
                            </label>
                            <select
                                value={formData.client_capacity}
                                onChange={(e) => setFormData({ ...formData, client_capacity: e.target.value })}
                                className="w-full px-3 py-2 text-sm bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white focus:outline-none focus:border-gold-500"
                                style={{ fontFamily: 'Cairo, sans-serif' }}
                            >
                                <option value="">اختر</option>
                                <option value="مدعي">مدعي</option>
                                <option value="مدعى عليه">مدعى عليه</option>
                                <option value="مستأنف">مستأنف</option>
                                <option value="مستأنف ضده">مستأنف ضده</option>
                            </select>
                        </div>

                        <div>
                            <label className="block text-xs font-medium text-gold-500 mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                تاريخ القضية
                            </label>
                            <input
                                type="date"
                                value={formData.case_date}
                                onChange={(e) => setFormData({ ...formData, case_date: e.target.value })}
                                className="w-full px-3 py-2 text-sm bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white focus:outline-none focus:border-gold-500"
                                style={{ fontFamily: 'Cairo, sans-serif' }}
                            />
                        </div>

                        <div>
                            <label className="block text-xs font-medium text-gold-500 mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                الحالة
                            </label>
                            <select
                                value={formData.status}
                                onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                                className="w-full px-3 py-2 text-sm bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white focus:outline-none focus:border-gold-500"
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
                        <label className="block text-xs font-medium text-gold-500 mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            موضوع القضية
                        </label>
                        <input
                            type="text"
                            value={formData.subject}
                            onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                            className="w-full px-3 py-2 text-sm bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold-500"
                            style={{ fontFamily: 'Cairo, sans-serif' }}
                            placeholder="وصف مختصر..."
                        />
                    </div>

                    {/* Summary */}
                    <div>
                        <label className="block text-xs font-medium text-gold-500 mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            ملخص القضية
                        </label>
                        <textarea
                            value={formData.summary}
                            onChange={(e) => setFormData({ ...formData, summary: e.target.value })}
                            className="w-full px-3 py-2 text-sm bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold-500 resize-none"
                            style={{ fontFamily: 'Cairo, sans-serif' }}
                            rows={2}
                        />
                    </div>

                    {/* Opponents Section */}
                    <div className="border-t border-gold-500/20 pt-4">
                        <div className="flex items-center justify-between mb-3">
                            <h3 className="text-sm font-bold text-white" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                الخصوم
                            </h3>
                            <button
                                type="button"
                                onClick={addOpponent}
                                className="flex items-center gap-1 px-3 py-1 text-xs bg-gold-500/20 text-gold-500 rounded-lg hover:bg-gold-500/30 transition"
                                style={{ fontFamily: 'Cairo, sans-serif' }}
                            >
                                <UserPlus className="w-3 h-3" />
                                <span>إضافة خصم</span>
                            </button>
                        </div>

                        <AnimatePresence>
                            {opponents.map((opponent, index) => (
                                <motion.div
                                    key={index}
                                    initial={{ opacity: 0, height: 0 }}
                                    animate={{ opacity: 1, height: 'auto' }}
                                    exit={{ opacity: 0, height: 0 }}
                                    className="grid grid-cols-1 md:grid-cols-4 gap-2 mb-2 p-3 bg-obsidian-900/30 rounded-lg border border-gold-500/10"
                                >
                                    <input
                                        type="text"
                                        value={opponent.full_name}
                                        onChange={(e) => updateOpponent(index, 'full_name', e.target.value)}
                                        className="px-3 py-2 text-sm bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold-500"
                                        style={{ fontFamily: 'Cairo, sans-serif' }}
                                        placeholder="الاسم الكامل"
                                    />
                                    <input
                                        type="text"
                                        value={opponent.national_id}
                                        onChange={(e) => updateOpponent(index, 'national_id', e.target.value)}
                                        className="px-3 py-2 text-sm bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold-500"
                                        style={{ fontFamily: 'Cairo, sans-serif' }}
                                        placeholder="رقم الهوية"
                                    />
                                    <select
                                        value={opponent.capacity}
                                        onChange={(e) => updateOpponent(index, 'capacity', e.target.value)}
                                        className="px-3 py-2 text-sm bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white focus:outline-none focus:border-gold-500"
                                        style={{ fontFamily: 'Cairo, sans-serif' }}
                                    >
                                        <option value="">الصفة</option>
                                        <option value="مدعي">مدعي</option>
                                        <option value="مدعى عليه">مدعى عليه</option>
                                    </select>
                                    <button
                                        type="button"
                                        onClick={() => removeOpponent(index)}
                                        className="px-3 py-2 text-sm bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition flex items-center justify-center gap-1"
                                        style={{ fontFamily: 'Cairo, sans-serif' }}
                                    >
                                        <Trash2 className="w-3 h-3" />
                                        <span>حذف</span>
                                    </button>
                                </motion.div>
                            ))}
                        </AnimatePresence>
                    </div>

                    {/* Verdict Section */}
                    <div className="border-t border-gold-500/20 pt-4">
                        <h3 className="text-sm font-bold text-white mb-3" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            بيانات الحكم (اختياري)
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                            <input
                                type="text"
                                value={formData.verdict_number}
                                onChange={(e) => setFormData({ ...formData, verdict_number: e.target.value })}
                                className="px-3 py-2 text-sm bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold-500"
                                style={{ fontFamily: 'Cairo, sans-serif' }}
                                placeholder="رقم الحكم"
                            />
                            <input
                                type="text"
                                value={formData.verdict_year}
                                onChange={(e) => setFormData({ ...formData, verdict_year: e.target.value })}
                                className="px-3 py-2 text-sm bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold-500"
                                style={{ fontFamily: 'Cairo, sans-serif' }}
                                placeholder="سنة الحكم"
                            />
                            <input
                                type="date"
                                value={formData.verdict_date}
                                onChange={(e) => setFormData({ ...formData, verdict_date: e.target.value })}
                                className="px-3 py-2 text-sm bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white focus:outline-none focus:border-gold-500"
                                style={{ fontFamily: 'Cairo, sans-serif' }}
                            />
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
