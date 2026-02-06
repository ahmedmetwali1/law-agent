import { create } from 'zustand'
import { apiClient } from '../api/client'

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

        try {
            // ✅ BFF Pattern: استخدام apiClient بدلاً من Supabase
            const stats = await apiClient.get<{
                activeCases: number
                weeklyHearings: number
                pendingTasks: number
            }>('/api/dashboard/stats')

            set({
                activeCases: stats.activeCases,
                weeklyHearings: stats.weeklyHearings,
                pendingTasks: stats.pendingTasks,
                isLoading: false,
            })
        } catch (error: any) {
            console.error('Failed to fetch dashboard stats:', error)
            set({
                error: error.message || 'Failed to fetch statistics',
                isLoading: false,
            })
        }
    },
}))
