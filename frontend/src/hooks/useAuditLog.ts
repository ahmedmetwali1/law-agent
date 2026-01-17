import { useAuth } from '../contexts/AuthContext'
import { supabase } from '../supabaseClient'

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
                    // مقارنة القيم مع تجاهل الأنواع المختلفة (مثل null و undefined)
                    const oldVal = oldValues[key]
                    const newVal = newValues[key]

                    // تحويل التواريخ لمقارنة صحيحة إذا لزم الأمر
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

            await supabase.from('audit_logs').insert({
                action,
                table_name: tableName,
                record_id: recordId,
                user_id: profile?.id,
                user_name: profile?.full_name,
                user_role: profile?.role,
                old_values: oldValues,
                new_values: newValues,
                changes: changes,
                lawyer_id: lawyerId,
                description: description || `${action === 'create' ? 'إضافة' : action === 'update' ? 'تعديل' : 'حذف'} في ${tableName}`
            })
        } catch (error) {
            console.error('Error logging audit action:', error)
        }
    }

    return { logAction }
}
