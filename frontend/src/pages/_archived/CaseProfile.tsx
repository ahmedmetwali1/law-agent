import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
    Briefcase, Calendar, FileText, Scale,
    ArrowRight, Plus, Upload, Brain,
    Clock, Shield, AlertCircle
} from 'lucide-react'
import { supabase } from '../supabaseClient'
import { toast } from 'sonner'
import { format } from 'date-fns'
import { ar } from 'date-fns/locale'

interface Case {
    id: string
    case_number: string
    court_name: string
    case_type: string
    status: 'نشطة' | 'مغلقة' | 'معلقة'
    description: string
    created_at: string
    client: {
        id: string
        full_name: string
        phone_number: string
    }
}

interface Hearing {
    id: string
    hearing_date: string
    hearing_time: string
    notes: string
    judge_name: string
}

export function CaseProfile() {
    const { id } = useParams()
    const navigate = useNavigate()
    const [caseData, setCaseData] = useState<Case | null>(null)
    const [hearings, setHearings] = useState<Hearing[]>([])
    const [activeTab, setActiveTab] = useState<'overview' | 'hearings' | 'documents'>('overview')
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        if (id) fetchCaseData()
    }, [id])

    const fetchCaseData = async () => {
        try {
            setLoading(true)

            // Fetch Case Details
            const { data: caseResult, error: caseError } = await supabase
                .from('cases')
                .select(`
          *,
          client:clients (id, full_name, phone_number)
        `)
                .eq('id', id)
                .single()

            if (caseError) throw caseError
            setCaseData(caseResult)

            // Fetch Hearings
            const { data: hearingsResult, error: hearingsError } = await supabase
                .from('hearings')
                .select('*')
                .eq('case_id', id)
                .order('hearing_date', { ascending: false })

            if (hearingsError) throw hearingsError
            setHearings(hearingsResult || [])

        } catch (error) {
            console.error('Error fetching case data:', error)
            toast.error('فشل تحميل بيانات القضية')
        } finally {
            setLoading(false)
        }
    }

    if (loading) return <div className="text-center py-20">جاري التحميل...</div>
    if (!caseData) return <div className="text-center py-20">القضية غير موجودة</div>

    return (
        <div className="space-y-6">
            {/* Header with Navigation */}
            <div className="flex items-center gap-4">
                <button
                    onClick={() => navigate('/cases')}
                    className="p-2 hover:bg-obsidian-800 rounded-lg text-gray-400 hover:text-white transition-colors"
                >
                    <ArrowRight className="w-5 h-5" />
                </button>
                <div>
                    <h1 className="text-2xl font-bold text-white flex items-center gap-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        القضية رقم {caseData.case_number}
                    </h1>
                    <p className="text-gray-400 text-sm" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        الموكل: {caseData.client.full_name}
                    </p>
                </div>
                <div className="mr-auto flex gap-2">
                    <span className={`px-3 py-1 rounded-md text-sm font-medium ${caseData.status === 'نشطة' ? 'bg-green-500/10 text-green-400 border border-green-500/20' :
                            caseData.status === 'مغلقة' ? 'bg-gray-500/10 text-gray-400 border border-gray-500/20' :
                                'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20'
                        }`} style={{ fontFamily: 'Cairo, sans-serif' }}>
                        {caseData.status}
                    </span>
                </div>
            </div>

            {/* Tabs */}
            <div className="flex gap-4 border-b border-gold-500/20 pb-1">
                {[
                    { id: 'overview', label: 'نظرة عامة', icon: Scale },
                    { id: 'hearings', label: 'الجلسات', icon: Calendar },
                    { id: 'documents', label: 'المستندات', icon: FileText }
                ].map(tab => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id as any)}
                        className={`flex items-center gap-2 px-4 py-2 border-b-2 transition-colors ${activeTab === tab.id
                                ? 'border-gold-500 text-gold-500'
                                : 'border-transparent text-gray-400 hover:text-white'
                            }`}
                    >
                        <tab.icon className="w-4 h-4" />
                        <span style={{ fontFamily: 'Cairo, sans-serif' }}>{tab.label}</span>
                    </button>
                ))}
            </div>

            {/* Content */}
            <div className="min-h-[400px]">
                {activeTab === 'overview' && (
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="grid grid-cols-1 md:grid-cols-2 gap-6"
                    >
                        {/* Info Card */}
                        <div className="backdrop-blur-xl bg-obsidian-800/70 border border-gold-500/20 rounded-xl p-6">
                            <h3 className="text-lg font-bold text-gold-500 mb-4 flex items-center gap-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                <Shield className="w-5 h-5" />
                                تفاصيل القضية
                            </h3>
                            <div className="space-y-4">
                                <div className="flex justify-between border-b border-gold-500/10 pb-2">
                                    <span className="text-gray-400">المحكمة</span>
                                    <span className="text-white">{caseData.court_name}</span>
                                </div>
                                <div className="flex justify-between border-b border-gold-500/10 pb-2">
                                    <span className="text-gray-400">نوع القضية</span>
                                    <span className="text-white">{caseData.case_type}</span>
                                </div>
                                <div className="flex justify-between border-b border-gold-500/10 pb-2">
                                    <span className="text-gray-400">تاريخ الفتح</span>
                                    <span className="text-white">
                                        {format(new Date(caseData.created_at), 'PPP', { locale: ar })}
                                    </span>
                                </div>
                                <div className="pt-2">
                                    <p className="text-gray-400 mb-1">الوصف</p>
                                    <p className="text-gray-300 text-sm leading-relaxed bg-obsidian-900/50 p-3 rounded-lg">
                                        {caseData.description || 'لا يوجد وصف متاح'}
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* AI Assistant Card (Future Feature) */}
                        <div className="backdrop-blur-xl bg-gradient-to-br from-obsidian-800/70 to-blue-900/20 border border-blue-500/20 rounded-xl p-6">
                            <h3 className="text-lg font-bold text-blue-400 mb-4 flex items-center gap-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                <Brain className="w-5 h-5" />
                                تحليل الذكاء الاصطناعي
                            </h3>
                            <div className="space-y-3">
                                <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-3">
                                    <p className="text-sm text-blue-200">
                                        بناءً على المعطيات الحالية، نسبة النجاح المتوقعة هي 75%. يُنصح بتقديم مستندات الإثبات قبل الجلسة القادمة.
                                    </p>
                                </div>
                                <button className="w-full py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors text-sm">
                                    طلب تحليل كامل
                                </button>
                            </div>
                        </div>
                    </motion.div>
                )}

                {activeTab === 'hearings' && (
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="space-y-4"
                    >
                        <div className="flex justify-end">
                            <button className="flex items-center gap-2 px-4 py-2 bg-gold-600 hover:bg-gold-500 text-obsidian-900 font-bold rounded-lg transition-colors">
                                <Plus className="w-4 h-4" />
                                <span>إضافة جلسة</span>
                            </button>
                        </div>

                        {hearings.length === 0 ? (
                            <div className="text-center py-10 bg-obsidian-800/30 border border-gold-500/10 rounded-xl border-dashed">
                                <Calendar className="w-10 h-10 text-gray-600 mx-auto mb-2" />
                                <p className="text-gray-500">لا توجد جلسات مسجلة</p>
                            </div>
                        ) : (
                            hearings.map(hearing => (
                                <div key={hearing.id} className="backdrop-blur-xl bg-obsidian-800/70 border border-gold-500/20 rounded-xl p-4 flex gap-4">
                                    <div className="flex flex-col items-center justify-center p-3 bg-obsidian-900 rounded-lg min-w-[80px] text-gold-500 border border-gold-500/20">
                                        <span className="text-2xl font-bold">{format(new Date(hearing.hearing_date), 'd')}</span>
                                        <span className="text-xs">{format(new Date(hearing.hearing_date), 'MMM', { locale: ar })}</span>
                                    </div>
                                    <div className="flex-1">
                                        <div className="flex justify-between mb-2">
                                            <h4 className="font-bold text-white text-lg">جلسة محكمة</h4>
                                            <span className="flex items-center gap-1 text-sm text-gray-400">
                                                <Clock className="w-3 h-3" />
                                                {hearing.hearing_time}
                                            </span>
                                        </div>
                                        <p className="text-gray-400 text-sm mb-2">{hearing.notes}</p>
                                        {hearing.judge_name && (
                                            <p className="text-xs text-gold-500 flex items-center gap-1">
                                                <Scale className="w-3 h-3" />
                                                القاضي: {hearing.judge_name}
                                            </p>
                                        )}
                                    </div>
                                </div>
                            ))
                        )}
                    </motion.div>
                )}

                {activeTab === 'documents' && (
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="text-center py-12"
                    >
                        <div className="border-2 border-dashed border-gray-700 rounded-xl p-10 hover:border-gold-500/50 transition-colors cursor-pointer bg-obsidian-800/30">
                            <Upload className="w-12 h-12 text-gray-500 mx-auto mb-4" />
                            <h3 className="text-lg font-medium text-white mb-2">رفع مستندات</h3>
                            <p className="text-gray-500 text-sm">اسحب الملفات هنا أو اضغط للاستعراض</p>
                        </div>
                    </motion.div>
                )}
            </div>
        </div>
    )
}
