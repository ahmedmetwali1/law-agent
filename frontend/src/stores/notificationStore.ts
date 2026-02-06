import { create } from 'zustand'
import { toast } from 'sonner'
import { apiClient } from '../api/client'

interface Notification {
    id: string
    type: 'hearing' | 'task' | 'case'
    title: string
    message: string
    timestamp: Date
    read: boolean
    link?: string
}

interface NotificationState {
    notifications: Notification[]
    unreadCount: number
    isLoading: boolean

    fetchNotifications: (lawyerId: string) => Promise<void>
    markAsRead: (id: string) => void
    clearAll: () => void
}

export const useNotificationStore = create<NotificationState>((set, get) => ({
    notifications: [],
    unreadCount: 0,
    isLoading: false,

    fetchNotifications: async (lawyerId: string) => {
        set({ isLoading: true })
        try {
            // ✅ BFF Pattern: استخدام apiClient بدلاً من Supabase مباشرة
            const response = await apiClient.get<{
                notifications: Array<{
                    id: string
                    type: string
                    title: string
                    message: string
                    timestamp: string
                    read: boolean
                    link?: string
                }>
                unreadCount: number
            }>('/api/notifications')

            // Convert timestamp strings to Date objects
            const notifications: Notification[] = response.notifications.map(n => ({
                ...n,
                type: n.type as 'hearing' | 'task' | 'case',
                timestamp: new Date(n.timestamp)
            }))

            set({
                notifications,
                unreadCount: response.unreadCount,
                isLoading: false
            })
        } catch (error) {
            console.error('Failed to fetch notifications:', error)
            toast.error('فشل تحميل الإشعارات')
            set({ isLoading: false })
        }
    },

    markAsRead: (id: string) => {
        set(state => ({
            notifications: state.notifications.map(n =>
                n.id === id ? { ...n, read: true } : n
            ),
            unreadCount: Math.max(0, state.unreadCount - 1)
        }))
    },

    clearAll: () => {
        set({
            notifications: [],
            unreadCount: 0
        })
    }
}))
