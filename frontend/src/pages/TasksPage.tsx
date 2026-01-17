import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { useBreadcrumb } from '../contexts/BreadcrumbContext'
import { supabase } from '../supabaseClient'
import { motion, AnimatePresence } from 'framer-motion'
import { toast } from 'sonner'
import {
    Plus, Search, Filter, Calendar, BarChart3, Clock, AlertCircle, CheckCircle, Edit, Trash2, Users, X, User, Eye
} from 'lucide-react'
import { useAuditLog } from '../hooks/useAuditLog'

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
    const [tasks, setTasks] = useState<Task[]>([])
    const [loading, setLoading] = useState(true)
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
    const [isDetailsModalOpen, setIsDetailsModalOpen] = useState(false)
    const [isEditModalOpen, setIsEditModalOpen] = useState(false)
    const [selectedTask, setSelectedTask] = useState<Task | null>(null)
    const [searchQuery, setSearchQuery] = useState('')
    const [statusFilter, setStatusFilter] = useState<'all' | 'pending' | 'in_progress' | 'completed'>('all')
    const [priorityFilter, setPriorityFilter] = useState<'all' | 'low' | 'medium' | 'high'>('all')

    useEffect(() => {
        setPageTitle('المهام')
    }, [setPageTitle])

    useEffect(() => {
        const lawyerId = getEffectiveLawyerId()
        if (lawyerId) {
            fetchTasks()
        }
    }, [getEffectiveLawyerId])

    const fetchTasks = async () => {
        try {
            const lawyerId = getEffectiveLawyerId()
            if (!lawyerId) return

            let query = supabase
                .from('tasks')
                .select(`
                    *,
                    assigned_user:users!tasks_assigned_to_fkey(full_name),
                    completed_user:users!tasks_completed_by_fkey(full_name)
                `)
                .eq('lawyer_id', lawyerId)
                .order('created_at', { ascending: false })

            if (isAssistant && profile) {
                query = query.or(`assigned_to.eq.${profile.id},assign_to_all.eq.true,user_id.eq.${profile.id}`)
            }

            const { data, error } = await query

            if (error) throw error
            setTasks(data || [])
        } catch (error: any) {
            console.error('Error fetching tasks:', error)
            toast.error('فشل تحميل المهام')
        } finally {
            setLoading(false)
        }
    }

    const updateTaskStatus = async (taskId: string, newStatus: 'pending' | 'in_progress' | 'completed') => {
        try {
            // الحصول على القيم القديمة
            const oldTask = tasks.find(t => t.id === taskId)

            const updateData: any = { status: newStatus }

            if (newStatus === 'completed') {
                updateData.completed_by = profile?.id
                updateData.completed_at = new Date().toISOString()
            } else {
                updateData.completed_by = null
                updateData.completed_at = null
            }

            const { error } = await supabase
                .from('tasks')
                .update(updateData)
                .eq('id', taskId)

            if (error) throw error

            // ✅ تسجيل التحديث باستخدام الخطاف الموحد
            if (oldTask) {
                await logAction(
                    'update',
                    'tasks',
                    taskId,
                    oldTask,
                    { ...oldTask, ...updateData },
                    'تحديث حالة المهمة'
                )
            }

            toast.success('تم تحديث حالة المهمة')
            fetchTasks()
        } catch (error: any) {
            console.error('Error updating task:', error)
            toast.error('فشل تحديث المهمة')
        }
    }

    const deleteTask = async (taskId: string) => {
        if (!confirm('هل أنت متأكد من حذف هذه المهمة؟')) return

        try {
            // الحصول على القيم القديمة قبل الحذف
            const oldTask = tasks.find(t => t.id === taskId)

            const { error } = await supabase
                .from('tasks')
                .delete()
                .eq('id', taskId)

            if (error) throw error

            // ✅ تسجيل الحذف
            if (oldTask) {
                await logAction('delete', 'tasks', taskId, oldTask, null, 'حذف مهمة')
            }

            toast.success('تم حذف المهمة')
            fetchTasks()
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

    if (loading) {
        return <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gold-500"></div>
        </div>
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
                        إدارة وتتبع المهام
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

            {/* Filters */}
            <div className="flex gap-3">
                {[
                    { value: 'all', label: 'الكل', count: tasks.length },
                    { value: 'pending', label: 'معلقة', count: tasks.filter(t => t.status === 'pending').length },
                    { value: 'completed', label: 'مكتملة', count: tasks.filter(t => t.status === 'completed').length }
                ].map((f) => (
                    <button
                        key={f.value}
                        onClick={() => setStatusFilter(f.value as any)}
                        className={`px-4 py-2 rounded-lg transition-all ${statusFilter === f.value
                            ? 'bg-cobalt-600 text-white'
                            : 'bg-obsidian-800 text-gray-400 hover:bg-obsidian-700'
                            }`}
                        style={{ fontFamily: 'Cairo, sans-serif' }}
                    >
                        {f.label} ({f.count})
                    </button>
                ))}
            </div>

            {/* Tasks Grid */}
            {tasks.length === 0 ? (
                <div className="glass-card p-12 text-center">
                    <AlertCircle className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                    <p className="text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        لا توجد مهام
                    </p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {tasks.map((task) => (
                        <motion.div
                            key={task.id}
                            initial={{ opacity: 1, y: 0 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="glass-card p-4 space-y-3"
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

            {/* Modals */}
            {isCreateModalOpen && (
                <CreateTaskModal
                    onClose={() => setIsCreateModalOpen(false)}
                    onSuccess={() => {
                        setIsCreateModalOpen(false)
                        fetchTasks()
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
                        fetchTasks()
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
            const lawyerId = getEffectiveLawyerId()
            if (!lawyerId) return

            const { data, error } = await supabase
                .from('users')
                .select('id, full_name, email')
                .eq('office_id', lawyerId)
                .eq('role', 'assistant')
                .eq('is_active', true)

            if (error) throw error
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

            const { error } = await supabase
                .from('tasks')
                .update(newData)
                .eq('id', task.id)

            if (error) throw error

            // ✅ تسجيل التعديل باستخدام useAuditLog
            const lawyerId = getEffectiveLawyerId()

            await logAction(
                'update',
                'tasks',
                task.id,
                { title: task.title, description: task.description, priority: task.priority },
                newData,
                'تعديل مهمة'
            )

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
            const lawyerId = getEffectiveLawyerId()
            if (!lawyerId) return

            const { data, error } = await supabase
                .from('users')
                .select('id, full_name, email')
                .eq('office_id', lawyerId)
                .eq('role', 'assistant')
                .eq('is_active', true)

            if (error) throw error
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
            const lawyerId = getEffectiveLawyerId()
            if (!lawyerId) throw new Error('خطأ في المصادقة')

            const taskData = {
                lawyer_id: lawyerId,
                user_id: profile?.id,
                title: formData.title,
                description: formData.description || null,
                execution_date: formData.execution_date || null,
                priority: formData.priority,
                assigned_to: formData.assign_to_all ? null : (formData.assigned_to || null),
                assign_to_all: formData.assign_to_all,
                status: 'pending'
            }

            const { data, error } = await supabase
                .from('tasks')
                .insert(taskData)
                .select()

            if (error) throw error

            // ✅ تسجيل الإنشاء باستخدام useAuditLog
            if (data && data[0]) {
                await logAction(
                    'create',
                    'tasks',
                    data[0].id,
                    null,
                    taskData,
                    'إضافة مهمة جديدة'
                )
            }

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
