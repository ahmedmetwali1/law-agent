import { useEffect, useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { supabase } from '../supabaseClient'
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
            const endOfWeek = new Date(today.getFullYear(), today.getMonth(), today.getDate() - today.getDay() + 6)
            const startOfMonth = new Date(today.getFullYear(), today.getMonth(), 1)
            const endOfMonth = new Date(today.getFullYear(), today.getMonth() + 1, 0)

            // 1. Fetch Stats
            const [
                activeCases,
                allCases,
                urgentCases,
                hearingsWeek,
                hearingsNextWeek,
                pendingTasks,
                tasksInProgress,
                overdueTasks,
                totalClients,
                newClients
            ] = await Promise.all([
                // Active Cases
                supabase.from('cases').select('id', { count: 'exact', head: true }).eq('lawyer_id', lawyerId).eq('status', 'active'),
                // All Cases (for growth calc - simplified)
                supabase.from('cases').select('created_at').eq('lawyer_id', lawyerId),
                // Urgent Cases (using pending status as proxy for urgent)
                supabase.from('cases').select('id', { count: 'exact', head: true }).eq('lawyer_id', lawyerId).eq('status', 'pending'),

                // Hearings This Week
                supabase.from('hearings').select('id', { count: 'exact', head: true }).eq('lawyer_id', lawyerId)
                    .gte('hearing_date', startOfWeek.toISOString()).lte('hearing_date', endOfWeek.toISOString()),
                // Hearings Next 7 Days (Upcoming)
                supabase.from('hearings').select('id', { count: 'exact', head: true }).eq('lawyer_id', lawyerId)
                    .gte('hearing_date', new Date().toISOString()).lte('hearing_date', new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString()),

                // Pending Tasks (both pending and in_progress)
                supabase.from('tasks').select('id', { count: 'exact', head: true }).eq('lawyer_id', lawyerId).in('status', ['pending', 'in_progress']),
                // Tasks In Progress (for micro-stat)
                supabase.from('tasks').select('id', { count: 'exact', head: true }).eq('lawyer_id', lawyerId).eq('status', 'in_progress'),
                // Overdue Tasks
                supabase.from('tasks').select('id', { count: 'exact', head: true }).eq('lawyer_id', lawyerId).lt('execution_date', new Date().toISOString()).neq('status', 'completed'),

                // Total Clients
                supabase.from('clients').select('id', { count: 'exact', head: true }).eq('lawyer_id', lawyerId),
                // New Clients This Month
                supabase.from('clients').select('id', { count: 'exact', head: true }).eq('lawyer_id', lawyerId).gte('created_at', startOfMonth.toISOString())
            ])

            // Calculate mock growth for now (requires deeper history queries)
            // Real implementation would compare with previous month counts

            setStats({
                activeCases: activeCases.count || 0,
                casesGrowth: 12, // Mock
                newCasesWeek: allCases.data?.filter(c => new Date(c.created_at) >= startOfWeek).length || 0,
                urgentCases: urgentCases.count || 0,

                weeklyHearings: hearingsWeek.count || 0,
                hearingsGrowth: 5, // Mock
                hearingsThisWeek: hearingsWeek.count || 0,
                upcomingHearings: hearingsNextWeek.count || 0,

                pendingTasks: pendingTasks.count || 0,
                tasksGrowth: -8, // Mock
                tasksInProgress: tasksInProgress.count || 0,
                tasksOverdue: overdueTasks.count || 0,

                totalClients: totalClients.count || 0,
                clientsGrowth: 3, // Mock
                activeClients: Math.floor((totalClients.count || 0) * 0.8), // Estimate
                newClientsMonth: newClients.count || 0,

                isLoading: false
            })

            // 2. Fetch Events for Calendar (2 months range: prev and next)
            const rangeStart = new Date(today.getFullYear(), today.getMonth() - 1, 1)
            const rangeEnd = new Date(today.getFullYear(), today.getMonth() + 2, 0)

            // A. Fetch Cases Lookup (to avoid complex joins that might fail)
            const { data: casesData, error: casesError } = await supabase
                .from('cases')
                .select('id, subject, case_number, court_name, clients(full_name)')
                .eq('lawyer_id', lawyerId)

            if (casesError) {
                console.error('Cases Error:', casesError)
            }

            // Create a lookup map
            const casesMap = new Map()
            if (casesData) {
                casesData.forEach((c: any) => {
                    const clientName = Array.isArray(c.clients) ? c.clients[0]?.full_name : c.clients?.full_name
                    casesMap.set(c.id, {
                        subject: c.subject,
                        case_number: c.case_number,
                        court_name: c.court_name,
                        clientName: clientName
                    })
                })
            }

            // B. Fetch Hearings
            const { data: hearingsData, error: hearingsError } = await supabase
                .from('hearings')
                .select('id, hearing_date, hearing_time, case_id')
                .eq('lawyer_id', lawyerId)
                .gte('hearing_date', rangeStart.toISOString())
                .lte('hearing_date', rangeEnd.toISOString())

            if (hearingsError) console.error('Hearings Error:', hearingsError)

            // C. Fetch Tasks
            const { data: tasksData, error: tasksError } = await supabase
                .from('tasks')
                .select('id, title, execution_date, priority, case_id')
                .eq('lawyer_id', lawyerId)
                .gte('execution_date', rangeStart.toISOString())
                .lte('execution_date', rangeEnd.toISOString())

            if (tasksError) console.error('Tasks Error:', tasksError)

            // D. Combine
            const allEvents: CalendarEvent[] = [
                ...(hearingsData || []).map(h => {
                    const caseInfo = h.case_id ? casesMap.get(h.case_id) : null

                    // Format Title: "Session at [Time] for client [Name] - Case [Number] - Court [Name]"
                    let formattedTitle = 'جلسة'
                    if (h.hearing_time) formattedTitle += ` الساعة ${h.hearing_time}`
                    if (caseInfo?.clientName) formattedTitle += ` للعميل ${caseInfo.clientName}`
                    if (caseInfo?.case_number) formattedTitle += ` - قضية رقم ${caseInfo.case_number}`
                    if (caseInfo?.court_name) formattedTitle += ` - ${caseInfo.court_name}`

                    if (!caseInfo) formattedTitle = 'جلسة (بدون تفاصيل)';

                    return {
                        id: h.id,
                        type: 'hearing' as const,
                        date: new Date(h.hearing_date),
                        title: formattedTitle,
                        time: h.hearing_time,
                        caseId: h.case_id,
                        caseTitle: caseInfo?.subject,
                        clientName: caseInfo?.clientName
                    }
                }),
                ...(tasksData || []).map(t => {
                    const caseInfo = t.case_id ? casesMap.get(t.case_id) : null
                    return {
                        id: t.id,
                        type: 'task' as const,
                        date: new Date(t.execution_date),
                        title: t.title,
                        priority: t.priority,
                        caseId: t.case_id,
                        caseTitle: caseInfo?.subject,
                        clientName: caseInfo?.clientName
                    }
                })
            ]
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
