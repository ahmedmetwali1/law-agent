import { create } from 'zustand'
import { toast } from 'sonner'
import { supabase } from '../supabaseClient'

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
            const notifications: Notification[] = []

            // 1. Fetch upcoming hearings (next 7 days)
            const today = new Date()
            const sevenDaysLater = new Date(today)
            sevenDaysLater.setDate(today.getDate() + 7)

            const { data: hearings, error: hearingsError } = await supabase
                .from('hearings')
                .select('id, date, time, case_id')
                .gte('date', today.toISOString().split('T')[0])
                .lte('date', sevenDaysLater.toISOString().split('T')[0])
                .order('date', { ascending: true })
                .limit(5)

            if (hearings && !hearingsError) {
                hearings.forEach(h => {
                    const hearingDate = new Date(`${h.date}T${h.time || '00:00'}`)
                    const daysUntil = Math.ceil((hearingDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24))
                    const timeText = daysUntil === 0 ? 'اليوم' : daysUntil === 1 ? 'غداً' : `بعد ${daysUntil} أيام`

                    notifications.push({
                        id: `hearing-${h.id}`,
                        type: 'hearing',
                        title: '⚖️ جلسة قادمة',
                        message: `جلسة - ${timeText}`,
                        timestamp: hearingDate,
                        read: false,
                        link: `/hearings`
                    })
                })
            }

            // 2. Fetch pending tasks
            const { data: tasks, error: tasksError } = await supabase
                .from('tasks')
                .select('id, title, due_date, status')
                .in('status', ['pending', 'in_progress'])
                .order('due_date', { ascending: true })
                .limit(10)

            if (tasks && !tasksError) {
                tasks.forEach(task => {
                    const dueDate = new Date(task.due_date)
                    const isOverdue = dueDate < today

                    notifications.push({
                        id: `task-${task.id}`,
                        type: 'task',
                        title: isOverdue ? '⚠️ مهمة متأخرة' : '✓ مهمة معلقة',
                        message: task.title,
                        timestamp: dueDate,
                        read: false,
                        link: `/tasks`
                    })
                })
            }

            // Sort by timestamp
            notifications.sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime())

            set({
                notifications,
                unreadCount: notifications.filter(n => !n.read).length,
                isLoading: false
            })
        } catch (error) {
            console.error('Failed to fetch notifications:', error)
            set({ isLoading: false })
        }
    },

    markAsRead: (id) => set((state) => ({
        notifications: state.notifications.map(n =>
            n.id === id ? { ...n, read: true } : n
        ),
        unreadCount: Math.max(0, state.unreadCount - 1)
    })),

    clearAll: () => set({ notifications: [], unreadCount: 0 }),
}))
