import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { ArrowRight, Plus, Calendar, Clock, MapPin, User, FileText, X, Gavel, Scale, Users, Upload, Edit2, Trash2, Download, Eye } from 'lucide-react'
import { supabase } from '../supabaseClient'
import { useAuth } from '../contexts/AuthContext'
import { useBreadcrumb } from '../contexts/BreadcrumbContext'
import { toast } from 'sonner'
import { useAuditLog } from '../hooks/useAuditLog'

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

interface Hearing {
    id: string
    case_id: string
    lawyer_id: string
    hearing_date: string
    hearing_time: string | null
    court_room: string | null
    judge_name: string | null
    judge_requests: string | null
    notes: string | null
    outcome: string | null
    next_hearing_date: string | null
    created_at: string
}

interface Opponent {
    id: string
    case_id: string
    full_name: string
    national_id: string | null
    capacity: string | null
}

interface Document {
    id: string
    case_id: string
    lawyer_id: string
    client_id: string | null
    file_name: string
    file_url: string
    file_type: string
    document_type: string
    raw_text: string | null
    ai_summary: string | null
    is_analyzed: boolean
    ocr_enabled: boolean
    ocr_status: string
    summary_status: string
    word_count: number
    file_size: number
    created_at: string
}

export function CaseDetails() {
    const { id } = useParams<{ id: string }>()
    const navigate = useNavigate()
    const { getEffectiveLawyerId } = useAuth()
    const { logAction } = useAuditLog()
    const { setPageTitle } = useBreadcrumb()
    const [caseData, setCaseData] = useState<Case | null>(null)
    const [hearings, setHearings] = useState<Hearing[]>([])
    const [opponents, setOpponents] = useState<Opponent[]>([])
    const [documents, setDocuments] = useState<Document[]>([])
    const [loading, setLoading] = useState(true)
    const [showAddHearingModal, setShowAddHearingModal] = useState(false)
    const [showEditHearingModal, setShowEditHearingModal] = useState(false)
    const [editingHearing, setEditingHearing] = useState<Hearing | null>(null)
    const [showAddOpponentModal, setShowAddOpponentModal] = useState(false)
    const [showUploadModal, setShowUploadModal] = useState(false)

    useEffect(() => {
        const lawyerId = getEffectiveLawyerId()
        if (id && lawyerId) {
            fetchCaseDetails()
        }
    }, [id, getEffectiveLawyerId])

    // Update breadcrumb and document title when case data loads
    useEffect(() => {
        if (caseData) {
            const clientName = caseData.clients?.full_name || 'موكل'
            const caseNumber = caseData.case_number
            const title = `${clientName} - قضية رقم ${caseNumber}`
            setPageTitle(title) // Set breadcrumb title with client name
            document.title = `${title} - نظام إدارة المحاماة`
        }
        return () => {
            setPageTitle(null) // Clear breadcrumb on unmount
            document.title = 'نظام إدارة المحاماة'
        }
    }, [caseData, setPageTitle])

    const fetchCaseDetails = async () => {
        const lawyerId = getEffectiveLawyerId()
        if (!id || !lawyerId) return

        try {
            setLoading(true)

            // Fetch case
            const { data: caseDataResult, error: caseError } = await supabase
                .from('cases')
                .select('*, clients(full_name)')
                .eq('id', id)
                .eq('lawyer_id', lawyerId)  // ✅ UPDATED for assistants
                .single()

            if (caseError) throw caseError
            setCaseData(caseDataResult)

            // Fetch hearings
            const { data: hearingsData, error: hearingsError } = await supabase
                .from('hearings')
                .select('*')
                .eq('case_id', id)
                .eq('lawyer_id', lawyerId)  // ✅ UPDATED for assistants
                .order('hearing_date', { ascending: false })

            if (hearingsError) throw hearingsError
            setHearings(hearingsData || [])

            // Fetch opponents
            const { data: opponentsData, error: opponentsError } = await supabase
                .from('opponents')
                .select('*')
                .eq('case_id', id)

            if (opponentsError) throw opponentsError
            setOpponents(opponentsData || [])

            // Fetch documents from backend API
            try {
                const documentsResponse = await fetch(`http://localhost:8000/api/documents/case/${id}`)
                if (documentsResponse.ok) {
                    const documentsJson = await documentsResponse.json()
                    setDocuments(documentsJson.documents || [])
                }
            } catch (error) {
                console.error('Error fetching documents:', error)
            }
        } catch (error: any) {
            console.error('Error fetching case details:', error)
            toast.error('فشل تحميل البيانات')
        } finally {
            setLoading(false)
        }
    }

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

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gold-500"></div>
            </div>
        )
    }

    if (!caseData) {
        return (
            <div className="text-center py-12">
                <p className="text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>لم يتم العثور على القضية</p>
                <button onClick={() => navigate('/cases')} className="mt-4 text-gold-500">العودة</button>
            </div>
        )
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center gap-4">
                <button onClick={() => navigate('/cases')} className="p-2 hover:bg-obsidian-700 rounded-lg transition">
                    <ArrowRight className="w-5 h-5 text-gray-400" />
                </button>
                <div className="flex-1">
                    <div className="flex items-center gap-3">
                        <h1 className="text-3xl font-bold text-gold-500" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            {caseData.case_number}
                        </h1>
                        <span className={`px-3 py-1 rounded-full text-sm ${getStatusColor(caseData.status)}`} style={{ fontFamily: 'Cairo, sans-serif' }}>
                            {getStatusText(caseData.status)}
                        </span>
                    </div>
                    {caseData.subject && (
                        <p className="text-gray-400 mt-1" style={{ fontFamily: 'Cairo, sans-serif' }}>{caseData.subject}</p>
                    )}
                </div>
            </div>

            {/* Case Info Card */}
            <div className="backdrop-blur-xl bg-obsidian-800/70 border border-gold-500/20 rounded-xl p-6">
                <h2 className="text-xl font-bold text-white mb-4" style={{ fontFamily: 'Cairo, sans-serif' }}>
                    بيانات القضية
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                        <p className="text-xs text-gray-500 mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>الموكل</p>
                        <p className="text-white" style={{ fontFamily: 'Cairo, sans-serif' }}>{caseData.clients?.full_name}</p>
                    </div>
                    {caseData.court_name && (
                        <div>
                            <p className="text-xs text-gray-500 mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>المحكمة</p>
                            <p className="text-white" style={{ fontFamily: 'Cairo, sans-serif' }}>{caseData.court_name}</p>
                        </div>
                    )}
                    {caseData.court_circuit && (
                        <div>
                            <p className="text-xs text-gray-500 mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>الدائرة</p>
                            <p className="text-white" style={{ fontFamily: 'Cairo, sans-serif' }}>{caseData.court_circuit}</p>
                        </div>
                    )}
                    {caseData.case_type && (
                        <div>
                            <p className="text-xs text-gray-500 mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>نوع القضية</p>
                            <p className="text-white" style={{ fontFamily: 'Cairo, sans-serif' }}>{caseData.case_type}</p>
                        </div>
                    )}
                    {caseData.case_year && (
                        <div>
                            <p className="text-xs text-gray-500 mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>السنة</p>
                            <p className="text-white" style={{ fontFamily: 'Cairo, sans-serif' }}>{caseData.case_year}</p>
                        </div>
                    )}
                    {caseData.client_capacity && (
                        <div>
                            <p className="text-xs text-gray-500 mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>صفة الموكل</p>
                            <p className="text-white" style={{ fontFamily: 'Cairo, sans-serif' }}>{caseData.client_capacity}</p>
                        </div>
                    )}
                </div>

                {caseData.summary && (
                    <div className="mt-4 pt-4 border-t border-gold-500/10">
                        <p className="text-xs text-gray-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>الملخص</p>
                        <p className="text-white text-sm" style={{ fontFamily: 'Cairo, sans-serif' }}>{caseData.summary}</p>
                    </div>
                )}
            </div>

            {/* Opponents Card */}
            <div className="backdrop-blur-xl bg-obsidian-800/70 border border-gold-500/20 rounded-xl p-6">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                        <Users className="w-5 h-5 text-gold-500" />
                        <h2 className="text-xl font-bold text-white" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            الخصوم ({opponents.length})
                        </h2>
                    </div>
                    <button
                        onClick={() => setShowAddOpponentModal(true)}
                        className="flex items-center gap-2 px-4 py-2 bg-transparent border-2 border-gold-500 text-white font-bold rounded-lg hover:bg-gold-500/10 transition-all"
                        style={{ fontFamily: 'Cairo, sans-serif' }}
                    >
                        <Plus className="w-4 h-4" />
                        <span>إضافة خصم</span>
                    </button>
                </div>

                {opponents.length === 0 ? (
                    <div className="text-center py-8">
                        <Users className="w-12 h-12 text-gray-600 mx-auto mb-3" />
                        <p className="text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>لا يوجد خصوم</p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {opponents.map(opponent => (
                            <div key={opponent.id} className="bg-obsidian-900/50 rounded-lg p-3 border border-gold-500/10 group relative">
                                <button
                                    onClick={async () => {
                                        if (confirm('هل تريد حذف هذا الخصم؟')) {
                                            try {
                                                const { error } = await supabase
                                                    .from('opponents')
                                                    .delete()
                                                    .eq('id', opponent.id)

                                                if (error) throw error

                                                // ✅ تسجيل حذف الخصم
                                                await logAction(
                                                    'delete',
                                                    'opponents',
                                                    opponent.id,
                                                    opponent,
                                                    null,
                                                    'حذف خصم من القضية'
                                                )

                                                toast.success('تم حذف الخصم')
                                                fetchCaseDetails()
                                            } catch (error) {
                                                toast.error('فشل حذف الخصم')
                                            }
                                        }
                                    }}
                                    className="absolute top-2 left-2 p-1 bg-red-500/20 text-red-400 rounded opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-500/30"
                                >
                                    <X className="w-4 h-4" />
                                </button>
                                <p className="text-white font-medium mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>{opponent.full_name}</p>
                                <div className="flex items-center gap-3 text-sm">
                                    {opponent.capacity && (
                                        <span className="text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                            {opponent.capacity}
                                        </span>
                                    )}
                                    {opponent.national_id && (
                                        <span className="text-gray-500" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                            {opponent.national_id}
                                        </span>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Hearings Section */}
            <div className="backdrop-blur-xl bg-obsidian-800/70 border border-gold-500/20 rounded-xl p-6">
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-2">
                        <Calendar className="w-5 h-5 text-gold-500" />
                        <h2 className="text-xl font-bold text-white" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            الجلسات ({hearings.length})
                        </h2>
                    </div>
                    <button
                        onClick={() => setShowAddHearingModal(true)}
                        className="flex items-center gap-2 px-4 py-2 bg-transparent border-2 border-gold-500 text-white font-bold rounded-lg hover:bg-gold-500/10 transition-all"
                        style={{ fontFamily: 'Cairo, sans-serif' }}
                    >
                        <Plus className="w-4 h-4" />
                        <span>إضافة جلسة</span>
                    </button>
                </div>

                {hearings.length === 0 ? (
                    <div className="text-center py-12">
                        <Calendar className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                        <p className="text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>لا توجد جلسات مسجلة</p>
                    </div>
                ) : (
                    <div className="space-y-4">
                        {hearings.map((hearing, index) => (
                            <motion.div
                                key={hearing.id}
                                initial={{ opacity: 1, y: 0 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: index * 0.05 }}
                                className="bg-obsidian-900/50 border border-gold-500/10 rounded-lg p-4"
                            >
                                <div className="flex items-start justify-between mb-3">
                                    <div className="flex items-center gap-3">
                                        <Calendar className="w-5 h-5 text-gold-500" />
                                        <div>
                                            <p className="text-white font-bold" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                                {new Date(hearing.hearing_date).toLocaleDateString('ar-EG', {
                                                    weekday: 'long',
                                                    year: 'numeric',
                                                    month: 'long',
                                                    day: 'numeric'
                                                })}
                                            </p>
                                            {hearing.hearing_time && (
                                                <p className="text-sm text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                                    {hearing.hearing_time}
                                                </p>
                                            )}
                                        </div>
                                    </div>
                                    {/* Action Buttons */}
                                    <div className="flex items-center gap-2">
                                        <button
                                            onClick={() => {
                                                setEditingHearing(hearing)
                                                setShowEditHearingModal(true)
                                            }}
                                            className="p-2 hover:bg-blue-500/20 text-blue-400 rounded-lg transition-colors"
                                            title="تعديل"
                                        >
                                            <Edit2 className="w-4 h-4" />
                                        </button>
                                        <button
                                            onClick={async () => {
                                                if (confirm('هل تريد حذف هذه الجلسة؟')) {
                                                    try {
                                                        const { error } = await supabase
                                                            .from('hearings')
                                                            .delete()
                                                            .eq('id', hearing.id)

                                                        if (error) throw error

                                                        // ✅ تسجيل حذف الجلسة
                                                        await logAction(
                                                            'delete',
                                                            'hearings',
                                                            hearing.id,
                                                            hearing,
                                                            null,
                                                            'حذف جلسة'
                                                        )

                                                        toast.success('تم حذف الجلسة')
                                                        fetchCaseDetails()
                                                    } catch (error) {
                                                        toast.error('فشل حذف الجلسة')
                                                    }
                                                }
                                            }}
                                            className="p-2 hover:bg-red-500/20 text-red-400 rounded-lg transition-colors"
                                            title="حذف"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm mb-3">
                                    {hearing.court_room && (
                                        <div className="flex items-center gap-2">
                                            <MapPin className="w-4 h-4 text-gray-500" />
                                            <span className="text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                                قاعة: {hearing.court_room}
                                            </span>
                                        </div>
                                    )}
                                    {hearing.judge_name && (
                                        <div className="flex items-center gap-2">
                                            <Gavel className="w-4 h-4 text-gray-500" />
                                            <span className="text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                                {hearing.judge_name}
                                            </span>
                                        </div>
                                    )}
                                    {hearing.next_hearing_date && (
                                        <div className="flex items-center gap-2">
                                            <Calendar className="w-4 h-4 text-gray-500" />
                                            <span className="text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                                الجلسة القادمة: {new Date(hearing.next_hearing_date).toLocaleDateString('ar-EG')}
                                            </span>
                                        </div>
                                    )}
                                </div>

                                {hearing.judge_requests && (
                                    <div className="mb-2">
                                        <p className="text-xs text-gray-500 mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>طلبات القاضي:</p>
                                        <p className="text-white text-sm" style={{ fontFamily: 'Cairo, sans-serif' }}>{hearing.judge_requests}</p>
                                    </div>
                                )}

                                {hearing.outcome && (
                                    <div className="mb-2">
                                        <p className="text-xs text-gray-500 mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>النتيجة:</p>
                                        <p className="text-white text-sm" style={{ fontFamily: 'Cairo, sans-serif' }}>{hearing.outcome}</p>
                                    </div>
                                )}

                                {hearing.notes && (
                                    <div>
                                        <p className="text-xs text-gray-500 mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>ملاحظات:</p>
                                        <p className="text-gray-400 text-sm" style={{ fontFamily: 'Cairo, sans-serif' }}>{hearing.notes}</p>
                                    </div>
                                )}
                            </motion.div>
                        ))}
                    </div>
                )}
            </div>

            {/* Documents Section */}
            <div className="backdrop-blur-xl bg-obsidian-800/70 border border-gold-500/20 rounded-xl p-6">
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-2">
                        <FileText className="w-5 h-5 text-gold-500" />
                        <h2 className="text-xl font-bold text-white" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            المستندات ({documents.length})
                        </h2>
                    </div>
                    <button
                        onClick={() => setShowUploadModal(true)}
                        className="flex items-center gap-2 px-4 py-2 bg-transparent border-2 border-gold-500 text-white font-bold rounded-lg hover:bg-gold-500/10 transition-all"
                        style={{ fontFamily: 'Cairo, sans-serif' }}
                    >
                        <Plus className="w-4 h-4" />
                        <span>رفع مستند</span>
                    </button>
                </div>

                {documents.length === 0 ? (
                    <div className="text-center py-12">
                        <FileText className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                        <p className="text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>لا توجد مستندات</p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {documents.map((doc) => (
                            <div key={doc.id} className="bg-obsidian-900/50 border border-gold-500/10 rounded-lg p-4">
                                <div className="flex items-start justify-between mb-3">
                                    <div className="flex-1">
                                        <h3 className="text-white font-medium mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                            {doc.document_type || 'مستند'}
                                        </h3>
                                        <p className="text-xs text-gray-500 mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                            {doc.file_name}
                                        </p>
                                        <p className="text-xs text-gray-500" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                            {(doc.file_size / 1024).toFixed(2)} KB • {new Date(doc.created_at).toLocaleDateString('ar-EG')}
                                        </p>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <span className="px-2 py-1 text-xs rounded bg-blue-500/20 text-blue-400" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                            {doc.file_type.toUpperCase()}
                                        </span>
                                        {/* Action Buttons */}
                                        <button
                                            onClick={() => {
                                                // ✅ FIX: استخدام URL كامل للمستند
                                                const fullUrl = doc.file_url.startsWith('http')
                                                    ? doc.file_url
                                                    : `http://localhost:8000${doc.file_url}`
                                                window.open(fullUrl, '_blank')
                                            }}
                                            className="p-2 hover:bg-green-500/20 text-green-400 rounded-lg transition-colors"
                                            title="عرض المستند"
                                        >
                                            <Eye className="w-4 h-4" />
                                        </button>
                                        <button
                                            onClick={async () => {
                                                // ✅ FIX: تنزيل صحيح باستخدام fetch
                                                try {
                                                    const fullUrl = doc.file_url.startsWith('http')
                                                        ? doc.file_url
                                                        : `http://localhost:8000${doc.file_url}`

                                                    const response = await fetch(fullUrl)
                                                    const blob = await response.blob()
                                                    const url = window.URL.createObjectURL(blob)
                                                    const link = document.createElement('a')
                                                    link.href = url
                                                    link.download = doc.file_name
                                                    document.body.appendChild(link)
                                                    link.click()
                                                    document.body.removeChild(link)
                                                    window.URL.revokeObjectURL(url)
                                                } catch (error) {
                                                    toast.error('فشل تنزيل المستند')
                                                }
                                            }}
                                            className="p-2 hover:bg-blue-500/20 text-blue-400 rounded-lg transition-colors"
                                            title="تنزيل"
                                        >
                                            <Download className="w-4 h-4" />
                                        </button>
                                        <button
                                            onClick={async () => {
                                                if (confirm('هل تريد حذف هذا المستند؟')) {
                                                    try {
                                                        // Delete from backend API
                                                        const response = await fetch(`http://localhost:8000/api/documents/${doc.id}`, {
                                                            method: 'DELETE'
                                                        })

                                                        if (!response.ok) {
                                                            throw new Error('فشل حذف المستند')
                                                        }

                                                        // ✅ تسجيل حذف المستند
                                                        await logAction(
                                                            'delete',
                                                            'documents',
                                                            doc.id,
                                                            doc,
                                                            null,
                                                            'حذف مستند'
                                                        )

                                                        toast.success('تم حذف المستند')
                                                        fetchCaseDetails()
                                                    } catch (error) {
                                                        toast.error('فشل حذف المستند')
                                                        console.error(error)
                                                    }
                                                }
                                            }}
                                            className="p-2 hover:bg-red-500/20 text-red-400 rounded-lg transition-colors"
                                            title="حذف"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </div>
                                </div>

                                {/* OCR Status */}
                                {doc.ocr_enabled && (
                                    <div className="mb-2">
                                        <div className="flex items-center gap-2 text-xs mb-1">
                                            <span className="text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>استخراج النص:</span>
                                            <span className={`px-2 py-0.5 rounded ${doc.ocr_status === 'completed' ? 'bg-green-500/20 text-green-400' :
                                                doc.ocr_status === 'processing' ? 'bg-yellow-500/20 text-yellow-400' :
                                                    doc.ocr_status === 'failed' ? 'bg-red-500/20 text-red-400' :
                                                        'bg-gray-500/20 text-gray-400'
                                                }`} style={{ fontFamily: 'Cairo, sans-serif' }}>
                                                {doc.ocr_status === 'completed' ? 'مكتمل' :
                                                    doc.ocr_status === 'processing' ? 'جاري...' :
                                                        doc.ocr_status === 'failed' ? 'فشل' : 'معلق'}
                                            </span>
                                            {doc.word_count > 0 && (
                                                <span className="text-gray-500" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                                    ({doc.word_count} كلمة)
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                )}

                                {/* AI Summary Status */}
                                {doc.ocr_enabled && doc.ocr_status === 'completed' && (
                                    <div className="mb-2">
                                        <div className="flex items-center gap-2 text-xs mb-1">
                                            <span className="text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>التلخيص:</span>
                                            <span className={`px-2 py-0.5 rounded ${doc.summary_status === 'completed' ? 'bg-green-500/20 text-green-400' :
                                                doc.summary_status === 'processing' ? 'bg-yellow-500/20 text-yellow-400' :
                                                    doc.summary_status === 'failed' ? 'bg-red-500/20 text-red-400' :
                                                        'bg-gray-500/20 text-gray-400'
                                                }`} style={{ fontFamily: 'Cairo, sans-serif' }}>
                                                {doc.summary_status === 'completed' ? 'مكتمل' :
                                                    doc.summary_status === 'processing' ? 'جاري...' :
                                                        doc.summary_status === 'failed' ? 'فشل' : 'معلق'}
                                            </span>
                                        </div>
                                    </div>
                                )}

                                {/* Show Summary */}
                                {doc.ai_summary && (
                                    <div className="mt-3 p-3 bg-obsidian-800/50 rounded border border-gold-500/10">
                                        <p className="text-xs text-gray-400 mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>الملخص:</p>
                                        <p className="text-sm text-white" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                            {doc.ai_summary}
                                        </p>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Add Hearing Modal */}
            {showAddHearingModal && (
                <AddHearingModal
                    caseId={caseData.id}
                    caseNumber={caseData.case_number}
                    onClose={() => setShowAddHearingModal(false)}
                    onSuccess={() => {
                        setShowAddHearingModal(false)
                        fetchCaseDetails()
                    }}
                />
            )}

            {/* Edit Hearing Modal */}
            {showEditHearingModal && editingHearing && (
                <EditHearingModal
                    hearing={editingHearing}
                    caseNumber={caseData.case_number}
                    onClose={() => {
                        setShowEditHearingModal(false)
                        setEditingHearing(null)
                    }}
                    onSuccess={() => {
                        setShowEditHearingModal(false)
                        setEditingHearing(null)
                        fetchCaseDetails()
                    }}
                />
            )}

            {/* Add Opponent Modal */}
            {showAddOpponentModal && (
                <AddOpponentModal
                    caseId={caseData.id}
                    caseNumber={caseData.case_number}
                    onClose={() => setShowAddOpponentModal(false)}
                    onSuccess={() => {
                        setShowAddOpponentModal(false)
                        fetchCaseDetails()
                    }}
                />
            )}

            {/* Upload Document Modal */}
            {showUploadModal && caseData && (
                <UploadDocumentModal
                    caseId={caseData.id}
                    clientId={caseData.client_id}
                    lawyerId={getEffectiveLawyerId()!}  // ✅ FIXED: use getEffectiveLawyerId
                    caseNumber={caseData.case_number}
                    onClose={() => setShowUploadModal(false)}
                    onSuccess={() => {
                        setShowUploadModal(false)
                        fetchCaseDetails()
                    }}
                />
            )}
        </div>
    )
}

// UploadDocumentModal Component
import axios from 'axios'

interface UploadDocumentModalProps {
    caseId: string
    clientId: string
    lawyerId: string
    caseNumber: string
    onClose: () => void
    onSuccess: () => void
}

function UploadDocumentModal({
    caseId,
    clientId,
    lawyerId,
    caseNumber,
    onClose,
    onSuccess
}: UploadDocumentModalProps) {
    const { logAction } = useAuditLog()
    const [file, setFile] = useState<File | null>(null)
    const [documentType, setDocumentType] = useState('other')
    const [enableOCR, setEnableOCR] = useState(false)
    const [uploading, setUploading] = useState(false)
    const [extracting, setExtracting] = useState(false)
    const [summarizing, setSummarizing] = useState(false)

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            const selectedFile = e.target.files[0]
            // Validate file type - PDF and images only
            const allowedTypes = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg']
            if (!allowedTypes.includes(selectedFile.type)) {
                toast.error('نوع الملف غير مدعوم. يُرجى اختيار PDF أو صورة')
                e.target.value = '' // Reset
                return
            }
            setFile(selectedFile)
        }
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()

        if (!file) {
            toast.error('يُرجى اختيار ملف')
            return
        }

        try {
            setUploading(true)

            const formData = new FormData()
            formData.append('file', file)
            formData.append('case_id', caseId)
            formData.append('client_id', clientId)
            formData.append('lawyer_id', lawyerId)
            formData.append('file', file)
            formData.append('document_type', documentType || 'مستند')  // ✅ النص المخصص
            formData.append('enable_ocr', enableOCR.toString())

            const uploadResponse = await axios.post(
                'http://localhost:8000/api/documents/upload',
                formData,
                { headers: { 'Content-Type': 'multipart/form-data' } }
            )

            const documentId = uploadResponse.data.document.id

            // ✅ تسجيل رفع المستند
            await logAction(
                'create',
                'documents',
                documentId,
                null,
                {
                    file_name: file.name,
                    document_type: documentType,
                    enable_ocr: enableOCR
                },
                'رفع مستند جديد'
            )

            toast.success('تم رفع المستند بنجاح')

            // Refresh the documents list
            onSuccess()
        } catch (error: any) {
            toast.error(error.response?.data?.detail || 'فشل الرفع')
        } finally {
            setUploading(false)
        }
    }

    const isProcessing = uploading || extracting || summarizing

    return (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <motion.div initial={{ opacity: 1, scale: 1 }} animate={{ opacity: 1, scale: 1 }} className="backdrop-blur-xl bg-obsidian-800/90 border border-gold-500/20 rounded-2xl p-6 max-w-lg w-full">
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h2 className="text-2xl font-bold text-gold-500" style={{ fontFamily: 'Cairo, sans-serif' }}>رفع مستند</h2>
                        <p className="text-gray-400 text-sm mt-1" style={{ fontFamily: 'Cairo, sans-serif' }}>القضية: {caseNumber}</p>
                    </div>
                    <button onClick={onClose} disabled={isProcessing} className="text-gray-400 hover:text-white">
                        <X className="w-6 h-6" />
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>الملف *</label>
                        <input type="file" onChange={handleFileChange} accept=".pdf,.png,.jpg,.jpeg" className="hidden" id="file-upload" disabled={isProcessing} />
                        <label htmlFor="file-upload" className="flex items-center justify-center gap-2 w-full px-4 py-3 border-2 border-dashed border-gold-500/30 rounded-lg cursor-pointer hover:border-gold-500/50 bg-obsidian-900/30">
                            <Upload className="w-5 h-5 text-gold-500" />
                            <span className="text-white" style={{ fontFamily: 'Cairo, sans-serif' }}>{file ? file.name : 'اختر ملف'}</span>
                        </label>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>نوع/وصف المستند</label>
                        <input
                            type="text"
                            value={documentType}
                            onChange={(e) => setDocumentType(e.target.value)}
                            disabled={isProcessing}
                            placeholder="مثال: عقد إيجار، عقد بيع، صك، حكم..."
                            className="w-full px-3 py-2 text-sm bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white placeholder-gray-500"
                            style={{ fontFamily: 'Cairo, sans-serif' }}
                        />
                    </div>

                    <div className="flex items-center gap-3 p-3 bg-obsidian-900/30 rounded-lg border border-gold-500/10">
                        <input type="checkbox" id="enable-ocr" checked={enableOCR} onChange={(e) => setEnableOCR(e.target.checked)} disabled={isProcessing} className="w-4 h-4 rounded" />
                        <label htmlFor="enable-ocr" className="flex-1 text-white text-sm" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            <span className="font-medium">تفعيل استخراج النص (OCR)</span>
                            <p className="text-xs text-gray-400 mt-1">استخراج وتلخيص تلقائي</p>
                        </label>
                    </div>

                    {isProcessing && (
                        <div className="p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                            <div className="flex items-center gap-3">
                                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500"></div>
                                <p className="text-blue-400 text-sm" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                    {uploading && 'جاري الرفع...'}
                                    {extracting && 'استخراج النص...'}
                                    {summarizing && 'التلخيص...'}
                                </p>
                            </div>
                        </div>
                    )}

                    <div className="flex gap-3 pt-4">
                        <button type="submit" disabled={!file || isProcessing} className="flex-1 px-6 py-3 bg-transparent border-2 border-gold-500 text-white font-bold rounded-lg hover:bg-gold-500/10 disabled:opacity-50" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            {uploading ? 'جاري...' : 'رفع'}
                        </button>
                        <button type="button" onClick={onClose} disabled={isProcessing} className="px-6 py-3 bg-obsidian-700 text-white rounded-lg" style={{ fontFamily: 'Cairo, sans-serif' }}>إلغاء</button>
                    </div>
                </form>
            </motion.div>
        </div>
    )
}

// Add Hearing Modal
interface AddHearingModalProps {
    caseId: string
    caseNumber: string
    onClose: () => void
    onSuccess: () => void
}

function AddHearingModal({ caseId, caseNumber, onClose, onSuccess }: AddHearingModalProps) {
    const { getEffectiveLawyerId } = useAuth()
    const { logAction } = useAuditLog()
    const [loading, setLoading] = useState(false)
    const [formData, setFormData] = useState({
        hearing_date: '',
        hearing_time: '',
        court_room: '',
        judge_name: '',
        judge_requests: '',
        notes: '',
        outcome: '',
        next_hearing_date: ''
    })

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()

        if (!formData.hearing_date) {
            toast.error('تاريخ الجلسة مطلوب')
            return
        }

        setLoading(true)

        try {
            const { data, error } = await supabase
                .from('hearings')
                .insert({
                    case_id: caseId,
                    lawyer_id: getEffectiveLawyerId(),  // ✅ يُسجل للمحامي
                    hearing_date: formData.hearing_date,
                    hearing_time: formData.hearing_time || null,
                    court_room: formData.court_room || null,
                    judge_name: formData.judge_name || null,
                    judge_requests: formData.judge_requests || null,
                    notes: formData.notes || null,
                    outcome: formData.outcome || null,
                    next_hearing_date: formData.next_hearing_date || null
                })
                .select()
                .single()

            if (error) throw error

            // ✅ تسجيل إضافة الجلسة
            if (data) {
                await logAction(
                    'create',
                    'hearings',
                    data.id,
                    null,
                    {
                        hearing_date: formData.hearing_date,
                        court_room: formData.court_room,
                        judge_name: formData.judge_name
                    },
                    'إضافة جلسة جديدة'
                )
            }

            toast.success('تمت إضافة الجلسة بنجاح')
            onSuccess()
        } catch (error: any) {
            console.error('Error adding hearing:', error)
            toast.error('فشل إضافة الجلسة')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="backdrop-blur-xl bg-obsidian-800/90 border border-gold-500/20 rounded-2xl p-6 max-w-3xl w-full"
            >
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h2 className="text-2xl font-bold text-gold-500" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            إضافة جلسة جديدة
                        </h2>
                        <p className="text-gray-400 text-sm mt-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            القضية: {caseNumber}
                        </p>
                    </div>
                    <button onClick={onClose} className="text-gray-400 hover:text-white">
                        <X className="w-6 h-6" />
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    {/* Date and Time */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <div>
                            <label className="block text-xs font-medium text-gold-500 mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                تاريخ الجلسة <span className="text-red-400">*</span>
                            </label>
                            <input
                                type="date"
                                value={formData.hearing_date}
                                onChange={(e) => setFormData({ ...formData, hearing_date: e.target.value })}
                                className="w-full px-3 py-2 text-sm bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white focus:outline-none focus:border-gold-500"
                                required
                            />
                        </div>
                        <div>
                            <label className="block text-xs font-medium text-gold-500 mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                الوقت
                            </label>
                            <input
                                type="time"
                                value={formData.hearing_time}
                                onChange={(e) => setFormData({ ...formData, hearing_time: e.target.value })}
                                className="w-full px-3 py-2 text-sm bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white focus:outline-none focus:border-gold-500"
                            />
                        </div>
                    </div>

                    {/* Court Room and Judge */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <div>
                            <label className="block text-xs font-medium text-gold-500 mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                رقم القاعة
                            </label>
                            <input
                                type="text"
                                value={formData.court_room}
                                onChange={(e) => setFormData({ ...formData, court_room: e.target.value })}
                                className="w-full px-3 py-2 text-sm bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold-500"
                                style={{ fontFamily: 'Cairo, sans-serif' }}
                                placeholder="مثال: 12"
                            />
                        </div>
                        <div>
                            <label className="block text-xs font-medium text-gold-500 mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                اسم القاضي
                            </label>
                            <input
                                type="text"
                                value={formData.judge_name}
                                onChange={(e) => setFormData({ ...formData, judge_name: e.target.value })}
                                className="w-full px-3 py-2 text-sm bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold-500"
                                style={{ fontFamily: 'Cairo, sans-serif' }}
                            />
                        </div>
                    </div>

                    {/* Judge Requests */}
                    <div>
                        <label className="block text-xs font-medium text-gold-500 mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            طلبات القاضي
                        </label>
                        <textarea
                            value={formData.judge_requests}
                            onChange={(e) => setFormData({ ...formData, judge_requests: e.target.value })}
                            className="w-full px-3 py-2 text-sm bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold-500 resize-none"
                            style={{ fontFamily: 'Cairo, sans-serif' }}
                            rows={2}
                        />
                    </div>

                    {/* Outcome */}
                    <div>
                        <label className="block text-xs font-medium text-gold-500 mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            نتيجة الجلسة
                        </label>
                        <textarea
                            value={formData.outcome}
                            onChange={(e) => setFormData({ ...formData, outcome: e.target.value })}
                            className="w-full px-3 py-2 text-sm bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold-500 resize-none"
                            style={{ fontFamily: 'Cairo, sans-serif' }}
                            rows={2}
                        />
                    </div>

                    {/* Notes */}
                    <div>
                        <label className="block text-xs font-medium text-gold-500 mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            ملاحظات
                        </label>
                        <textarea
                            value={formData.notes}
                            onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                            className="w-full px-3 py-2 text-sm bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold-500 resize-none"
                            style={{ fontFamily: 'Cairo, sans-serif' }}
                            rows={2}
                        />
                    </div>

                    {/* Next Hearing Date */}
                    <div>
                        <label className="block text-xs font-medium text-gold-500 mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            تاريخ الجلسة القادمة
                        </label>
                        <input
                            type="date"
                            value={formData.next_hearing_date}
                            onChange={(e) => setFormData({ ...formData, next_hearing_date: e.target.value })}
                            className="w-full px-3 py-2 text-sm bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white focus:outline-none focus:border-gold-500"
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
                            {loading ? 'جاري الحفظ...' : 'حفظ الجلسة'}
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

// Edit Hearing Modal
interface EditHearingModalProps {
    hearing: Hearing
    caseNumber: string
    onClose: () => void
    onSuccess: () => void
}

function EditHearingModal({ hearing, caseNumber, onClose, onSuccess }: EditHearingModalProps) {
    const { profile } = useAuth()
    const { logAction } = useAuditLog()
    const [loading, setLoading] = useState(false)
    const [formData, setFormData] = useState({
        hearing_date: hearing.hearing_date,
        hearing_time: hearing.hearing_time || '',
        court_room: hearing.court_room || '',
        judge_name: hearing.judge_name || '',
        judge_requests: hearing.judge_requests || '',
        notes: hearing.notes || '',
        outcome: hearing.outcome || '',
        next_hearing_date: hearing.next_hearing_date || ''
    })

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!formData.hearing_date) {
            toast.error('تاريخ الجلسة مطلوب')
            return
        }
        setLoading(true)
        try {
            const { error } = await supabase
                .from('hearings')
                .update({
                    hearing_date: formData.hearing_date,
                    hearing_time: formData.hearing_time || null,
                    court_room: formData.court_room || null,
                    judge_name: formData.judge_name || null,
                    judge_requests: formData.judge_requests || null,
                    notes: formData.notes || null,
                    outcome: formData.outcome || null,
                    next_hearing_date: formData.next_hearing_date || null
                })
                .eq('id', hearing.id)
            if (error) throw error

            // ✅ تسجيل تعديل الجلسة
            await logAction(
                'update',
                'hearings',
                hearing.id,
                hearing,
                { ...hearing, ...formData },
                'تعديل تفاصيل الجلسة'
            )

            toast.success('تم تحديث الجلسة بنجاح')
            onSuccess()
        } catch (error: any) {
            toast.error('فشل تحديث الجلسة')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="backdrop-blur-xl bg-obsidian-800/90 border border-gold-500/20 rounded-2xl p-6 max-w-3xl w-full max-h-[90vh] overflow-y-auto">
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h2 className="text-2xl font-bold text-gold-500" style={{ fontFamily: 'Cairo, sans-serif' }}>تعديل الجلسة</h2>
                        <p className="text-gray-400 text-sm mt-1" style={{ fontFamily: 'Cairo, sans-serif' }}>القضية: {caseNumber}</p>
                    </div>
                    <button onClick={onClose} className="text-gray-400 hover:text-white"><X className="w-6 h-6" /></button>
                </div>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-xs font-medium text-gold-500 mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>تاريخ الجلسة *</label>
                            <input type="date" value={formData.hearing_date} onChange={(e) => setFormData({ ...formData, hearing_date: e.target.value })} className="w-full px-3 py-2 text-sm bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white" required />
                        </div>
                        <div>
                            <label className="block text-xs font-medium text-gold-500 mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>وقت الجلسة</label>
                            <input type="time" value={formData.hearing_time} onChange={(e) => setFormData({ ...formData, hearing_time: e.target.value })} className="w-full px-3 py-2 text-sm bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white" />
                        </div>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-xs font-medium text-gold-500 mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>قاعة المحكمة</label>
                            <input type="text" value={formData.court_room} onChange={(e) => setFormData({ ...formData, court_room: e.target.value })} className="w-full px-3 py-2 text-sm bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white" placeholder="مثال: الدائرة الثانية" style={{ fontFamily: 'Cairo, sans-serif' }} />
                        </div>
                        <div>
                            <label className="block text-xs font-medium text-gold-500 mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>اسم القاضي</label>
                            <input type="text" value={formData.judge_name} onChange={(e) => setFormData({ ...formData, judge_name: e.target.value })} className="w-full px-3 py-2 text-sm bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white" style={{ fontFamily: 'Cairo, sans-serif' }} /></div>
                    </div>
                    <div>
                        <label className="block text-xs font-medium text-gold-500 mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>طلبات القاضي</label>
                        <textarea value={formData.judge_requests} onChange={(e) => setFormData({ ...formData, judge_requests: e.target.value })} className="w-full px-3 py-2 text-sm bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white resize-none" rows={3} style={{ fontFamily: 'Cairo, sans-serif' }} />
                    </div>
                    <div>
                        <label className="block text-xs font-medium text-gold-500 mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>ملاحظات</label>
                        <textarea value={formData.notes} onChange={(e) => setFormData({ ...formData, notes: e.target.value })} className="w-full px-3 py-2 text-sm bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white resize-none" rows={3} style={{ fontFamily: 'Cairo, sans-serif' }} />
                    </div>
                    <div>
                        <label className="block text-xs font-medium text-gold-500 mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>نتيجة الجلسة</label>
                        <textarea value={formData.outcome} onChange={(e) => setFormData({ ...formData, outcome: e.target.value })} className="w-full px-3 py-2 text-sm bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white resize-none" rows={3} style={{ fontFamily: 'Cairo, sans-serif' }} />
                    </div>
                    <div>
                        <label className="block text-xs font-medium text-gold-500 mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>تاريخ الجلسة القادمة</label>
                        <input type="date" value={formData.next_hearing_date} onChange={(e) => setFormData({ ...formData, next_hearing_date: e.target.value })} className="w-full px-3 py-2 text-sm bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white" />
                    </div>
                    <div className="flex gap-3 pt-4">
                        <button type="submit" disabled={loading} className="flex-1 px-6 py-3 bg-transparent border-2 border-gold-500 text-white font-bold rounded-lg hover:bg-gold-500/10" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            {loading ? 'جاري الحفظ...' : 'حفظ التعديلات'}
                        </button>
                        <button type="button" onClick={onClose} className="px-6 py-3 bg-obsidian-700 text-white rounded-lg" style={{ fontFamily: 'Cairo, sans-serif' }}>إلغاء</button>
                    </div>
                </form>
            </motion.div>
        </div>
    )
}

// Add Opponent Modal
interface AddOpponentModalProps {
    caseId: string
    caseNumber: string
    onClose: () => void
    onSuccess: () => void
}

function AddOpponentModal({ caseId, caseNumber, onClose, onSuccess }: AddOpponentModalProps) {
    const { logAction } = useAuditLog()
    const [loading, setLoading] = useState(false)
    const [formData, setFormData] = useState({
        full_name: '',
        national_id: '',
        capacity: ''
    })

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()

        if (!formData.full_name.trim()) {
            toast.error('اسم الخصم مطلوب')
            return
        }

        setLoading(true)

        try {
            const { data, error } = await supabase
                .from('opponents')
                .insert({
                    case_id: caseId,
                    full_name: formData.full_name,
                    national_id: formData.national_id || null,
                    capacity: formData.capacity || null
                })
                .select()
                .single()

            if (error) throw error

            // ✅ تسجيل إضافة الخصم
            if (data) {
                await logAction(
                    'create',
                    'opponents',
                    data.id,
                    null,
                    { full_name: formData.full_name, capacity: formData.capacity },
                    'إضافة خصم جديد'
                )
            }

            toast.success('تمت إضافة الخصم بنجاح')
            onSuccess()
        } catch (error: any) {
            console.error('Error adding opponent:', error)
            toast.error('فشل إضافة الخصم')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="backdrop-blur-xl bg-obsidian-800/90 border border-gold-500/20 rounded-2xl p-6 max-w-lg w-full"
            >
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h2 className="text-2xl font-bold text-gold-500" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            إضافة خصم جديد
                        </h2>
                        <p className="text-gray-400 text-sm mt-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            القضية: {caseNumber}
                        </p>
                    </div>
                    <button onClick={onClose} className="text-gray-400 hover:text-white">
                        <X className="w-6 h-6" />
                    </button>
                </div>

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
                            className="w-full px-3 py-2 text-sm bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold-500"
                            style={{ fontFamily: 'Cairo, sans-serif' }}
                            placeholder="أدخل الاسم الكامل"
                            required
                        />
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
                            className="w-full px-3 py-2 text-sm bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold-500"
                            style={{ fontFamily: 'Cairo, sans-serif' }}
                            placeholder="1xxxxxxxxx"
                        />
                    </div>

                    {/* Capacity */}
                    <div>
                        <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            الصفة
                        </label>
                        <select
                            value={formData.capacity}
                            onChange={(e) => setFormData({ ...formData, capacity: e.target.value })}
                            className="w-full px-3 py-2 text-sm bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white focus:outline-none focus:border-gold-500"
                            style={{ fontFamily: 'Cairo, sans-serif' }}
                        >
                            <option value="">اختر الصفة</option>
                            <option value="مدعي">مدعي</option>
                            <option value="مدعى عليه">مدعى عليه</option>
                            <option value="مستأنف">مستأنف</option>
                            <option value="مستأنف ضده">مستأنف ضده</option>
                        </select>
                    </div>

                    {/* Buttons */}
                    <div className="flex gap-3 pt-4">
                        <button
                            type="submit"
                            disabled={loading}
                            className="flex-1 px-6 py-3 bg-transparent border-2 border-gold-500 text-white font-bold rounded-lg hover:bg-gold-500/10 transition-all disabled:opacity-50"
                            style={{ fontFamily: 'Cairo, sans-serif' }}
                        >
                            {loading ? 'جاري الحفظ...' : 'إضافة'}
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
