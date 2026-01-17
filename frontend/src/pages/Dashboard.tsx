import { useEffect, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
// import { supabase } from '../supabaseClient' // ✅ Replaced with API client
import { apiClient } from '../api/client'
import { HighDensityStatCard } from '../components/dashboard/HighDensityStatCard'
import { CalendarWidget, CalendarEvent } from '../components/dashboard/CalendarWidget'
import { DailyWorkCard } from '../components/dashboard/DailyWorkCard'
import { Briefcase, Calendar, CheckSquare, Users, TrendingUp } from 'lucide-react'

export function Dashboard() {
    const { profile, getEffectiveLawyerId } = useAuth()
    const [selectedDate, setSelectedDate] = useState(new Date())
    const [events, setEvents] = useState<CalendarEvent[]>([])
    const [stats, setStats] = useState({
        activeCases: 0,
        casesGrowth: 0,
        newCasesWeek: 0,
        urgentCases: 0,
        weeklyHearings: 0,
        hearingsGrowth: 0,
        hearingsThisWeek: 0,
        upcomingHearings: 0,
        pendingTasks: 0,
        tasksGrowth: 0,
        tasksInProgress: 0,
        tasksOverdue: 0,
        totalClients: 0,
        clientsGrowth: 0,
        activeClients: 0,
        newClientsMonth: 0,
        isLoading: true
    })

    useEffect(() => {
        const lawyerId = getEffectiveLawyerId()
        if (lawyerId) {
            fetchDashboardData()
        }
    }, [getEffectiveLawyerId])

    const fetchDashboardData = async () => {
        const lawyerId = getEffectiveLawyerId()
        if (!lawyerId) return

        try {
            const today = new Date()
            const startOfWeek = new Date(today.getFullYear(), today.getMonth(), today.getDate() - today.getDay())
            const startOfMonth = new Date(today.getFullYear(), today.getMonth(), 1)

            // 1. Fetch stats from Backend API
            const statsData = await apiClient.get('/api/dashboard/stats')

            setStats({
                activeCases: statsData.cases.active,
                casesGrowth: 12, // TODO: Calculate in backend
                newCasesWeek: statsData.cases.active, // Approximation
                urgentCases: statsData.cases.pending,

                weeklyHearings: statsData.hearings.total,
                hearingsGrowth: 5, // TODO: Calculate in backend
                hearingsThisWeek: statsData.hearings.total,
                upcomingHearings: statsData.hearings.upcoming,

                pendingTasks: statsData.tasks.total,
                tasksGrowth: -8, // TODO: Calculate in backend
                tasksInProgress: statsData.tasks.in_progress,
                tasksOverdue: statsData.tasks.overdue,

                totalClients: statsData.clients.total,
                clientsGrowth: 3, // TODO: Calculate in backend
                activeClients: Math.floor(statsData.clients.total * 0.8), // Estimate
                newClientsMonth: statsData.clients.new_this_month,

                isLoading: false
            })

            // 2. Fetch calendar events
            const rangeStart = new Date(today.getFullYear(), today.getMonth() - 1, 1)
            const rangeEnd = new Date(today.getFullYear(), today.getMonth() + 2, 0)

            const eventsData = await apiClient.get(
                `/api/dashboard/calendar-events?start_date=${rangeStart.toISOString()}&end_date=${rangeEnd.toISOString()}`
            )

            // Convert ISO date strings to Date objects (CRITICAL for calendar widget)
            const allEvents: CalendarEvent[] = eventsData.events.map((e: any) => ({
                id: e.id,
                type: e.type as 'hearing' | 'task',
                date: new Date(e.date), // Convert from ISO string to Date object
                title: e.title,
                time: e.time,
                priority: e.priority,
                caseId: e.case_id,
                caseTitle: e.case_title,
                clientName: e.client_name
            }))

            setEvents(allEvents)

        } catch (error) {
            console.error('Error fetching dashboard data:', error)
            setStats(prev => ({ ...prev, isLoading: false }))
        }
    }

    const getGreeting = () => {
        const hour = new Date().getHours()
        if (hour < 12) return 'صباح الخير'
        if (hour < 18) return 'مساء الخير'
        return 'مساء الخير'
    }

    // Filter events for selected date
    const selectedDayEvents = events.filter(e =>
        e.date.getDate() === selectedDate.getDate() &&
        e.date.getMonth() === selectedDate.getMonth() &&
        e.date.getFullYear() === selectedDate.getFullYear()
    )

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-gold-500 mb-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        {getGreeting()}, {profile?.full_name || 'المحامي'}
                    </h1>
                    {profile?.country && (
                        <p className="text-sm text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            {profile.country.flag_emoji} {profile.country.name_ar}
                            {profile.specialization && ` • ${profile.specialization}`}
                        </p>
                    )}
                </div>
                <div className="flex items-center gap-2 text-gray-400 text-sm">
                    <TrendingUp className="w-4 h-4" />
                    <span style={{ fontFamily: 'Cairo, sans-serif' }}>تحديث مباشر</span>
                </div>
            </div>

            {/* High-Density Stat Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <HighDensityStatCard
                    title="القضايا النشطة"
                    mainValue={stats.isLoading ? '...' : stats.activeCases}
                    icon={Briefcase}
                    iconColor="text-cobalt-500"
                    trend={{
                        value: `${stats.casesGrowth > 0 ? '+' : ''}${stats.casesGrowth}%`,
                        isPositive: stats.casesGrowth >= 0,
                        label: 'هذا الشهر'
                    }}
                    microStats={[
                        { label: 'جديدة هذا الأسبوع', value: stats.newCasesWeek, color: 'text-green-400' },
                        { label: 'عاجلة', value: stats.urgentCases, color: 'text-red-400' }
                    ]}
                    delay={0}
                />

                <HighDensityStatCard
                    title="الجلسات"
                    mainValue={stats.isLoading ? '...' : stats.weeklyHearings}
                    icon={Calendar}
                    iconColor="text-gold-500"
                    trend={{
                        value: `${stats.hearingsGrowth > 0 ? '+' : ''}${stats.hearingsGrowth}`,
                        isPositive: stats.hearingsGrowth >= 0,
                        label: 'منذ الأسبوع الماضي'
                    }}
                    microStats={[
                        { label: 'هذا الأسبوع', value: stats.hearingsThisWeek, color: 'text-orange-400' },
                        { label: 'قادمة (7 أيام)', value: stats.upcomingHearings, color: 'text-blue-400' }
                    ]}
                    delay={0.1}
                />

                <HighDensityStatCard
                    title="المهام"
                    mainValue={stats.isLoading ? '...' : stats.pendingTasks}
                    icon={CheckSquare}
                    iconColor="text-green-500"
                    trend={{
                        value: `${stats.tasksGrowth > 0 ? '+' : ''}${stats.tasksGrowth}`,
                        isPositive: stats.tasksGrowth >= 0,
                        label: 'منذ أمس'
                    }}
                    microStats={[
                        { label: 'قيد التنفيذ', value: stats.tasksInProgress, color: 'text-yellow-400' },
                        { label: 'متأخرة', value: stats.tasksOverdue, color: 'text-red-400' }
                    ]}
                    delay={0.2}
                />

                <HighDensityStatCard
                    title="الموكلون"
                    mainValue={stats.isLoading ? '...' : stats.totalClients}
                    icon={Users}
                    iconColor="text-purple-500"
                    trend={{
                        value: `${stats.clientsGrowth > 0 ? '+' : ''}${stats.clientsGrowth}`,
                        isPositive: stats.clientsGrowth >= 0,
                        label: 'هذا الشهر'
                    }}
                    microStats={[
                        { label: 'نشطون', value: stats.activeClients, color: 'text-green-400' },
                        { label: 'جدد هذا الشهر', value: stats.newClientsMonth, color: 'text-blue-400' }
                    ]}
                    delay={0.3}
                />
            </div>

            {/* Calendar & Daily Work Section */}
            {profile?.id && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[500px]">
                    <div className="lg:col-span-2 h-full">
                        <CalendarWidget
                            events={events} // Pass all events
                            selectedDate={selectedDate}
                            onSelectDate={setSelectedDate}
                        />
                    </div>
                    <div className="h-full">
                        <DailyWorkCard
                            date={selectedDate}
                            events={selectedDayEvents}
                            isLoading={stats.isLoading}
                        />
                    </div>
                </div>
            )}
        </div>
    )
}
