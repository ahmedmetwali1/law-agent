import { format } from 'date-fns'
import { arSA } from 'date-fns/locale'
import { Calendar as CalendarIcon, Clock, Briefcase, CheckSquare, AlertCircle, User } from 'lucide-react'
import { AnimatePresence } from 'framer-motion'
import { useNavigate } from 'react-router-dom'

interface DailyEvent {
    id: string
    type: 'hearing' | 'task'
    title: string
    time?: string
    caseNumber?: string // Deprecated
    caseId?: string
    caseTitle?: string
    clientName?: string
    priority?: string
    status?: string
}

interface DailyWorkCardProps {
    date: Date
    events: DailyEvent[]
    isLoading: boolean
}

export function DailyWorkCard({ date, events, isLoading }: DailyWorkCardProps) {
    const isToday = new Date().toDateString() === date.toDateString()
    const navigate = useNavigate()

    const handleEventClick = (event: DailyEvent) => {
        if (event.caseId) {
            // If linked to a case (hearing or task), go to case details
            // But user specifically said "if task go to tasks page". 
            // "if clicked go to case, and if it is a task go to tasks page"
            if (event.type === 'task') {
                navigate('/tasks')
            } else {
                navigate(`/cases/${event.caseId}`)
            }
        } else {
            // No case link, just go to general pages
            if (event.type === 'task') {
                navigate('/tasks')
            } else {
                // If hearing has no case (shouldn't happen often), go to cases list
                navigate('/cases')
            }
        }
    }

    return (
        <div className="backdrop-blur-xl bg-obsidian-800/70 border border-gold-500/20 rounded-xl p-5 h-full flex flex-col">
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h3 className="text-xl font-bold text-white flex items-center gap-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        <CalendarIcon className="w-5 h-5 text-gold-500" />
                        {isToday ? 'أعمال اليوم' : 'أعمال محددة'}
                    </h3>
                    <p className="text-sm text-gray-400 mt-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        {format(date, 'EEEE، d MMMM yyyy', { locale: arSA })}
                    </p>
                </div>
                <div className="px-3 py-1 bg-gold-500/10 border border-gold-500/20 rounded-full">
                    <span className="text-sm font-bold text-gold-500">
                        {events.length} مهام
                    </span>
                </div>
            </div>

            <div className="flex-1 overflow-y-auto space-y-3 scrollbar-thin scrollbar-thumb-obsidian-700 scrollbar-track-transparent pr-2">
                <AnimatePresence mode="wait">
                    {isLoading ? (
                        <div className="flex flex-col items-center justify-center h-40 space-y-3">
                            <div className="w-8 h-8 border-2 border-gold-500 border-t-transparent rounded-full animate-spin" />
                            <p className="text-gray-500 text-sm">جاري التحميل...</p>
                        </div>
                    ) : events.length > 0 ? (
                        events.map((event, index) => (
                            <div
                                key={event.id}
                                onClick={() => handleEventClick(event)}
                                className={`p-4 rounded-xl border transition-all cursor-pointer hover:scale-[1.02] ${event.type === 'hearing'
                                        ? 'bg-blue-900/10 border-blue-500/20 hover:border-blue-500/40 hover:bg-blue-900/20'
                                        : 'bg-green-900/10 border-green-500/20 hover:border-green-500/40 hover:bg-green-900/20'
                                    }`}
                            >
                                <div className="flex items-start justify-between">
                                    <div className="flex items-start gap-3 w-full">
                                        <div className={`p-2 rounded-lg shrink-0 ${event.type === 'hearing' ? 'bg-blue-500/10 text-blue-400' : 'bg-green-500/10 text-green-400'
                                            }`}>
                                            {event.type === 'hearing' ? <Briefcase className="w-4 h-4" /> : <CheckSquare className="w-4 h-4" />}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <h4 className="font-bold text-gray-200 text-sm mb-1 truncate">{event.title}</h4>

                                            {/* Case Title & Link */}
                                            {event.caseTitle && (
                                                <div className="flex items-center gap-1.5 text-xs text-gray-400 mb-1">
                                                    <Briefcase className="w-3 h-3 text-gray-500" />
                                                    <span className="truncate">{event.caseTitle}</span>
                                                </div>
                                            )}

                                            {/* Client Name */}
                                            {event.clientName && (
                                                <div className="flex items-center gap-1.5 text-xs text-gray-400 mb-2">
                                                    <User className="w-3 h-3 text-gray-500" />
                                                    <span className="truncate">{event.clientName}</span>
                                                </div>
                                            )}

                                            {/* Time for Hearings */}
                                            {event.time && (
                                                <div className="flex items-center gap-1.5 text-xs text-gray-400 bg-black/20 w-fit px-2 py-1 rounded">
                                                    <Clock className="w-3 h-3" />
                                                    {event.time}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                    {event.priority === 'urgent' && (
                                        <div className="text-red-400 shrink-0" title="عاجل">
                                            <AlertCircle className="w-4 h-4" />
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))
                    ) : (
                        <div className="flex flex-col items-center justify-center h-40 text-gray-500 border-2 border-dashed border-gray-800 rounded-xl">
                            <Clock className="w-8 h-8 mb-2 opacity-50" />
                            <p className="text-sm">لا توجد أعمال مجدولة لهذا اليوم</p>
                        </div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    )
}
