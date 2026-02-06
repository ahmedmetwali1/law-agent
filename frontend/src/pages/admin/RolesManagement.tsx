import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
    UserCog,
    Plus,
    Edit3,
    Trash2,
    Shield,
    Save,
    Eye,
    FileText,
    Settings,
    Users,
    Briefcase,
    Calendar,
    CheckSquare
} from 'lucide-react';
import { getAllRoles, createRole, updateRole, deleteRole, Role, RolePermissions } from '../../api/admin';
import { toast } from 'sonner';

// Module permissions type for each module
type ModulePermissions = {
    read: boolean;
    create: boolean;
    update: boolean;
    delete: boolean;
};

const modulesList = [
    { key: 'users', label: 'المستخدمين', icon: Users },
    { key: 'cases', label: 'القضايا', icon: Briefcase },
    { key: 'clients', label: 'الموكلين', icon: Users },
    { key: 'hearings', label: 'الجلسات', icon: Calendar },
    { key: 'tasks', label: 'المهام', icon: CheckSquare },
    { key: 'documents', label: 'المستندات', icon: FileText },
    { key: 'settings', label: 'الإعدادات', icon: Settings },
];

const permissionActions: (keyof ModulePermissions)[] = ['read', 'create', 'update', 'delete'];

export default function RolesManagement() {
    const [roles, setRoles] = useState<Role[]>([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [editingRole, setEditingRole] = useState<Role | null>(null);
    const [formData, setFormData] = useState<{
        name: string;
        name_ar: string;
        description: string;
        permissions: Record<string, ModulePermissions>;
        is_active: boolean;
        is_default: boolean;
    }>({
        name: '',
        name_ar: '',
        description: '',
        permissions: {},
        is_active: true,
        is_default: false
    });


    useEffect(() => {
        loadRoles();
    }, []);

    const loadRoles = async () => {
        try {
            setLoading(true);
            const data = await getAllRoles();
            setRoles(data);
        } catch (error) {
            console.error('Error loading roles:', error);
            toast.error('فشل تحميل الأدوار');
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async () => {
        if (!formData.name || !formData.name_ar) {
            toast.error('يرجى ملء اسم الدور بالعربي والإنجليزي');
            return;
        }

        try {
            if (editingRole) {
                await updateRole(editingRole.id, formData);
                toast.success('تم تحديث الدور');
            } else {
                await createRole(formData);
                toast.success('تم إنشاء الدور');
            }
            setShowModal(false);
            resetForm();
            loadRoles();
        } catch (error) {
            console.error('Error saving role:', error);
            toast.error('فشل حفظ الدور');
        }
    };

    const handleDelete = async (role: Role) => {
        if (role.is_default) {
            toast.error('لا يمكن حذف الدور الافتراضي');
            return;
        }
        if (!confirm('هل أنت متأكد من حذف هذا الدور؟')) return;

        try {
            await deleteRole(role.id);
            toast.success('تم حذف الدور');
            loadRoles();
        } catch (error) {
            console.error('Error deleting role:', error);
            toast.error('فشل حذف الدور');
        }
    };

    const handleEdit = (role: Role) => {
        setEditingRole(role);
        setFormData({
            name: role.name,
            name_ar: role.name_ar || '',
            description: role.description || '',
            permissions: role.permissions || {},
            is_active: role.is_active,
            is_default: role.is_default
        });
        setShowModal(true);
    };

    const resetForm = () => {
        setEditingRole(null);
        setFormData({
            name: '',
            name_ar: '',
            description: '',
            permissions: {},
            is_active: true,
            is_default: false
        });
    };

    const openCreateModal = () => {
        resetForm();
        setShowModal(true);
    };

    const togglePermission = (module: string, action: string) => {
        setFormData(prev => {
            const modulePerms = prev.permissions[module] || { read: false, create: false, update: false, delete: false };
            return {
                ...prev,
                permissions: {
                    ...prev.permissions,
                    [module]: {
                        ...modulePerms,
                        [action]: !modulePerms[action as keyof typeof modulePerms]
                    }
                }
            };
        });
    };

    const selectAllForModule = (module: string, value: boolean) => {
        setFormData(prev => ({
            ...prev,
            permissions: {
                ...prev.permissions,
                [module]: {
                    read: value,
                    create: value,
                    update: value,
                    delete: value
                }
            }
        }));
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[60vh]">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto"></div>
                    <p className="text-gray-400 mt-4" style={{ fontFamily: 'Cairo, sans-serif' }}>جاري التحميل...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-purple-500 flex items-center gap-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        <UserCog className="w-7 h-7" />
                        إدارة الأدوار والصلاحيات
                    </h1>
                    <p className="text-gray-400 mt-1" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        إجمالي: {roles.length} أدوار
                    </p>
                </div>
                <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={openCreateModal}
                    className="flex items-center gap-2 px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-all"
                    style={{ fontFamily: 'Cairo, sans-serif' }}
                >
                    <Plus className="w-5 h-5" />
                    دور جديد
                </motion.button>
            </div>

            {/* Roles Grid */}
            {roles.length === 0 ? (
                <div className="text-center py-12 backdrop-blur-xl bg-obsidian-800/50 border border-purple-500/20 rounded-xl">
                    <UserCog className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                    <h3 className="text-xl font-bold text-gray-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        لا يوجد أدوار
                    </h3>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {roles.map((role, index) => (
                        <motion.div
                            key={role.id}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: index * 0.05 }}
                            className="backdrop-blur-xl bg-obsidian-800/70 border border-purple-500/20 rounded-xl p-6 hover:border-purple-500/50 transition-all"
                        >
                            <div className="flex items-start justify-between mb-4">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center">
                                        <Shield className="w-5 h-5 text-purple-400" />
                                    </div>
                                    <div>
                                        <h3 className="text-lg font-bold text-white" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                            {role.name_ar || role.name}
                                        </h3>
                                        <p className="text-sm text-gray-500">{role.name}</p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-1">
                                    {!role.is_default && (
                                        <>
                                            <button
                                                onClick={() => handleEdit(role)}
                                                className="p-2 text-gray-400 hover:text-purple-400 hover:bg-purple-500/10 rounded-lg transition-all"
                                            >
                                                <Edit3 className="w-4 h-4" />
                                            </button>
                                            <button
                                                onClick={() => handleDelete(role)}
                                                className="p-2 text-gray-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-all"
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                        </>
                                    )}
                                </div>
                            </div>

                            <div className="flex flex-wrap gap-2 mb-3">
                                {role.is_active ? (
                                    <span className="px-2 py-1 bg-green-500/20 text-green-400 rounded-full text-xs" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                        نشط
                                    </span>
                                ) : (
                                    <span className="px-2 py-1 bg-red-500/20 text-red-400 rounded-full text-xs" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                        غير نشط
                                    </span>
                                )}
                                {role.is_default && (
                                    <span className="px-2 py-1 bg-blue-500/20 text-blue-400 rounded-full text-xs" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                        افتراضي
                                    </span>
                                )}
                            </div>

                            {role.description && (
                                <p className="text-sm text-gray-400 mb-3 line-clamp-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                    {role.description}
                                </p>
                            )}

                            <div className="flex flex-wrap gap-1">
                                {Object.keys(role.permissions || {}).slice(0, 4).map(key => (
                                    <span key={key} className="px-2 py-0.5 bg-purple-500/10 text-purple-400 rounded text-xs">
                                        {key}
                                    </span>
                                ))}
                                {Object.keys(role.permissions || {}).length > 4 && (
                                    <span className="px-2 py-0.5 bg-gray-500/20 text-gray-400 rounded text-xs">
                                        +{Object.keys(role.permissions || {}).length - 4}
                                    </span>
                                )}
                            </div>
                        </motion.div>
                    ))}
                </div>
            )}

            {/* Create/Edit Modal */}
            {showModal && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="backdrop-blur-xl bg-obsidian-800/95 border border-purple-500/20 rounded-2xl p-8 max-w-4xl w-full max-h-[90vh] overflow-y-auto"
                    >
                        <h2 className="text-2xl font-bold text-purple-500 mb-6" style={{ fontFamily: 'Cairo, sans-serif' }}>
                            {editingRole ? 'تعديل الدور' : 'دور جديد'}
                        </h2>

                        <div className="space-y-6">
                            {/* Basic Info */}
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-purple-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                        اسم الدور (English) <span className="text-red-400">*</span>
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.name}
                                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                        className="w-full px-4 py-3 bg-obsidian-900/50 border border-purple-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors"
                                        placeholder="lawyer"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-purple-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                        اسم الدور (عربي) <span className="text-red-400">*</span>
                                    </label>
                                    <input
                                        type="text"
                                        value={formData.name_ar}
                                        onChange={(e) => setFormData({ ...formData, name_ar: e.target.value })}
                                        className="w-full px-4 py-3 bg-obsidian-900/50 border border-purple-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors"
                                        style={{ fontFamily: 'Cairo, sans-serif' }}
                                        placeholder="محامي"
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-purple-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                    الوصف
                                </label>
                                <textarea
                                    value={formData.description}
                                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                    rows={2}
                                    className="w-full px-4 py-3 bg-obsidian-900/50 border border-purple-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors resize-none"
                                    style={{ fontFamily: 'Cairo, sans-serif' }}
                                    placeholder="وصف مختصر للدور..."
                                />
                            </div>

                            {/* Permissions Matrix */}
                            <div>
                                <label className="block text-sm font-medium text-purple-400 mb-4" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                    الصلاحيات
                                </label>
                                <div className="overflow-x-auto">
                                    <table className="w-full">
                                        <thead>
                                            <tr className="border-b border-purple-500/20">
                                                <th className="text-right py-3 px-4 text-gray-400 font-medium" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                                    الوحدة
                                                </th>
                                                <th className="py-3 px-4 text-green-400 text-center text-sm">قراءة</th>
                                                <th className="py-3 px-4 text-blue-400 text-center text-sm">إنشاء</th>
                                                <th className="py-3 px-4 text-yellow-400 text-center text-sm">تحديث</th>
                                                <th className="py-3 px-4 text-red-400 text-center text-sm">حذف</th>
                                                <th className="py-3 px-4 text-purple-400 text-center text-sm">الكل</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {modulesList.map(module => {
                                                const Icon = module.icon;
                                                const perms = formData.permissions[module.key] || {};
                                                const allChecked = perms.read && perms.create && perms.update && perms.delete;

                                                return (
                                                    <tr key={module.key} className="border-b border-purple-500/10 hover:bg-obsidian-900/30">
                                                        <td className="py-3 px-4">
                                                            <div className="flex items-center gap-2">
                                                                <Icon className="w-4 h-4 text-gray-400" />
                                                                <span className="text-white" style={{ fontFamily: 'Cairo, sans-serif' }}>{module.label}</span>
                                                            </div>
                                                        </td>
                                                        {permissionActions.map(action => (
                                                            <td key={action} className="py-3 px-4 text-center">
                                                                <input
                                                                    type="checkbox"
                                                                    checked={perms[action as keyof typeof perms] || false}
                                                                    onChange={() => togglePermission(module.key, action)}
                                                                    className="w-5 h-5 rounded border-purple-500/30 bg-obsidian-900/50 text-purple-500 focus:ring-purple-500 cursor-pointer"
                                                                />
                                                            </td>
                                                        ))}
                                                        <td className="py-3 px-4 text-center">
                                                            <input
                                                                type="checkbox"
                                                                checked={allChecked}
                                                                onChange={(e) => selectAllForModule(module.key, e.target.checked)}
                                                                className="w-5 h-5 rounded border-purple-500/30 bg-obsidian-900/50 text-purple-500 focus:ring-purple-500 cursor-pointer"
                                                            />
                                                        </td>
                                                    </tr>
                                                );
                                            })}
                                        </tbody>
                                    </table>
                                </div>
                            </div>

                            {/* Status */}
                            <div className="flex items-center gap-6">
                                <label className="flex items-center gap-2 cursor-pointer">
                                    <input
                                        type="checkbox"
                                        checked={formData.is_active}
                                        onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                                        className="w-5 h-5 rounded border-purple-500/30 bg-obsidian-900/50 text-purple-500 focus:ring-purple-500"
                                    />
                                    <span className="text-sm text-gray-300" style={{ fontFamily: 'Cairo, sans-serif' }}>نشط</span>
                                </label>
                            </div>

                            {/* Actions */}
                            <div className="flex gap-3 pt-4">
                                <motion.button
                                    whileHover={{ scale: 1.02 }}
                                    whileTap={{ scale: 0.98 }}
                                    onClick={handleSubmit}
                                    className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-all"
                                    style={{ fontFamily: 'Cairo, sans-serif' }}
                                >
                                    <Save className="w-5 h-5" />
                                    {editingRole ? 'حفظ التعديلات' : 'إنشاء الدور'}
                                </motion.button>
                                <button
                                    onClick={() => setShowModal(false)}
                                    className="px-6 py-3 bg-obsidian-700 text-white rounded-lg hover:bg-obsidian-600 transition-colors"
                                    style={{ fontFamily: 'Cairo, sans-serif' }}
                                >
                                    إلغاء
                                </button>
                            </div>
                        </div>
                    </motion.div>
                </div>
            )}
        </div>
    );
}
