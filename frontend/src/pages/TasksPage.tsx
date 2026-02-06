import { useState, useEffect, useRef, useCallback } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { useBreadcrumb } from '../contexts/BreadcrumbContext'
import { apiClient } from '../api/client'
import { motion, AnimatePresence } from 'framer-motion'
import { toast } from 'sonner'
import {
    Plus, Search, Filter, Calendar, BarChart3, Clock, AlertCircle, CheckCircle, Edit, Trash2, Users, X, User, Eye
} from 'lucide-react'
import { useAuditLog } from '../hooks/useAuditLog'
import { useInfiniteScroll } from '../hooks/useInfiniteScroll' // ✅ Import hook

interface Task {
    id: string
    title: string
    description: string
    execution_date: string
    priority: 'low' | 'medium' | 'high'
    status: 'pending' | 'in_progress' | 'completed'
    assigned_to: string | null
    assign_to_all: boolean
    completed_by?: string
    completed_at?: string
    created_at: string
    created_by: string
    case_id: string | null
    client_id: string | null
    lawyer_id: string
    assigned_user?: {
        full_name: string
    }
    completed_user?: {
        full_name: string
    }
}

interface Assistant {
    id: string
    full_name: string
    email: string
}

export function TasksPage() {
    const { getEffectiveLawyerId, profile, isAssistant } = useAuth()
    const { setPageTitle } = useBreadcrumb()
    const { logAction } = useAuditLog()

    const [searchQuery, setSearchQuery] = useState('')
    const [statusFilter, setStatusFilter] = useState<'all' | 'pending' | 'in_progress' | 'completed'>('all')
    const [priorityFilter, setPriorityFilter] = useState<'all' | 'low' | 'medium' | 'high'>('all')

    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
    const [isDetailsModalOpen, setIsDetailsModalOpen] = useState(false)
    const [isEditModalOpen, setIsEditModalOpen] = useState(false)
    const [selectedTask, setSelectedTask] = useState<Task | null>(null)

    // ✅ Use Infinite Scroll Hook
    const {
        data: tasks,
        loading,
        hasMore,
        loadMore,
        refresh,
        setParams,
        total
    } = useInfiniteScroll<Task>({
        endpoint: '/api/tasks',
        limit: 12, // 12 items per batch
        initialParams: {
            status: statusFilter === 'all' ? undefined : statusFilter,
            priority: priorityFilter === 'all' ? undefined : priorityFilter
        }
    })

    // Update params when filters change (Debounce search could be added here)
    useEffect(() => {
        setParams({
            status: statusFilter === 'all' ? undefined : statusFilter,
            priority: priorityFilter === 'all' ? undefined : priorityFilter,
            search: searchQuery || undefined
        })
    }, [statusFilter, priorityFilter, searchQuery, setParams])

    useEffect(() => {
        setPageTitle('المهام')
    }, [setPageTitle])


    // ✅ Observer for Infinite Scroll
    const observer = useRef<IntersectionObserver | null>(null)
    const lastTaskElementRef = useCallback((node: HTMLDivElement | null) => {
        if (loading) return
        if (observer.current) observer.current.disconnect()

        observer.current = new IntersectionObserver(entries => {
            if (entries[0].isIntersecting && hasMore) {
                loadMore()
            }
        })

        if (node) observer.current.observe(node)
    }, [loading, hasMore, loadMore])


    const updateTaskStatus = async (taskId: string, newStatus: 'pending' | 'in_progress' | 'completed') => {
        try {
            await apiClient.put(`/api/tasks/${taskId}/status`, { status: newStatus })
            toast.success('تم تحديث حالة المهمة')
            refresh() // Refresh list to reflect changes
        } catch (error: any) {
            console.error('Error updating task:', error)
            toast.error('فشل تحديث المهمة')
        }
    }

    const deleteTask = async (taskId: string) => {
        if (!confirm('هل أنت متأكد من حذف هذه المهمة؟')) return

        try {
            await apiClient.delete(`/api/tasks/${taskId}`)
            toast.success('تم حذف المهمة')
            refresh()
        } catch (error: any) {
            console.error('Error deleting task:', error)
            toast.error('فشل حذف المهمة')
        }
    }

    const getPriorityColor = (priority: string) => {
        switch (priority) {
            case 'high': return 'text-red-400 bg-red-500/20'
            case 'medium': return 'text-yellow-400 bg-yellow-500/20'
            case 'low': return 'text-green-400 bg-green-500/20'
            default: return 'text-gray-400 bg-gray-500/20'
        }
    }

    const getPriorityText = (priority: string) => {
        switch (priority) {
            case 'high': return 'عالية'
            case 'medium': return 'متوسطة'
            case 'low': return 'منخفضة'
            default: return priority
        }
    }

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'completed': return 'text-green-400 bg-green-500/20'
            case 'in_progress': return 'text-blue-400 bg-blue-500/20'
            case 'pending': return 'text-gray-400 bg-gray-500/20'
            default: return 'text-gray-400 bg-gray-500/20'
        }
    }

    const getStatusText = (status: string) => {
        switch (status) {
            case 'completed': return 'مكتملة'
            case 'in_progress': return 'قيد التنفيذ'
            case 'pending': return 'معلقة'
            default: return status
        }
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-white" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        المهام
                    </h1>
                    <p className="text-gray-400 mt-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        إدارة وتتبع المهام ({total})
                    </p>
                </div>
                {!isAssistant && (
                    <button
                        onClick={() => setIsCreateModalOpen(true)}
                        className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-cobalt-600 to-cobalt-700 text-white rounded-lg hover:from-cobalt-700 hover:to-cobalt-800 transition-all"
                        style={{ fontFamily: 'Cairo, sans-serif' }}
                    >
                        <Plus className="w-4 h-4" />
                        <span>مهمة جديدة</span>
                    </button>
                )}
            </div>

            {/* Filters & Search */}
            <div className="flex flex-col md:flex-row gap-4 items-center justify-between bg-obsidian-800/50 p-4 rounded-xl border border-gold-500/10">
                {/* Search */}
                <div className="relative w-full md:w-96">
                    <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="بحث في المهام..."
                        className="w-full pr-10 pl-4 py-2 bg-obsidian-900/80 border border-gray-700 rounded-lg focus:border-gold-500 focus:outline-none text-white"
                        style={{ fontFamily: 'Cairo, sans-serif' }}
                    />
                </div>

                {/* Status Filters */}
                <div className="flex gap-2 overflow-x-auto pb-2 md:pb-0 w-full md:w-auto">
                    {[
                        { value: 'all', label: 'الكل' },
                        { value: 'pending', label: 'معلقة' },
                        { value: 'in_progress', label: 'قيد التنفيذ' },
                        { value: 'completed', label: 'مكتملة' }
                    ].map((f) => (
                        <button
                            key={f.value}
                            onClick={() => setStatusFilter(f.value as any)}
                            className={`px-4 py-2 rounded-lg transition-all whitespace-nowrap ${statusFilter === f.value
                                ? 'bg-cobalt-600 text-white'
                                : 'bg-obsidian-900 text-gray-400 hover:bg-obsidian-700'
                                }`}
                            style={{ fontFamily: 'Cairo, sans-serif' }}
                        >
                            {f.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* Tasks Grid */}
            {tasks.length === 0 && !loading ? (
                <div className="glass-card p-12 text-center">
                    <AlertCircle className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                    <p className="text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        لا توجد مهام مطابقة للبحث
                    </p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {tasks.map((task, index) => (
                        <motion.div
                            key={task.id}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: index * 0.05 }}
                            ref={index === tasks.length - 1 ? lastTaskElementRef : null} // ✅ Attach Observer to last element
                            className="glass-card p-4 space-y-3 hover:border-gold-500/30 transition-all group"
                        >
                            {/* Header */}
                            <div className="flex items-start justify-between">
                                <h3 className="text-white font-bold flex-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                    {task.title}
                                </h3>
                                <span className={`px-2 py-1 text-xs rounded ${getPriorityColor(task.priority)}`} style={{ fontFamily: 'Cairo, sans-serif' }}>
                                    {getPriorityText(task.priority)}
                                </span>
                            </div>

                            {/* Description - ✅ اختصار 100 حرف */}
                            {task.description && (
                                <p className="text-sm text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                    {task.description.length > 100
                                        ? task.description.substring(0, 100) + '...'
                                        : task.description}
                                </p>
                            )}

                            {/* Meta Info */}
                            <div className="space-y-2 text-xs text-gray-500">
                                {task.execution_date && (
                                    <div className="flex items-center gap-2">
                                        <Calendar className="w-3 h-3" />
                                        <span style={{ fontFamily: 'Cairo, sans-serif' }}>
                                            {new Date(task.execution_date).toLocaleDateString('ar-EG')}
                                        </span>
                                    </div>
                                )}

                                <div className="flex items-center gap-2">
                                    {task.assign_to_all ? (
                                        <>
                                            <Users className="w-3 h-3" />
                                            <span style={{ fontFamily: 'Cairo, sans-serif' }}>للجميع</span>
                                        </>
                                    ) : task.assigned_user ? (
                                        <>
                                            <User className="w-3 h-3" />
                                            <span style={{ fontFamily: 'Cairo, sans-serif' }}>
                                                {task.assigned_user.full_name}
                                            </span>
                                        </>
                                    ) : null}
                                </div>

                                {task.completed_by && task.completed_user && (
                                    <div className="flex items-center gap-2 text-green-400">
                                        <CheckCircle className="w-3 h-3" />
                                        <span style={{ fontFamily: 'Cairo, sans-serif' }}>
                                            أكملها: {task.completed_user.full_name}
                                        </span>
                                    </div>
                                )}
                            </div>

                            {/* Status & Actions */}
                            <div className="flex items-center justify-between pt-3 border-t border-gold-500/10">
                                <span className={`px-2 py-1 text-xs rounded ${getStatusColor(task.status)}`} style={{ fontFamily: 'Cairo, sans-serif' }}>
                                    {getStatusText(task.status)}
                                </span>

                                {/* ✅ أزرار جديدة: عرض/تعديل/حذف */}
                                <div className="flex gap-1">
                                    {/* عرض */}
                                    <button
                                        onClick={() => {
                                            setSelectedTask(task)
                                            setIsDetailsModalOpen(true)
                                        }}
                                        className="p-1.5 hover:bg-blue-500/20 text-blue-400 rounded transition-colors"
                                        title="عرض التفاصيل"
                                    >
                                        <Eye className="w-4 h-4" />
                                    </button>

                                    {/* تعديل */}
                                    {!isAssistant && (
                                        <button
                                            onClick={() => {
                                                setSelectedTask(task)
                                                setIsEditModalOpen(true)
                                            }}
                                            className="p-1.5 hover:bg-yellow-500/20 text-yellow-400 rounded transition-colors"
                                            title="تعديل"
                                        >
                                            <Edit className="w-4 h-4" />
                                        </button>
                                    )}

                                    {/* حذف */}
                                    {!isAssistant && (
                                        <button
                                            onClick={() => deleteTask(task.id)}
                                            className="p-1.5 hover:bg-red-500/20 text-red-400 rounded transition-colors"
                                            title="حذف"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    )}

                                    {/* إكمال/إعادة فتح */}
                                    {task.status !== 'completed' ? (
                                        <button
                                            onClick={() => updateTaskStatus(task.id, 'completed')}
                                            className="p-1.5 hover:bg-green-500/20 text-green-400 rounded transition-colors"
                                            title="إكمال"
                                        >
                                            <CheckCircle className="w-4 h-4" />
                                        </button>
                                    ) : (
                                        <button
                                            onClick={() => updateTaskStatus(task.id, 'pending')}
                                            className="p-1.5 hover:bg-gray-500/20 text-gray-400 rounded transition-colors"
                                            title="إعادة فتح"
                                        >
                                            <Clock className="w-4 h-4" />
                                        </button>
                                    )}
                                </div>
                            </div>
                        </motion.div>
                    ))}
                </div>
            )}

            {loading && (
                <div className="flex justify-center p-4">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gold-500"></div>
                </div>
            )}

            {/* Modals */}
            {isCreateModalOpen && (
                <CreateTaskModal
                    onClose={() => setIsCreateModalOpen(false)}
                    onSuccess={() => {
                        setIsCreateModalOpen(false)
                        refresh()
                    }}
                />
            )}

            {isDetailsModalOpen && selectedTask && (
                <TaskDetailsModal
                    task={selectedTask}
                    onClose={() => {
                        setIsDetailsModalOpen(false)
                        setSelectedTask(null)
                    }}
                />
            )}

            {isEditModalOpen && selectedTask && (
                <EditTaskModal
                    task={selectedTask}
                    onClose={() => {
                        setIsEditModalOpen(false)
                        setSelectedTask(null)
                    }}
                    onSuccess={() => {
                        setIsEditModalOpen(false)
                        setSelectedTask(null)
                        refresh()
                    }}
                />
            )}
        </div>
    )
}

// Task Details Modal
interface TaskDetailsModalProps {
    task: Task
    onClose: () => void
}

function TaskDetailsModal({ task, onClose }: TaskDetailsModalProps) {
    return (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="backdrop-blur-xl bg-obsidian-800/90 border border-gold-500/20 rounded-2xl p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto"
            >
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-bold text-gold-500" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        تفاصيل المهمة
                    </h2>
                    <button onClick={onClose} className="text-gray-400 hover:text-white">
                        <X className="w-6 h-6" />
                    </button>
                </div>

                <div className="space-y-4">
                    {/* العنوان */}
                    <div>
                        <label className="text-sm text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>العنوان</label>
                        <p className="text-white font-bold mt-1" style={{ fontFamily: 'Cairo, sans-serif' }}>{task.title}</p>
                    </div>

                    {/* الوصف */}
                    {task.description && (
                        <div>
                            <label className="text-sm text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>الوصف</label>
                            <p className="text-white mt-1 whitespace-pre-wrap" style={{ fontFamily: 'Cairo, sans-serif' }}>{task.description}</p>
                        </div>
                    )}

                    {/* التاريخ والأولوية */}
                    <div className="grid grid-cols-2 gap-4">
                        {task.execution_date && (
                            <div>
                                <label className="text-sm text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>تاريخ التنفيذ</label>
                                <p className="text-white mt-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                    {new Date(task.execution_date).toLocaleDateString('ar-EG')}
                                </p>
                            </div>
                        )}
                        <div>
                            <label className="text-sm text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>الأولوية</label>
                            <p className="text-white mt-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                {task.priority === 'high' ? 'عالية' : task.priority === 'medium' ? 'متوسطة' : 'منخفضة'}
                            </p>
                        </div>
                    </div>

                    {/* الحالة */}
                    <div>
                        <label className="text-sm text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>الحالة</label>
                        <p className="text-white mt-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            {task.status === 'completed' ? 'مكتملة' : task.status === 'in_progress' ? 'قيد التنفيذ' : 'معلقة'}
                        </p>
                    </div>

                    {/* المُسند إليه */}
                    <div>
                        <label className="text-sm text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>المُسند إليه</label>
                        <p className="text-white mt-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            {task.assign_to_all ? 'للجميع' : task.assigned_user?.full_name || 'غير محدد'}
                        </p>
                    </div>

                    {/* إذا تم الإكمال */}
                    {task.completed_by && task.completed_user && (
                        <div className="pt-4 border-t border-gold-500/10">
                            <label className="text-sm text-green-400" style={{ fontFamily: 'Cairo, sans-serif' }}>تم الإكمال بواسطة</label>
                            <p className="text-white mt-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                {task.completed_user.full_name}
                            </p>
                            {task.completed_at && (
                                <p className="text-sm text-gray-400 mt-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                    {new Date(task.completed_at).toLocaleString('ar-EG')}
                                </p>
                            )}
                        </div>
                    )}
                </div>

                <div className="flex justify-end pt-6">
                    <button
                        onClick={onClose}
                        className="px-6 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
                        style={{ fontFamily: 'Cairo, sans-serif' }}
                    >
                        إغلاق
                    </button>
                </div>
            </motion.div>
        </div>
    )
}

// Edit Task Modal
interface EditTaskModalProps {
    task: Task
    onClose: () => void
    onSuccess: () => void
}

function EditTaskModal({ task, onClose, onSuccess }: EditTaskModalProps) {
    const { getEffectiveLawyerId, profile } = useAuth()
    const { logAction } = useAuditLog() // ✅ استخدام الخطاف
    const [loading, setLoading] = useState(false)
    const [assistants, setAssistants] = useState<Assistant[]>([])
    const [formData, setFormData] = useState({
        title: task.title,
        description: task.description || '',
        execution_date: task.execution_date || '',
        priority: task.priority,
        assigned_to: task.assigned_to || '',
        assign_to_all: task.assign_to_all
    })

    useEffect(() => {
        fetchAssistants()
    }, [])

    const fetchAssistants = async () => {
        try {
            // ✅ BFF Pattern: استخدام apiClient
            const data = await apiClient.get<Assistant[]>('/api/tasks/assistants')
            setAssistants(data || [])
        } catch (error) {
            console.error('Error fetching assistants:', error)
        }
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()

        if (!formData.title.trim()) {
            toast.error('عنوان المهمة مطلوب')
            return
        }

        setLoading(true)

        try {
            const newData = {
                title: formData.title,
                description: formData.description || null,
                execution_date: formData.execution_date || null,
                priority: formData.priority,
                assigned_to: formData.assign_to_all ? null : (formData.assigned_to || null),
                assign_to_all: formData.assign_to_all
            }

            // ✅ BFF Pattern: Backend يتولى التحقق والتسجيل
            await apiClient.put(`/api/tasks/${task.id}`, newData)

            toast.success('تم تحديث المهمة بنجاح')
            onSuccess()
        } catch (error: any) {
            console.error('Error updating task:', error)
            toast.error('فشل تحديث المهمة')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="backdrop-blur-xl bg-obsidian-800/90 border border-gold-500/20 rounded-2xl p-6 max-w-lg w-full"
            >
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-bold text-gold-500" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        تعديل المهمة
                    </h2>
                    <button onClick={onClose} className="text-gray-400 hover:text-white">
                        <X className="w-6 h-6" />
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            العنوان *
                        </label>
                        <input
                            type="text"
                            value={formData.title}
                            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                            className="w-full px-3 py-2 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white"
                            style={{ fontFamily: 'Cairo, sans-serif' }}
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            الوصف
                        </label>
                        <textarea
                            value={formData.description}
                            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                            rows={3}
                            className="w-full px-3 py-2 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white"
                            style={{ fontFamily: 'Cairo, sans-serif' }}
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                تاريخ التنفيذ
                            </label>
                            <input
                                type="date"
                                value={formData.execution_date}
                                onChange={(e) => setFormData({ ...formData, execution_date: e.target.value })}
                                className="w-full px-3 py-2 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                الأولوية
                            </label>
                            <select
                                value={formData.priority}
                                onChange={(e) => setFormData({ ...formData, priority: e.target.value as any })}
                                className="w-full px-3 py-2 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white"
                                style={{ fontFamily: 'Cairo, sans-serif' }}
                            >
                                <option value="low">منخفضة</option>
                                <option value="medium">متوسطة</option>
                                <option value="high">عالية</option>
                            </select>
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            إسناد المهمة
                        </label>

                        <div className="flex items-center gap-2 mb-3 p-3 bg-obsidian-900/30 rounded-lg">
                            <input
                                type="checkbox"
                                id="edit_assign_to_all"
                                checked={formData.assign_to_all}
                                onChange={(e) => setFormData({
                                    ...formData,
                                    assign_to_all: e.target.checked,
                                    assigned_to: e.target.checked ? '' : formData.assigned_to
                                })}
                                className="w-4 h-4 rounded"
                            />
                            <label htmlFor="edit_assign_to_all" className="text-white text-sm flex items-center gap-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                <Users className="w-4 h-4" />
                                إرسال للجميع
                            </label>
                        </div>

                        {!formData.assign_to_all && (
                            <select
                                value={formData.assigned_to}
                                onChange={(e) => setFormData({ ...formData, assigned_to: e.target.value })}
                                className="w-full px-3 py-2 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white"
                                style={{ fontFamily: 'Cairo, sans-serif' }}
                            >
                                <option value="">-- اختر مساعد --</option>
                                {assistants.map((assistant) => (
                                    <option key={assistant.id} value={assistant.id}>
                                        {assistant.full_name}
                                    </option>
                                ))}
                            </select>
                        )}
                    </div>

                    <div className="flex gap-3 pt-4">
                        <button
                            type="submit"
                            disabled={loading}
                            className="flex-1 px-6 py-3 bg-cobalt-600 text-white font-bold rounded-lg hover:bg-cobalt-700 disabled:opacity-50"
                            style={{ fontFamily: 'Cairo, sans-serif' }}
                        >
                            {loading ? 'جاري الحفظ...' : 'حفظ التعديلات'}
                        </button>
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-6 py-3 bg-gray-600 text-white font-bold rounded-lg hover:bg-gray-700"
                            style={{ fontFamily: 'Cairo, sans-serif' }}
                        >
                            إلغاء
                        </button>
                    </div>
                </form>
            </motion.div>
        </div>
    )
}

// Create Task Modal (نفس الكود السابق)
interface CreateTaskModalProps {
    onClose: () => void
    onSuccess: () => void
}

function CreateTaskModal({ onClose, onSuccess }: CreateTaskModalProps) {
    const { getEffectiveLawyerId, profile } = useAuth()
    const { logAction } = useAuditLog() // ✅ استخدام الخطاف
    const [loading, setLoading] = useState(false)
    const [assistants, setAssistants] = useState<Assistant[]>([])
    const [formData, setFormData] = useState({
        title: '',
        description: '',
        execution_date: '',
        priority: 'medium',
        assigned_to: '',
        assign_to_all: false
    })

    useEffect(() => {
        fetchAssistants()
    }, [])

    const fetchAssistants = async () => {
        try {
            // ✅ BFF Pattern: استخدام apiClient
            const data = await apiClient.get<Assistant[]>('/api/tasks/assistants')
            setAssistants(data || [])
        } catch (error) {
            console.error('Error fetching assistants:', error)
        }
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()

        if (!formData.title.trim()) {
            toast.error('عنوان المهمة مطلوب')
            return
        }

        setLoading(true)

        try {
            // ✅ BFF Pattern: Backend يتولى تعيين lawyer_id من JWT وتسجيل التدقيق
            const taskData = {
                title: formData.title,
                description: formData.description || null,
                execution_date: formData.execution_date || null,
                priority: formData.priority,
                assigned_to: formData.assign_to_all ? null : (formData.assigned_to || null),
                assign_to_all: formData.assign_to_all
            }

            await apiClient.post('/api/tasks', taskData)

            toast.success('تم إنشاء المهمة بنجاح')
            onSuccess()
        } catch (error: any) {
            console.error('Error creating task:', error)
            toast.error('فشل إنشاء المهمة')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="backdrop-blur-xl bg-obsidian-800/90 border border-gold-500/20 rounded-2xl p-6 max-w-lg w-full"
            >
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-bold text-gold-500" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        مهمة جديدة
                    </h2>
                    <button onClick={onClose} className="text-gray-400 hover:text-white">
                        <X className="w-6 h-6" />
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            العنوان *
                        </label>
                        <input
                            type="text"
                            value={formData.title}
                            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                            className="w-full px-3 py-2 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white"
                            style={{ fontFamily: 'Cairo, sans-serif' }}
                            placeholder="مثال: مراجعة عقد البيع"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            الوصف
                        </label>
                        <textarea
                            value={formData.description}
                            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                            rows={3}
                            className="w-full px-3 py-2 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white"
                            style={{ fontFamily: 'Cairo, sans-serif' }}
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                تاريخ التنفيذ
                            </label>
                            <input
                                type="date"
                                value={formData.execution_date}
                                onChange={(e) => setFormData({ ...formData, execution_date: e.target.value })}
                                className="w-full px-3 py-2 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                الأولوية
                            </label>
                            <select
                                value={formData.priority}
                                onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                                className="w-full px-3 py-2 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white"
                                style={{ fontFamily: 'Cairo, sans-serif' }}
                            >
                                <option value="low">منخفضة</option>
                                <option value="medium">متوسطة</option>
                                <option value="high">عالية</option>
                            </select>
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            إسناد المهمة
                        </label>

                        <div className="flex items-center gap-2 mb-3 p-3 bg-obsidian-900/30 rounded-lg">
                            <input
                                type="checkbox"
                                id="assign_to_all"
                                checked={formData.assign_to_all}
                                onChange={(e) => setFormData({
                                    ...formData,
                                    assign_to_all: e.target.checked,
                                    assigned_to: e.target.checked ? '' : formData.assigned_to
                                })}
                                className="w-4 h-4 rounded"
                            />
                            <label htmlFor="assign_to_all" className="text-white text-sm flex items-center gap-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                <Users className="w-4 h-4" />
                                إرسال للجميع
                            </label>
                        </div>

                        {!formData.assign_to_all && (
                            <select
                                value={formData.assigned_to}
                                onChange={(e) => setFormData({ ...formData, assigned_to: e.target.value })}
                                className="w-full px-3 py-2 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white"
                                style={{ fontFamily: 'Cairo, sans-serif' }}
                            >
                                <option value="">-- اختر مساعد --</option>
                                {assistants.map((assistant) => (
                                    <option key={assistant.id} value={assistant.id}>
                                        {assistant.full_name}
                                    </option>
                                ))}
                            </select>
                        )}
                    </div>

                    <div className="flex gap-3 pt-4">
                        <button
                            type="submit"
                            disabled={loading}
                            className="flex-1 px-6 py-3 bg-cobalt-600 text-white font-bold rounded-lg hover:bg-cobalt-700 disabled:opacity-50"
                            style={{ fontFamily: 'Cairo, sans-serif' }}
                        >
                            {loading ? 'جاري الحفظ...' : 'إنشاء المهمة'}
                        </button>
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-6 py-3 bg-gray-600 text-white font-bold rounded-lg hover:bg-gray-700"
                            style={{ fontFamily: 'Cairo, sans-serif' }}
                        >
                            إلغاء
                        </button>
                    </div>
                </form>
            </motion.div>
        </div>
    )
}
