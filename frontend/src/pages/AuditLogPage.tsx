import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { useBreadcrumb } from '../contexts/BreadcrumbContext'
import { supabase } from '../supabaseClient'
import { motion, AnimatePresence } from 'framer-motion'
import { toast } from 'sonner'
import {
    FileText,
    Search,
    Calendar,
    User,
    Info,
    Plus,
    Edit,
    Trash2,
    Eye,
    X,
    Filter
} from 'lucide-react'

interface AuditLog {
    id: string
    action: 'create' | 'update' | 'delete'
    table_name: string
    record_id: string
    user_id: string | null
    user_name: string | null
    user_role: string | null
    old_values: any
    new_values: any
    changes: any
    description: string | null
    created_at: string
    lawyer_id: string
}

export function AuditLogPage() {
    const { getEffectiveLawyerId } = useAuth()
    const { setPageTitle } = useBreadcrumb()
    const [logs, setLogs] = useState<AuditLog[]>([])
    const [loading, setLoading] = useState(true)
    const [searchQuery, setSearchQuery] = useState('')
    const [actionFilter, setActionFilter] = useState<'all' | 'create' | 'update' | 'delete'>('all')
    const [tableFilter, setTableFilter] = useState('all')
    const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null)

    useEffect(() => {
        setPageTitle('سجل العمليات')
    }, [setPageTitle])

    useEffect(() => {
        const lawyerId = getEffectiveLawyerId()
        if (lawyerId) {
            fetchLogs()
        }
    }, [getEffectiveLawyerId, actionFilter, tableFilter])

    const fetchLogs = async () => {
        try {
            const lawyerId = getEffectiveLawyerId()
            if (!lawyerId) return

            let query = supabase
                .from('audit_logs')
                .select('*')
                .eq('lawyer_id', lawyerId)
                .order('created_at', { ascending: false })
                .limit(100)

            if (actionFilter !== 'all') {
                query = query.eq('action', actionFilter)
            }

            if (tableFilter !== 'all') {
                query = query.eq('table_name', tableFilter)
            }

            const { data, error } = await query

            if (error) throw error
            setLogs(data || [])
        } catch (error: any) {
            console.error('Error fetching audit logs:', error)
            toast.error('فشل تحميل السجل')
        } finally {
            setLoading(false)
        }
    }

    const filteredLogs = logs.filter(log => {
        if (!searchQuery) return true
        const query = searchQuery.toLowerCase()
        return (
            log.user_name?.toLowerCase().includes(query) ||
            log.table_name.toLowerCase().includes(query) ||
            log.description?.toLowerCase().includes(query)
        )
    })

    const uniqueTables = ['all', ...new Set(logs.map(log => log.table_name))]

    const getActionIcon = (action: string) => {
        switch (action) {
            case 'create': return <Plus className="w-4 h-4" />
            case 'update': return <Edit className="w-4 h-4" />
            case 'delete': return <Trash2 className="w-4 h-4" />
            default: return <Info className="w-4 h-4" />
        }
    }

    const getActionColor = (action: string) => {
        switch (action) {
            case 'create': return 'text-green-400'
            case 'update': return 'text-blue-400'
            case 'delete': return 'text-red-400'
            default: return 'text-gray-400'
        }
    }

    const getActionText = (action: string) => {
        switch (action) {
            case 'create': return 'إضافة'
            case 'update': return 'تعديل'
            case 'delete': return 'حذف'
            default: return action
        }
    }

    const getTableText = (table: string) => {
        const tableNames: { [key: string]: string } = {
            'clients': 'موكل',
            'cases': 'قضية',
            'tasks': 'مهمة',
            'hearings': 'جلسة',
            'documents': 'مستند',
            'opponents': 'خصم',
            'users': 'مستخدم'
        }
        return tableNames[table] || table
    }

    const getFieldName = (fieldKey: string): string => {
        const fieldNames: { [key: string]: string } = {
            'title': 'العنوان',
            'description': 'الوصف',
            'status': 'الحالة',
            'priority': 'الأولوية',
            'execution_date': 'تاريخ التنفيذ',
            'completed_by': 'أكمله',
            'completed_at': 'تاريخ الإكمال',
            'assigned_to': 'مسند إلى',
            'assign_to_all': 'للجميع',
            'full_name': 'الاسم الكامل',
            'email': 'البريد الإلكتروني',
            'phone': 'الهاتف',
            'address': 'العنوان'
        }
        return fieldNames[fieldKey] || fieldKey
    }

    const formatValue = (value: any): string => {
        if (value === null || value === undefined) return 'فارغ'
        if (typeof value === 'boolean') return value ? 'نعم' : 'لا'
        if (typeof value === 'string' && value.includes('T') && value.includes('Z')) {
            try {
                return new Date(value).toLocaleString('ar-EG')
            } catch {
                return value
            }
        }
        const translations: { [key: string]: string } = {
            'pending': 'معلقة',
            'completed': 'مكتملة',
            'in_progress': 'قيد التنفيذ',
            'high': 'عالية',
            'medium': 'متوسطة',
            'low': 'منخفضة'
        }
        return translations[value] || value.toString()
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-white" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        سجل العمليات
                    </h1>
                    <p className="text-gray-400 mt-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        تتبع ومراقبة جميع الإجراءات في النظام
                    </p>
                </div>
            </div>

            {/* Filters Bar */}
            <div className="glass-card p-4">
                <div className="flex flex-wrap gap-4 items-center justify-between">
                    <div className="relative flex-1 min-w-[300px]">
                        <Search className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                        <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="بحث في السجل (بواسطة الاسم، الإجراء...)"
                            className="w-full pr-10 pl-4 py-2 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white"
                            style={{ fontFamily: 'Cairo, sans-serif' }}
                        />
                    </div>

                    <div className="flex gap-2">
                        <select
                            value={tableFilter}
                            onChange={(e) => setTableFilter(e.target.value)}
                            className="px-4 py-2 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white"
                            style={{ fontFamily: 'Cairo, sans-serif' }}
                        >
                            <option value="all">جميع الجداول</option>
                            {uniqueTables.filter(t => t !== 'all').map((table) => (
                                <option key={table} value={table}>{getTableText(table)}</option>
                            ))}
                        </select>

                        <div className="flex rounded-lg overflow-hidden border border-gold-500/20">
                            {[
                                { value: 'all', label: 'الكل' },
                                { value: 'create', label: 'إضافة' },
                                { value: 'update', label: 'تعديل' },
                                { value: 'delete', label: 'حذف' }
                            ].map((f) => (
                                <button
                                    key={f.value}
                                    onClick={() => setActionFilter(f.value as any)}
                                    className={`px-3 py-2 text-sm transition-all ${actionFilter === f.value
                                        ? 'bg-cobalt-600 text-white'
                                        : 'bg-obsidian-900/50 text-gray-400 hover:bg-obsidian-800'
                                        }`}
                                    style={{ fontFamily: 'Cairo, sans-serif' }}
                                >
                                    {f.label}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            {/* Table View */}
            <div className="glass-card overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-right">
                        <thead>
                            <tr className="border-b border-gold-500/10 bg-obsidian-900/50">
                                <th className="px-6 py-4 text-sm font-bold text-gold-500" style={{ fontFamily: 'Cairo, sans-serif' }}>الإجراء</th>
                                <th className="px-6 py-4 text-sm font-bold text-gold-500" style={{ fontFamily: 'Cairo, sans-serif' }}>قام بالإجراء</th>
                                <th className="px-6 py-4 text-sm font-bold text-gold-500" style={{ fontFamily: 'Cairo, sans-serif' }}>التفاصيل</th>
                                <th className="px-6 py-4 text-sm font-bold text-gold-500" style={{ fontFamily: 'Cairo, sans-serif' }}>التاريخ</th>
                                <th className="px-6 py-4 text-sm font-bold text-gold-500" style={{ fontFamily: 'Cairo, sans-serif' }}>عرض</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gold-500/5">
                            {loading ? (
                                <tr>
                                    <td colSpan={5} className="px-6 py-8 text-center text-gray-400">
                                        جاري تحميل السجلات...
                                    </td>
                                </tr>
                            ) : filteredLogs.length === 0 ? (
                                <tr>
                                    <td colSpan={5} className="px-6 py-8 text-center text-gray-400">
                                        لا توجد سجلات مطابقة
                                    </td>
                                </tr>
                            ) : (
                                filteredLogs.map((log) => (
                                    <tr key={log.id} className="hover:bg-white/5 transition-colors">
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-3">
                                                <div className={`p-2 rounded-lg bg-white/5 ${getActionColor(log.action)}`}>
                                                    {getActionIcon(log.action)}
                                                </div>
                                                <div>
                                                    <p className="text-white font-medium" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                                        {getActionText(log.action)} {getTableText(log.table_name)}
                                                    </p>
                                                    <span className="text-xs text-gray-500">
                                                        {log.action === 'create' ? 'إنشاء جديد' : log.action === 'update' ? 'تحديث بيانات' : 'حذف نهائي'}
                                                    </span>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-2 text-gray-300">
                                                <User className="w-4 h-4 text-cobalt-400" />
                                                <span style={{ fontFamily: 'Cairo, sans-serif' }}>
                                                    {log.user_name || 'غير معروف'}
                                                </span>
                                            </div>
                                            <span className="text-xs text-gray-500 mr-6">
                                                {log.user_role === 'lawyer' ? 'محامي' : 'مساعد'}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4">
                                            <p className="text-sm text-gray-300 max-w-xs truncate" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                                {log.description || '-'}
                                                {log.new_values?.title && ` - ${log.new_values.title}`}
                                                {log.new_values?.full_name && ` - ${log.new_values.full_name}`}
                                            </p>
                                        </td>
                                        <td className="px-6 py-4 text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                            <div className="flex flex-col text-sm">
                                                <span>{new Date(log.created_at).toLocaleDateString('ar-EG')}</span>
                                                <span className="text-xs text-gray-600">{new Date(log.created_at).toLocaleTimeString('ar-EG')}</span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <button
                                                onClick={() => setSelectedLog(log)}
                                                className="p-2 text-cobalt-400 hover:text-cobalt-300 hover:bg-cobalt-500/10 rounded-lg transition-colors"
                                            >
                                                <Eye className="w-5 h-5" />
                                            </button>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Details Modal */}
            <AnimatePresence>
                {selectedLog && (
                    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                        <motion.div
                            initial={{ opacity: 1, scale: 1 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.95 }}
                            className="glass-card w-full max-w-2xl max-h-[80vh] overflow-hidden flex flex-col"
                        >
                            <div className="p-6 border-b border-gold-500/10 flex items-center justify-between">
                                <h2 className="text-xl font-bold text-white flex items-center gap-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                    <FileText className="w-5 h-5 text-gold-500" />
                                    تفاصيل الإجراء
                                </h2>
                                <button
                                    onClick={() => setSelectedLog(null)}
                                    className="text-gray-400 hover:text-white transition-colors"
                                >
                                    <X className="w-6 h-6" />
                                </button>
                            </div>

                            <div className="p-6 overflow-y-auto flex-1">
                                <div className="grid grid-cols-2 gap-4 mb-6">
                                    <div className="bg-white/5 p-4 rounded-lg">
                                        <label className="text-xs text-gray-500 block mb-1">الإجراء</label>
                                        <p className="text-white font-medium">{getActionText(selectedLog.action)}</p>
                                    </div>
                                    <div className="bg-white/5 p-4 rounded-lg">
                                        <label className="text-xs text-gray-500 block mb-1">الكيان</label>
                                        <p className="text-white font-medium">{getTableText(selectedLog.table_name)}</p>
                                    </div>
                                    <div className="bg-white/5 p-4 rounded-lg">
                                        <label className="text-xs text-gray-500 block mb-1">بواسطة</label>
                                        <p className="text-white font-medium">{selectedLog.user_name}</p>
                                    </div>
                                    <div className="bg-white/5 p-4 rounded-lg">
                                        <label className="text-xs text-gray-500 block mb-1">التاريخ</label>
                                        <p className="text-white font-medium">{new Date(selectedLog.created_at).toLocaleString('ar-EG')}</p>
                                    </div>
                                </div>

                                <h3 className="text-lg font-bold text-gold-500 mb-4" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                    التغييرات المسجلة
                                </h3>

                                <div className="space-y-4">
                                    {selectedLog.action === 'update' && selectedLog.changes ? (
                                        Object.entries(selectedLog.changes).map(([key, value]: [string, any]) => (
                                            <div key={key} className="bg-obsidian-900/50 p-4 rounded-lg border border-gold-500/10">
                                                <div className="font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                                    {getFieldName(key)}
                                                </div>
                                                <div className="grid grid-cols-2 gap-4">
                                                    <div>
                                                        <span className="text-xs text-red-400 block mb-1">القيمة القديمة:</span>
                                                        <div className="text-gray-300 text-sm bg-black/20 p-2 rounded break-all">
                                                            {formatValue(value.old)}
                                                        </div>
                                                    </div>
                                                    <div>
                                                        <span className="text-xs text-green-400 block mb-1">القيمة الجديدة:</span>
                                                        <div className="text-white text-sm bg-black/20 p-2 rounded break-all">
                                                            {formatValue(value.new)}
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        ))
                                    ) : (
                                        <div className="bg-obsidian-900/50 p-4 rounded-lg border border-gold-500/10">
                                            <div className="font-medium text-gold-500 mb-2">بيانات السجل</div>
                                            <pre className="text-xs text-gray-300 overflow-x-auto whitespace-pre-wrap font-mono bg-black/20 p-3 rounded">
                                                {JSON.stringify(
                                                    selectedLog.action === 'create' ? selectedLog.new_values :
                                                        selectedLog.action === 'delete' ? selectedLog.old_values :
                                                            { ...selectedLog.new_values },
                                                    null, 2
                                                )}
                                            </pre>
                                        </div>
                                    )}
                                </div>
                            </div>

                            <div className="p-4 border-t border-gold-500/10 bg-obsidian-900/50 flex justify-end">
                                <button
                                    onClick={() => setSelectedLog(null)}
                                    className="px-6 py-2 bg-gray-600 hover:bg-gray-500 text-white rounded-lg transition-colors"
                                    style={{ fontFamily: 'Cairo, sans-serif' }}
                                >
                                    إغلاق
                                </button>
                            </div>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>
        </div>
    )
}
