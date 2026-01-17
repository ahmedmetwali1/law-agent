import React from 'react'
import { useAuth } from '../contexts/AuthContext'

interface PermissionGuardProps {
    resource: string  // 'cases', 'clients', 'hearings', 'tasks'
    action: string    // 'read', 'create', 'update', 'delete'
    children: React.ReactNode
    fallback?: React.ReactNode
}

/**
 * Permission Guard Component
 * 
 * يستخدم للتحقق من الصلاحيات قبل عرض المحتوى
 * 
 * @example
 * // إخفاء زر الحذف للمساعدين
 * <PermissionGuard resource="cases" action="delete">
 *     <button onClick={handleDelete}>حذف القضية</button>
 * </PermissionGuard>
 * 
 * @example
 * // عرض رسالة بديلة
 * <PermissionGuard 
 *     resource="clients" 
 *     action="create"
 *     fallback={<p>غير مصرح</p>}
 * >
 *     <CreateClientButton />
 * </PermissionGuard>
 */
export function PermissionGuard({
    resource,
    action,
    children,
    fallback = null
}: PermissionGuardProps) {
    const { canPerform } = useAuth()

    // إذا لم يكن لديه الصلاحية، عرض fallback أو لا شيء
    if (!canPerform(resource, action)) {
        return <>{fallback}</>
    }

    // إذا كان لديه الصلاحية، عرض المحتوى
    return <>{children}</>
}

/**
 * Hook للتحقق من الصلاحيات
 * 
 * @example
 * const canDelete = usePermission('cases', 'delete')
 * 
 * <button disabled={!canDelete}>حذف</button>
 */
export function usePermission(resource: string, action: string): boolean {
    const { canPerform } = useAuth()
    return canPerform(resource, action)
}
