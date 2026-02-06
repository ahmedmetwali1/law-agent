import { useAuth } from '../contexts/AuthContext'
import { apiClient } from '../api/client'

export const useAuditLog = () => {
    const { getEffectiveLawyerId, profile } = useAuth()

    const logAction = async (
        action: 'create' | 'update' | 'delete',
        tableName: string,
        recordId: string,
        oldValues: any = null,
        newValues: any = null,
        description: string = ''
    ) => {
        try {
            const lawyerId = getEffectiveLawyerId()
            if (!lawyerId) return

            const changes = action === 'update' && oldValues && newValues
                ? Object.keys(newValues).reduce((acc: any, key) => {
                    const oldVal = oldValues[key]
                    const newVal = newValues[key]

                    if (JSON.stringify(oldVal) !== JSON.stringify(newVal)) {
                        acc[key] = { old: oldVal, new: newVal }
                    }
                    return acc
                }, {})
                : null

            // إذا كانت عملية تحديث ولم تكن هناك تغييرات فعلية، لا تقم بالتسجيل
            if (action === 'update' && changes && Object.keys(changes).length === 0) {
                return
            }

            // Use Backend API instead of direct Supabase
            await apiClient.post('/api/audit/log', {
                action,
                table_name: tableName,
                record_id: recordId,
                old_values: oldValues,
                new_values: newValues,
                changes: changes,
                description: description || `${action === 'create' ? 'إضافة' : action === 'update' ? 'تعديل' : 'حذف'} في ${tableName}`
            })
        } catch (error) {
            console.error('Error logging audit action:', error)
        }
    }

    return { logAction }
}
