import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
    Calendar, Clock, MapPin, User, Gavel,
    Search, Filter, ChevronLeft, ChevronRight,
    Shield, CheckCircle2, AlertCircle
} from 'lucide-react'
import { apiClient } from '../api/client'
import { useAuth } from '../contexts/AuthContext'
import { useBreadcrumb } from '../contexts/BreadcrumbContext'
import { toast } from 'sonner'
import { format, isSameDay, addMonths, subMonths, startOfMonth, endOfMonth } from 'date-fns'
import { ar } from 'date-fns/locale'

interface Hearing {
    id: string
    hearing_date: string
    hearing_time: string
    court_room: string
    notes: string
    judge_name: string
    cases?: {
        id: string
        case_number: string
        court_name: string
        clients?: {
            full_name: string
        }
    }
    // ✅ New denormalized fields
    client_name?: string
    case_number?: string
    case_year?: string
    court_name?: string
}

export default function HearingsPage() {
    const { getEffectiveLawyerId } = useAuth()
    const { setPageTitle } = useBreadcrumb()
    const [hearings, setHearings] = useState<Hearing[]>([])
    const [loading, setLoading] = useState(true)
    const [currentDate, setCurrentDate] = useState(new Date())
    const [viewMode, setViewMode] = useState<'list' | 'timeline'>('timeline')

    useEffect(() => {
        setPageTitle('الجلسات')
        const lawyerId = getEffectiveLawyerId()
        if (lawyerId) {
            fetchHearings()
        }
    }, [currentDate, getEffectiveLawyerId, setPageTitle])

    const fetchHearings = async () => {
        const lawyerId = getEffectiveLawyerId()
        if (!lawyerId) return

        try {
            setLoading(true)
            const start = format(startOfMonth(currentDate), 'yyyy-MM-dd')
            const end = format(endOfMonth(currentDate), 'yyyy-MM-dd')

            // Fetch hearings with case & client details - FILTERED BY LAWYER_ID
            // Fetch hearings from Backend API
            const response = await apiClient.get(`/api/hearings/range?start_date=${start}&end_date=${end}`)

            if (response.success && response.hearings) {
                setHearings(response.hearings)
            } else {
                setHearings([])
            }

            // setHearings(data || []) <-- Removed
        } catch (error) {
            console.error('Error fetching hearings:', error)
            toast.error('فشل تحميل الجلسات')
        } finally {
            setLoading(false)
        }
    }

    const nextMonth = () => setCurrentDate(addMonths(currentDate, 1))
    const prevMonth = () => setCurrentDate(subMonths(currentDate, 1))

    // Group hearings by date
    const groupedHearings = hearings.reduce((groups, hearing) => {
        const date = hearing.hearing_date.split('T')[0]
        if (!groups[date]) groups[date] = []
        groups[date].push(hearing)
        return groups
    }, {} as Record<string, Hearing[]>)

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-center gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-gold-500" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        جدول الجلسات
                    </h1>
                    <p className="text-gray-400 text-sm mt-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        إدارة ومتابعة جميع الجلسات والمواعيد القضائية
                    </p>
                </div>

                <div className="flex items-center gap-4 bg-obsidian-800/50 p-2 rounded-xl border border-gold-500/20">
                    <button
                        onClick={prevMonth}
                        className="p-2 hover:bg-gold-500/10 rounded-lg text-gold-500 transition-colors"
                    >
                        <ChevronRight className="w-5 h-5" />
                    </button>
                    <span className="text-white font-bold min-w-[150px] text-center" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        {format(currentDate, 'MMMM yyyy', { locale: ar })}
                    </span>
                    <button
                        onClick={nextMonth}
                        className="p-2 hover:bg-gold-500/10 rounded-lg text-gold-500 transition-colors"
                    >
                        <ChevronLeft className="w-5 h-5" />
                    </button>
                </div>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="backdrop-blur-xl bg-obsidian-800/70 border border-gold-500/20 rounded-xl p-6 relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-24 h-24 bg-gold-500/5 rounded-br-full" />
                    <h3 className="text-gray-400 text-sm mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>إجمالي جلسات الشهر</h3>
                    <p className="text-4xl font-bold text-white">{hearings.length}</p>
                </div>
                <div className="backdrop-blur-xl bg-obsidian-800/70 border border-blue-500/20 rounded-xl p-6 relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-24 h-24 bg-blue-500/5 rounded-br-full" />
                    <h3 className="text-gray-400 text-sm mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>جلسات قادمة</h3>
                    <p className="text-4xl font-bold text-blue-400">
                        {hearings.filter(h => new Date(h.hearing_date) > new Date()).length}
                    </p>
                </div>
                <div className="backdrop-blur-xl bg-obsidian-800/70 border border-green-500/20 rounded-xl p-6 relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-24 h-24 bg-green-500/5 rounded-br-full" />
                    <h3 className="text-gray-400 text-sm mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>تمت هذا الشهر</h3>
                    <p className="text-4xl font-bold text-green-400">
                        {hearings.filter(h => new Date(h.hearing_date) <= new Date()).length}
                    </p>
                </div>
            </div>

            {/* Timeline View */}
            <div className="relative space-y-8 pl-4 md:pl-0">
                {/* Vertical Line */}
                <div className="hidden md:block absolute right-1/2 top-4 bottom-0 w-0.5 bg-gradient-to-b from-gold-500/50 via-gold-500/10 to-transparent transform translate-x-1/2" />

                {loading ? (
                    <div className="text-center py-20">
                        <div className="w-10 h-10 border-4 border-gold-500 border-t-transparent rounded-full animate-spin mx-auto" />
                    </div>
                ) : hearings.length === 0 ? (
                    <div className="text-center py-20 backdrop-blur-xl bg-obsidian-800/30 border border-gold-500/10 rounded-2xl border-dashed">
                        <Calendar className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                        <p className="text-gray-500 text-lg">لا توجد جلسات في هذا الشهر</p>
                    </div>
                ) : (
                    Object.entries(groupedHearings).map(([date, dayHearings], groupIndex) => (
                        <div key={date} className="relative">
                            {/* Date Badge */}
                            <div className="flex justify-center mb-6">
                                <div className="backdrop-blur-sm bg-obsidian-900/90 border border-gold-500/30 px-6 py-2 rounded-full text-gold-500 font-bold shadow-lg shadow-gold-500/10 z-10 flex items-center gap-2">
                                    <Calendar className="w-4 h-4" />
                                    {format(new Date(date), 'EEEE, d MMMM', { locale: ar })}
                                </div>
                            </div>

                            <div className="space-y-6">
                                {dayHearings.map((hearing, index) => {
                                    const isAlignLeft = index % 2 === 0
                                    return (
                                        <motion.div
                                            key={hearing.id}
                                            initial={{ opacity: 1, y: 0 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            transition={{ delay: index * 0.1 }}
                                            className={`flex flex-col md:flex-row items-center gap-6 ${isAlignLeft ? 'md:flex-row-reverse' : ''}`}
                                        >
                                            {/* Card */}
                                            <div className="w-full md:w-1/2">
                                                <div className="group backdrop-blur-xl bg-obsidian-800/70 border border-gold-500/20 rounded-xl p-6 hover:border-gold-500/50 transition-all hover:translate-y-[-2px] hover:shadow-lg hover:shadow-gold-500/5 relative">
                                                    {/* Connector Dot (Mobile Hidden) */}
                                                    <div className={`hidden md:block absolute top-1/2 ${isAlignLeft ? '-left-[3.25rem]' : '-right-[3.25rem]'} w-4 h-4 rounded-full bg-obsidian-900 border-2 border-gold-500 z-10 transform -translate-y-1/2`} />

                                                    {/* Connector Line (Mobile Hidden) */}
                                                    <div className={`hidden md:block absolute top-1/2 ${isAlignLeft ? '-left-12' : '-right-12'} w-12 h-0.5 bg-gold-500/30 transform -translate-y-1/2`} />

                                                    {/* Content */}
                                                    <div className="flex justify-between items-start mb-4 border-b border-gold-500/10 pb-4">
                                                        <div>
                                                            <div className="flex items-center gap-2 text-gold-500 mb-1">
                                                                <Clock className="w-4 h-4" />
                                                                <span className="font-bold font-mono">{hearing.hearing_time}</span>
                                                            </div>
                                                            <h3 className="text-xl font-bold text-white mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                                                جلسة {hearing.case_number || hearing.cases?.case_number || 'غير معروف'}
                                                            </h3>
                                                        </div>
                                                        <div className="p-2 bg-obsidian-900 rounded-lg text-gold-500">
                                                            <Gavel className="w-6 h-6" />
                                                        </div>
                                                    </div>

                                                    <div className="grid grid-cols-2 gap-4 text-sm">
                                                        <div>
                                                            <p className="text-gray-500 text-xs mb-1">المحكمة</p>
                                                            <p className="text-gray-300 flex items-center gap-1">
                                                                <MapPin className="w-3 h-3 text-gold-500/70" />
                                                                {hearing.court_name || hearing.cases?.court_name || '-'}
                                                            </p>
                                                        </div>
                                                        <div>
                                                            <p className="text-gray-500 text-xs mb-1">القاعة</p>
                                                            <p className="text-gray-300">{hearing.court_room || '-'}</p>
                                                        </div>
                                                        <div className="col-span-2">
                                                            <p className="text-gray-500 text-xs mb-1">الموكل</p>
                                                            <p className="text-gray-300 flex items-center gap-1">
                                                                <User className="w-3 h-3 text-gold-500/70" />
                                                                {hearing.client_name || hearing.cases?.clients?.full_name || '-'}
                                                            </p>
                                                        </div>
                                                    </div>

                                                    {hearing.notes && (
                                                        <div className="mt-4 pt-4 border-t border-gold-500/10">
                                                            <p className="text-sm text-gray-400 bg-obsidian-900/50 p-3 rounded-lg border border-gold-500/5">
                                                                {hearing.notes}
                                                            </p>
                                                        </div>
                                                    )}
                                                </div>
                                            </div>

                                            {/* Spacer for Timeline Alignment */}
                                            <div className="w-full md:w-1/2" />
                                        </motion.div>
                                    )
                                })}
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    )
}
