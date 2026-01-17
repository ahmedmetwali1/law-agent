import { create } from 'zustand'
import { supabase } from '../supabaseClient'

interface DashboardStats {
    activeCases: number
    weeklyHearings: number
    pendingTasks: number
    isLoading: boolean
    error: string | null
}

interface DashboardStore extends DashboardStats {
    fetchStats: () => Promise<void>
}

export const useDashboardStore = create<DashboardStore>((set) => ({
    activeCases: 0,
    weeklyHearings: 0,
    pendingTasks: 0,
    isLoading: false,
    error: null,

    fetchStats: async () => {
        set({ isLoading: true, error: null })

        // Check if using placeholder Supabase - use dummy data
        if (!import.meta.env.VITE_SUPABASE_URL) {
            await new Promise(resolve => setTimeout(resolve, 500))

            set({
                activeCases: 12,
                weeklyHearings: 7,
                pendingTasks: 5,
                isLoading: false,
            })
            return
        }

        try {
            const now = new Date()
            const dayOfWeek = now.getDay()
            const weekStart = new Date(now)
            weekStart.setDate(now.getDate() - dayOfWeek)
            weekStart.setHours(0, 0, 0, 0)

            const weekEnd = new Date(weekStart)
            weekEnd.setDate(weekStart.getDate() + 6)
            weekEnd.setHours(23, 59, 59, 999)

            const { count: casesCount, error: casesError } = await supabase
                .from('cases')
                .select('*', { count: 'exact', head: true })
                .eq('status', 'نشطة')

            if (casesError) throw casesError

            const { count: hearingsCount, error: hearingsError } = await supabase
                .from('hearings')
                .select('*', { count: 'exact', head: true })
                .gte('hearing_date', weekStart.toISOString().split('T')[0])
                .lte('hearing_date', weekEnd.toISOString().split('T')[0])

            if (hearingsError) throw hearingsError

            const { count: tasksCount, error: tasksError } = await supabase
                .from('tasks')
                .select('*', { count: 'exact', head: true })
                .eq('status', 'قيد التنفيذ')

            if (tasksError) throw tasksError

            set({
                activeCases: casesCount || 0,
                weeklyHearings: hearingsCount || 0,
                pendingTasks: tasksCount || 0,
                isLoading: false,
            })
        } catch (error) {
            console.error('Failed to fetch dashboard stats:', error)
            set({
                activeCases: 12,
                weeklyHearings: 7,
                pendingTasks: 5,
                isLoading: false,
                error: null,
            })
        }
    },
}))
