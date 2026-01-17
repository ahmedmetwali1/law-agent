import { useState } from 'react'
import { motion } from 'framer-motion'
import { ChevronLeft, ChevronRight, Calendar as CalendarIcon } from 'lucide-react'
import { format } from 'date-fns'
import { arSA } from 'date-fns/locale'

export interface CalendarEvent {
    id: string
    type: 'hearing' | 'task'
    date: Date
    title: string
    time?: string
    caseNumber?: string // Deprecated
    caseId?: string
    caseTitle?: string
    clientName?: string
    priority?: string
}

interface CalendarWidgetProps {
    events: CalendarEvent[]
    selectedDate: Date
    onSelectDate: (date: Date) => void
}

export function CalendarWidget({ events, selectedDate, onSelectDate }: CalendarWidgetProps) {
    const [currentDate, setCurrentDate] = useState(new Date())

    const getDaysInMonth = () => {
        const year = currentDate.getFullYear()
        const month = currentDate.getMonth()
        const firstDay = new Date(year, month, 1)
        const lastDay = new Date(year, month + 1, 0)
        const daysInMonth = lastDay.getDate()
        const startingDayOfWeek = firstDay.getDay()

        const days = []

        // Add empty cells for days before month starts relative to Sunday
        for (let i = 0; i < startingDayOfWeek; i++) {
            days.push(null)
        }

        for (let day = 1; day <= daysInMonth; day++) {
            days.push(new Date(year, month, day))
        }

        return days
    }

    const days = getDaysInMonth()
    const weekDays = ['أحد', 'إثنين', 'ثلاثاء', 'أربعاء', 'خميس', 'جمعة', 'سبت']

    const handlePrevMonth = () => {
        setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1))
    }

    const handleNextMonth = () => {
        setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1))
    }

    const getEventsForDay = (date: Date) => {
        return events.filter(e =>
            e.date.getDate() === date.getDate() &&
            e.date.getMonth() === date.getMonth() &&
            e.date.getFullYear() === date.getFullYear()
        )
    }

    return (
        <div className="backdrop-blur-xl bg-obsidian-800/70 border border-gold-500/20 rounded-xl p-6 h-full">
            <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-bold text-white flex items-center gap-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                    <CalendarIcon className="w-5 h-5 text-gold-500" />
                    التقويم
                </h3>
                <div className="flex items-center gap-4 bg-obsidian-900/50 rounded-lg p-1">
                    <button onClick={handlePrevMonth} className="p-1 hover:text-gold-500 transition-colors">
                        <ChevronRight className="w-5 h-5" />
                    </button>
                    <span className="text-sm font-bold min-w-[100px] text-center" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        {format(currentDate, 'MMMM yyyy', { locale: arSA })}
                    </span>
                    <button onClick={handleNextMonth} className="p-1 hover:text-gold-500 transition-colors">
                        <ChevronLeft className="w-5 h-5" />
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-7 gap-2 mb-2">
                {weekDays.map(day => (
                    <div key={day} className="text-center text-xs text-gray-400 py-2 font-bold" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        {day}
                    </div>
                ))}
            </div>

            <div className="grid grid-cols-7 gap-2">
                {days.map((date, i) => {
                    if (!date) return <div key={`empty-${i}`} className="aspect-square" />

                    const dayEvents = getEventsForDay(date)
                    const isSelected = selectedDate.toDateString() === date.toDateString()
                    const isToday = new Date().toDateString() === date.toDateString()
                    const hasHearing = dayEvents.some(e => e.type === 'hearing')
                    const hasTask = dayEvents.some(e => e.type === 'task')

                    return (
                        <div key={i} className="relative aspect-square">
                            <button
                                onClick={() => onSelectDate(date)}
                                className={`w-full h-full rounded-xl flex flex-col items-center justify-center relative transition-all border ${isSelected
                                    ? 'bg-gold-500 text-black border-gold-500 shadow-lg shadow-gold-500/20'
                                    : isToday
                                        ? 'bg-obsidian-700/50 text-gold-500 border-gold-500/30'
                                        : 'bg-obsidian-900/30 text-gray-300 border-transparent hover:bg-obsidian-800 hover:border-gray-700'
                                    }`}
                            >
                                <span className="text-sm font-bold">{date.getDate()}</span>

                                {/* Indicators */}
                                <div className="flex gap-1 mt-1">
                                    {hasHearing && (
                                        <div className={`w-1.5 h-1.5 rounded-full ${isSelected ? 'bg-black' : 'bg-blue-500'}`} />
                                    )}
                                    {hasTask && (
                                        <div className={`w-1.5 h-1.5 rounded-full ${isSelected ? 'bg-black/50' : 'bg-green-500'}`} />
                                    )}
                                </div>
                            </button>
                        </div>
                    )
                })}
            </div>
        </div>
    )
}
