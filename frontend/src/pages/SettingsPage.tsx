import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
    User, Lock, Shield, Info, CreditCard, Sparkles, LogOut, FileWarning,
    Briefcase, FileText, Scale, Users, Gavel, Edit, Save, X, Globe, Upload, Camera
} from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { apiClient } from '../api/client'
import { supabase } from '../supabaseClient'  // ✅ For password update only (Supabase Auth API)
import { toast } from 'sonner'
import { useNavigate } from 'react-router-dom'

export function SettingsPage() {
    const { user, profile, refreshProfile, signOut } = useAuth()
    const navigate = useNavigate()
    const [activeTab, setActiveTab] = useState('profile')
    const [isEditing, setIsEditing] = useState(false)
    const [stats, setStats] = useState({
        cases: 0,
        clients: 0,
        tasks: 0,
        sessions: 0,
        police_records: 0
    })

    const [formData, setFormData] = useState({
        full_name: '',
        email: '',
        phone: '',
        license_number: '',
        specialization: '',
        bio: '',
        lawyer_license_type: '',
        bar_association: '',
        years_of_experience: 0,
        languages: [] as string[],
        website: '',
        linkedin_profile: '',
        office_address: '',
        office_city: '',
        office_postal_code: '',
        timezone: 'UTC',
        profile_image_url: ''
    })

    const [officeLawyer, setOfficeLawyer] = useState<any>(null)

    const [passwordData, setPasswordData] = useState({
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
    })

    const [showDeleteModal, setShowDeleteModal] = useState(false)
    const [deletePassword, setDeletePassword] = useState('')
    const [deleteConfirmation, setDeleteConfirmation] = useState('')
    const [isUploading, setIsUploading] = useState(false)

    const handleDeleteAccount = async () => {
        if (deleteConfirmation !== "أقر برغبتي في حذف حسابي نهائياً") return

        try {
            // ✅ Correct Axios DELETE with data
            const response = await apiClient.delete('/api/auth/account', { data: { password: deletePassword } })

            // Backend typically returns the deleted object or a success flag
            if (!response) {
                throw new Error('فشل حذف الحساب')
            }

            toast.success('تم حذف الحساب بنجاح. وداعاً!')
            signOut()
        } catch (error: any) {
            console.error('Delete account error:', error)
            toast.error(error.message || 'حدث خطأ أثناء حذف الحساب')
        }
    }

    useEffect(() => {
        if (profile) {
            setFormData({
                full_name: profile.full_name || '',
                email: user?.email || '',
                phone: profile.phone || profile.phone_number || '', // Handle mapping
                license_number: profile.license_number || '',
                specialization: profile.specialization || '',
                bio: profile.bio || '',
                lawyer_license_type: profile.lawyer_license_type || '',
                bar_association: profile.bar_association || '',
                years_of_experience: profile.years_of_experience || 0,
                languages: profile.languages || [],
                website: profile.website || '',
                linkedin_profile: profile.linkedin_profile || '',
                office_address: profile.office_address || '',
                office_city: profile.office_city || '',
                office_postal_code: profile.office_postal_code || '',
                timezone: profile.timezone || 'UTC',
                profile_image_url: profile.profile_image_url || ''
            })

            if (profile.role?.name === 'assistant' || profile.role_id === 'assistant-role-id-if-needed') {
                fetchOfficeLawyer()
            }
        }
        fetchStats()
    }, [profile, user])

    const fetchOfficeLawyer = async () => {
        try {
            const data = await apiClient.get('/api/users/office-lawyer')
            if (data) setOfficeLawyer(data)
        } catch (error) {
            console.error('Error fetching office lawyer:', error)
        }
    }

    const fetchStats = async () => {
        if (!user?.id) return

        try {
            // Fetch account statistics from Backend API
            const stats = await apiClient.get('/api/settings/account-stats')

            setStats({
                cases: stats.cases,
                clients: stats.clients,
                tasks: stats.tasks,
                sessions: stats.hearings,
                police_records: stats.police_records
            })
        } catch (error) {
            console.error('Error fetching stats:', error)
        }
    }

    const handleUpdateProfile = async (e: React.FormEvent) => {
        e.preventDefault()
        try {
            // ✅ BFF Pattern: استخدام apiClient
            await apiClient.put('/api/settings/profile', {
                full_name: formData.full_name,
                phone: formData.phone,
                license_number: formData.license_number,
                specialization: formData.specialization,
                bio: formData.bio,
                lawyer_license_type: formData.lawyer_license_type,
                bar_association: formData.bar_association,
                years_of_experience: formData.years_of_experience,
                languages: formData.languages,
                website: formData.website,
                linkedin_profile: formData.linkedin_profile,
                office_address: formData.office_address,
                office_city: formData.office_city,
                office_postal_code: formData.office_postal_code,
                timezone: formData.timezone,
                profile_image_url: formData.profile_image_url
            })

            await refreshProfile()
            setIsEditing(false)
            toast.success('تم تحديث الملف الشخصي بنجاح')
        } catch (error) {
            console.error('Error updating profile:', error)
            toast.error('فشل تحديث البيانات')
        }
    }

    const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0]
        if (!file || !user) return

        try {
            setIsUploading(true)

            // ✅ Use FormData for file upload to server
            const formData = new FormData()
            formData.append('file', file)

            // ✅ Upload to our local server endpoint
            const response = await apiClient.post('/api/settings/upload-profile-image', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            })

            if (!response || !response.publicUrl) {
                throw new Error('فشل استلام رابط الصورة من الخادم')
            }

            const publicUrl = response.publicUrl

            // Update local state
            setFormData(prev => ({ ...prev, profile_image_url: publicUrl }))

            // Auto-save the URL to profile
            await apiClient.put('/api/settings/profile', { profile_image_url: publicUrl })
            await refreshProfile()

            toast.success('تم رفع الصورة بنجاح')
        } catch (error: any) {
            console.error('Upload error:', error)
            toast.error('فشل رفع الصورة: ' + (error.response?.data?.detail || error.message))
        } finally {
            setIsUploading(false)
        }
    }

    const handleUpdatePassword = async (e: React.FormEvent) => {
        e.preventDefault()
        if (passwordData.newPassword !== passwordData.confirmPassword) {
            toast.error('كلمات المرور غير متطابقة')
            return
        }

        try {
            const { error } = await supabase.auth.updateUser({
                password: passwordData.newPassword
            })

            if (error) throw error

            toast.success('تم تغيير كلمة المرور بنجاح')
            setPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' })
        } catch (error) {
            console.error('Error changing password:', error)
            toast.error('فشل تغيير كلمة المرور')
        }
    }

    const StatCard = ({ icon: Icon, label, value, color }: any) => (
        <div className="bg-obsidian-800/50 border border-gray-700/50 rounded-xl p-4 flex items-center gap-4">
            <div className={`p-3 rounded-lg bg-${color}-500/10`}>
                <Icon className={`w-6 h-6 text-${color}-500`} />
            </div>
            <div>
                <p className="text-sm text-gray-500">{label}</p>
                <p className="text-2xl font-bold text-gray-200">{value}</p>
            </div>
        </div>
    )

    return (
        <div className="flex bg-obsidian-900 h-[calc(100vh-8rem)] rounded-3xl overflow-hidden border border-gray-800">
            {/* Sidebar Navigation */}
            <div className="w-64 bg-obsidian-800/50 border-l border-gray-800 p-6 flex flex-col gap-2">
                <h2 className="text-xl font-bold text-white mb-6 px-2">الإعدادات</h2>

                <button onClick={() => setActiveTab('profile')} className={`flex items-center gap-3 px-4 py-3 rounded-xl text-right transition-all ${activeTab === 'profile' ? 'bg-gold-500/10 text-gold-500 border border-gold-500/20' : 'text-gray-400 hover:text-white hover:bg-obsidian-700'}`}>
                    <User className="w-5 h-5" />
                    الملف الشخصي
                </button>

                <button onClick={() => setActiveTab('security')} className={`flex items-center gap-3 px-4 py-3 rounded-xl text-right transition-all ${activeTab === 'security' ? 'bg-gold-500/10 text-gold-500 border border-gold-500/20' : 'text-gray-400 hover:text-white hover:bg-obsidian-700'}`}>
                    <Lock className="w-5 h-5" />
                    الأمان وكلمة المرور
                </button>

                <button onClick={() => navigate('/subscriptions')} className="flex items-center gap-3 px-4 py-3 rounded-xl text-right text-gray-400 hover:text-white hover:bg-obsidian-700 transition-all">
                    <CreditCard className="w-5 h-5" />
                    الاشتراكات
                </button>

                <div className="my-4 border-t border-gray-800" />

                <button onClick={() => navigate('/idea')} className="flex items-center gap-3 px-4 py-3 rounded-xl text-right text-gray-400 hover:text-white hover:bg-obsidian-700 transition-all">
                    <Sparkles className="w-5 h-5" />
                    فكرة التطبيق
                </button>

                <button onClick={() => navigate('/about')} className="flex items-center gap-3 px-4 py-3 rounded-xl text-right text-gray-400 hover:text-white hover:bg-obsidian-700 transition-all">
                    <Info className="w-5 h-5" />
                    من نحن
                </button>

                <button onClick={() => navigate('/privacy')} className="flex items-center gap-3 px-4 py-3 rounded-xl text-right text-gray-400 hover:text-white hover:bg-obsidian-700 transition-all">
                    <Shield className="w-5 h-5" />
                    سياسة الخصوصية
                </button>

                {/* Logout Button Removed - User Request */}
            </div>

            {/* Main Content Area */}
            <div className="flex-1 p-8 bg-obsidian-900 overflow-y-auto">
                {activeTab === 'profile' && (
                    <div className="max-w-4xl space-y-8 animate-in fade-in duration-500">
                        {/* Hero Section */}
                        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-obsidian-800 to-obsidian-900 border border-gold-500/20 p-8 shadow-2xl">
                            <div className="absolute top-0 right-0 w-64 h-64 bg-gold-500/10 rounded-full blur-3xl -mr-32 -mt-32" />

                            <div className="relative z-10 flex flex-col md:flex-row items-center justify-between gap-6">
                                <div className="flex items-center gap-6">
                                    <div className="relative group">
                                        <div className="w-24 h-24 rounded-full bg-gradient-to-br from-gold-400 to-gold-600 p-[2px] shadow-xl overflow-hidden">
                                            <div className="w-full h-full rounded-full bg-obsidian-900 flex items-center justify-center overflow-hidden">
                                                {formData.profile_image_url ? (
                                                    <img
                                                        src={formData.profile_image_url.startsWith('/')
                                                            ? (import.meta.env.VITE_API_URL || 'http://localhost:8000') + formData.profile_image_url
                                                            : formData.profile_image_url}
                                                        alt="Profile"
                                                        className="w-full h-full object-cover transition-transform group-hover:scale-110"
                                                    />
                                                ) : (
                                                    <User className="w-10 h-10 text-gold-500" />
                                                )}
                                            </div>
                                        </div>
                                        {isEditing && (
                                            <label className="absolute inset-0 flex items-center justify-center bg-black/50 rounded-full opacity-0 group-hover:opacity-100 cursor-pointer transition-opacity">
                                                <input
                                                    type="file"
                                                    accept="image/*"
                                                    className="hidden"
                                                    onChange={handleImageUpload}
                                                    disabled={isUploading}
                                                />
                                                {isUploading ? (
                                                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white"></div>
                                                ) : (
                                                    <Camera className="w-6 h-6 text-white" />
                                                )}
                                            </label>
                                        )}
                                    </div>
                                    <div>
                                        <h2 className="text-3xl font-bold text-white mb-2 font-cairo">
                                            {profile?.full_name || 'المحامي'}
                                        </h2>
                                        <p className="text-gold-400 flex items-center gap-2">
                                            <Sparkles className="w-4 h-4" />
                                            {profile?.specialization || 'مكتب محاماة'}
                                        </p>
                                    </div>
                                </div>

                                <div className="flex gap-3">
                                    {!isEditing ? (
                                        <button
                                            onClick={() => setIsEditing(true)}
                                            className="flex items-center gap-2 px-6 py-3 bg-gold-500 hover:bg-gold-600 text-black font-bold rounded-xl transition-all shadow-lg hover:shadow-gold-500/20"
                                        >
                                            <Edit className="w-4 h-4" />
                                            تعديل الملف
                                        </button>
                                    ) : (
                                        <button
                                            onClick={() => setIsEditing(false)}
                                            className="flex items-center gap-2 px-6 py-3 bg-red-500/10 hover:bg-red-500/20 text-red-500 border border-red-500/20 rounded-xl transition-all"
                                        >
                                            <X className="w-4 h-4" />
                                            إلغاء
                                        </button>
                                    )}
                                </div>
                            </div>

                            {/* Stats Grid */}
                            <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mt-8 pt-8 border-t border-gray-700/50">
                                <div className="text-center">
                                    <p className="text-2xl font-bold text-white">{stats.cases}</p>
                                    <p className="text-xs text-gray-400 mt-1">القضايا</p>
                                </div>
                                <div className="text-center border-r border-gray-700/50">
                                    <p className="text-2xl font-bold text-white">{stats.clients}</p>
                                    <p className="text-xs text-gray-400 mt-1">الموكلين</p>
                                </div>
                                <div className="text-center border-r border-gray-700/50">
                                    <p className="text-2xl font-bold text-white">{stats.sessions}</p>
                                    <p className="text-xs text-gray-400 mt-1">الجلسات</p>
                                </div>
                                <div className="text-center border-r border-gray-700/50">
                                    <p className="text-2xl font-bold text-white">{stats.police_records}</p>
                                    <p className="text-xs text-gray-400 mt-1">المحاضر</p>
                                </div>
                                <div className="text-center border-r border-gray-700/50">
                                    <p className="text-2xl font-bold text-white">{stats.tasks}</p>
                                    <p className="text-xs text-gray-400 mt-1">المهام</p>
                                </div>
                            </div>
                        </div>

                        {/* Full Profile Form */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="space-y-8"
                        >
                            {/* Assistant Banner */}
                            {officeLawyer && (
                                <div className="bg-cobalt-500/10 border border-cobalt-500/30 rounded-2xl p-6 flex items-center gap-4 animate-in fade-in slide-in-from-top-4">
                                    <div className="w-12 h-12 rounded-full bg-cobalt-500 flex items-center justify-center">
                                        <Users className="w-6 h-6 text-white" />
                                    </div>
                                    <div>
                                        <p className="text-gray-400 text-sm font-cairo">أنت مسجل كمساعد قانوني للمحامي:</p>
                                        <p className="text-xl font-bold text-white font-cairo">{officeLawyer.full_name}</p>
                                    </div>
                                </div>
                            )}

                            <div className="grid md:grid-cols-2 gap-8">
                                {/* Personal Info */}
                                <div className="space-y-6">
                                    <h3 className="text-xl font-bold text-white flex items-center gap-2 mb-4">
                                        <Info className="w-5 h-5 text-blue-500" />
                                        المعلومات الشخصية والاتصال
                                    </h3>
                                    <div className="glass-card p-6 space-y-4">
                                        <div>
                                            <label className="text-sm text-gray-400 block mb-2">الاسم الكامل</label>
                                            <div className="relative">
                                                <User className="absolute right-3 top-3 w-5 h-5 text-gray-500" />
                                                <input
                                                    disabled={!isEditing}
                                                    type="text"
                                                    value={formData.full_name}
                                                    onChange={e => setFormData({ ...formData, full_name: e.target.value })}
                                                    className="w-full bg-obsidian-900/50 border border-gray-700 rounded-xl py-3 pr-10 pl-4 text-white focus:border-gold-500/50 disabled:opacity-50 transition-all font-cairo"
                                                />
                                            </div>
                                        </div>
                                        <div>
                                            <label className="text-sm text-gray-400 block mb-2">البريد الإلكتروني</label>
                                            <div className="relative">
                                                <div className="absolute right-3 top-3 w-5 h-5 text-gray-500 text-center leading-tight">@</div>
                                                <input
                                                    disabled={true}
                                                    type="email"
                                                    value={formData.email}
                                                    className="w-full bg-obsidian-900/50 border border-gray-800 rounded-xl py-3 pr-10 pl-4 text-gray-400 cursor-not-allowed"
                                                />
                                            </div>
                                        </div>
                                        <div>
                                            <label className="text-sm text-gray-400 block mb-2">رقم الهاتف</label>
                                            <div className="relative">
                                                <Briefcase className="absolute right-3 top-3 w-5 h-5 text-gray-500" />
                                                <input
                                                    disabled={!isEditing}
                                                    type="text"
                                                    value={formData.phone}
                                                    onChange={e => setFormData({ ...formData, phone: e.target.value })}
                                                    className="w-full bg-obsidian-900/50 border border-gray-700 rounded-xl py-3 pr-10 pl-4 text-white focus:border-gold-500/50 disabled:opacity-50 transition-all"
                                                    dir="ltr"
                                                    placeholder="+966..."
                                                />
                                            </div>
                                        </div>
                                        <div>
                                            <label className="text-sm text-gray-400 block mb-2">الصورة الشخصية</label>
                                            <div className="flex gap-2">
                                                <div className="relative flex-1">
                                                    <Camera className="absolute right-3 top-3 w-5 h-5 text-gray-500" />
                                                    <input
                                                        disabled={!isEditing}
                                                        type="text"
                                                        value={formData.profile_image_url}
                                                        onChange={e => setFormData({ ...formData, profile_image_url: e.target.value })}
                                                        className="w-full bg-obsidian-900/50 border border-gray-700 rounded-xl py-3 pr-10 pl-4 text-white focus:border-gold-500/50 disabled:opacity-50 transition-all text-sm"
                                                        placeholder="رابط الصورة (URL)..."
                                                        dir="ltr"
                                                    />
                                                </div>
                                                <label className={`px-4 py-3 bg-obsidian-800 border border-gray-700 rounded-xl cursor-pointer hover:bg-obsidian-700 transition-colors flex items-center gap-2 ${!isEditing ? 'opacity-50 cursor-not-allowed' : ''}`}>
                                                    <input
                                                        disabled={!isEditing || isUploading}
                                                        type="file"
                                                        accept="image/*"
                                                        className="hidden"
                                                        onChange={handleImageUpload}
                                                    />
                                                    {isUploading ? (
                                                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gold-500"></div>
                                                    ) : (
                                                        <Upload className="w-4 h-4 text-gold-500" />
                                                    )}
                                                    <span className="text-xs text-white whitespace-nowrap">رفع ملف</span>
                                                </label>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* Professional Info */}
                                <div className="space-y-6">
                                    <h3 className="text-xl font-bold text-white flex items-center gap-2 mb-4">
                                        <Briefcase className="w-5 h-5 text-gold-500" />
                                        المعلومات المهنية والتراخيص
                                    </h3>
                                    <div className="glass-card p-6 space-y-4">
                                        <div className="grid grid-cols-2 gap-4">
                                            <div>
                                                <label className="text-sm text-gray-400 block mb-2">رقم الترخيص</label>
                                                <input
                                                    disabled={!isEditing}
                                                    type="text"
                                                    value={formData.license_number}
                                                    onChange={e => setFormData({ ...formData, license_number: e.target.value })}
                                                    className="w-full bg-obsidian-900/50 border border-gray-700 rounded-xl py-3 px-4 text-white focus:border-gold-500/50 disabled:opacity-50 transition-all font-mono"
                                                />
                                            </div>
                                            <div>
                                                <label className="text-sm text-gray-400 block mb-2">سنوات الخبرة</label>
                                                <input
                                                    disabled={!isEditing}
                                                    type="number"
                                                    value={formData.years_of_experience}
                                                    onChange={e => setFormData({ ...formData, years_of_experience: parseInt(e.target.value) || 0 })}
                                                    className="w-full bg-obsidian-900/50 border border-gray-700 rounded-xl py-3 px-4 text-white focus:border-gold-500/50 disabled:opacity-50 transition-all"
                                                />
                                            </div>
                                        </div>
                                        <div>
                                            <label className="text-sm text-gray-400 block mb-2">درجة الترخيص</label>
                                            <input
                                                disabled={!isEditing}
                                                type="text"
                                                value={formData.lawyer_license_type}
                                                onChange={e => setFormData({ ...formData, lawyer_license_type: e.target.value })}
                                                className="w-full bg-obsidian-900/50 border border-gray-700 rounded-xl py-3 px-4 text-white focus:border-gold-500/50 disabled:opacity-50 transition-all font-cairo"
                                                placeholder="مثال: ممارس، نقض، إلخ..."
                                            />
                                        </div>
                                        <div>
                                            <label className="text-sm text-gray-400 block mb-2">النقابة / الهيئة المهنية</label>
                                            <input
                                                disabled={!isEditing}
                                                type="text"
                                                value={formData.bar_association}
                                                onChange={e => setFormData({ ...formData, bar_association: e.target.value })}
                                                className="w-full bg-obsidian-900/50 border border-gray-700 rounded-xl py-3 px-4 text-white focus:border-gold-500/50 disabled:opacity-50 transition-all font-cairo"
                                                placeholder="مثال: الهيئة السعودية للمحامين"
                                            />
                                        </div>
                                        <div>
                                            <label className="text-sm text-gray-400 block mb-2">التخصص الرئيسي</label>
                                            <input
                                                disabled={!isEditing}
                                                type="text"
                                                value={formData.specialization}
                                                onChange={e => setFormData({ ...formData, specialization: e.target.value })}
                                                className="w-full bg-obsidian-900/50 border border-gray-700 rounded-xl py-3 px-4 text-white focus:border-gold-500/50 disabled:opacity-50 transition-all font-cairo"
                                            />
                                        </div>
                                    </div>
                                </div>

                                {/* Office & Location */}
                                <div className="space-y-6">
                                    <h3 className="text-xl font-bold text-white flex items-center gap-2 mb-4">
                                        <Gavel className="w-5 h-5 text-emerald-500" />
                                        معلومات المكتب والموقع
                                    </h3>
                                    <div className="glass-card p-6 space-y-4">
                                        <div>
                                            <label className="text-sm text-gray-400 block mb-2">عنوان المكتب</label>
                                            <input
                                                disabled={!isEditing}
                                                type="text"
                                                value={formData.office_address}
                                                onChange={e => setFormData({ ...formData, office_address: e.target.value })}
                                                className="w-full bg-obsidian-900/50 border border-gray-700 rounded-xl py-3 px-4 text-white focus:border-gold-500/50 disabled:opacity-50 transition-all font-cairo"
                                                placeholder="الشارع، الحي..."
                                            />
                                        </div>
                                        <div className="grid grid-cols-2 gap-4">
                                            <div>
                                                <label className="text-sm text-gray-400 block mb-2">المدينة</label>
                                                <input
                                                    disabled={!isEditing}
                                                    type="text"
                                                    value={formData.office_city}
                                                    onChange={e => setFormData({ ...formData, office_city: e.target.value })}
                                                    className="w-full bg-obsidian-900/50 border border-gray-700 rounded-xl py-3 px-4 text-white focus:border-gold-500/50 disabled:opacity-50 transition-all font-cairo"
                                                />
                                            </div>
                                            <div>
                                                <label className="text-sm text-gray-400 block mb-2">الرمز البريدي</label>
                                                <input
                                                    disabled={!isEditing}
                                                    type="text"
                                                    value={formData.office_postal_code}
                                                    onChange={e => setFormData({ ...formData, office_postal_code: e.target.value })}
                                                    className="w-full bg-obsidian-900/50 border border-gray-700 rounded-xl py-3 px-4 text-white focus:border-gold-500/50 disabled:opacity-50 transition-all"
                                                />
                                            </div>
                                        </div>
                                        <div>
                                            <label className="text-sm text-gray-400 block mb-2">المنطقة الزمنية</label>
                                            <select
                                                disabled={!isEditing}
                                                value={formData.timezone}
                                                onChange={e => setFormData({ ...formData, timezone: e.target.value })}
                                                className="w-full bg-obsidian-900/50 border border-gray-700 rounded-xl py-3 px-4 text-white focus:border-gold-500/50 disabled:opacity-50 transition-all"
                                            >
                                                <option value="Asia/Riyadh">Asia/Riyadh (GMT+3)</option>
                                                <option value="Asia/Dubai">Asia/Dubai (GMT+4)</option>
                                                <option value="Africa/Cairo">Africa/Cairo (GMT+2)</option>
                                                <option value="UTC">UTC</option>
                                            </select>
                                        </div>
                                    </div>
                                </div>

                                {/* Online Presence & Bio */}
                                <div className="space-y-6">
                                    <h3 className="text-xl font-bold text-white flex items-center gap-2 mb-4">
                                        <Globe className="w-5 h-5 text-cobalt-400" />
                                        الحضور الرقمي والنبذة
                                    </h3>
                                    <div className="glass-card p-6 space-y-4">
                                        <div>
                                            <label className="text-sm text-gray-400 block mb-2">الموقع الإلكتروني</label>
                                            <input
                                                disabled={!isEditing}
                                                type="url"
                                                value={formData.website}
                                                onChange={e => setFormData({ ...formData, website: e.target.value })}
                                                className="w-full bg-obsidian-900/50 border border-gray-700 rounded-xl py-3 px-4 text-white focus:border-gold-500/50 disabled:opacity-50 transition-all text-sm"
                                                placeholder="https://..."
                                                dir="ltr"
                                            />
                                        </div>
                                        <div>
                                            <label className="text-sm text-gray-400 block mb-2">LinkedIn</label>
                                            <input
                                                disabled={!isEditing}
                                                type="url"
                                                value={formData.linkedin_profile}
                                                onChange={e => setFormData({ ...formData, linkedin_profile: e.target.value })}
                                                className="w-full bg-obsidian-900/50 border border-gray-700 rounded-xl py-3 px-4 text-white focus:border-gold-500/50 disabled:opacity-50 transition-all text-sm"
                                                placeholder="https://linkedin.com/in/..."
                                                dir="ltr"
                                            />
                                        </div>
                                        <div>
                                            <label className="text-sm text-gray-400 block mb-2">نبذة تعريفية</label>
                                            <textarea
                                                disabled={!isEditing}
                                                value={formData.bio}
                                                onChange={e => setFormData({ ...formData, bio: e.target.value })}
                                                rows={4}
                                                className="w-full bg-obsidian-900/50 border border-gray-700 rounded-xl py-3 px-4 text-white focus:border-gold-500/50 disabled:opacity-50 transition-all font-cairo resize-none"
                                                placeholder="اكتب نبذة عن خبراتك ومجالات عملك..."
                                            />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </motion.div>

                        {isEditing && (
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="flex justify-end pt-4 border-t border-gray-800"
                            >
                                <button
                                    onClick={handleUpdateProfile}
                                    className="flex items-center gap-2 bg-gold-500 hover:bg-gold-600 text-black font-bold px-10 py-4 rounded-xl transition-all shadow-lg shadow-gold-500/10 hover:shadow-gold-500/30"
                                >
                                    <Save className="w-5 h-5" />
                                    حفظ التغييرات
                                </button>
                            </motion.div>
                        )}
                    </div>
                )}

                {activeTab === 'security' && (
                    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="max-w-2xl">
                        <h1 className="text-3xl font-bold text-white mb-8">الأمان وكلمة المرور</h1>
                        <div className="glass-card p-8">
                            <form onSubmit={handleUpdatePassword} className="space-y-6">
                                <div>
                                    <label className="text-sm text-gray-400 block mb-2">كلمة المرور الجديدة</label>
                                    <input
                                        type="password"
                                        required
                                        value={passwordData.newPassword}
                                        onChange={e => setPasswordData({ ...passwordData, newPassword: e.target.value })}
                                        className="w-full bg-obsidian-800 border border-gray-700 rounded-xl p-3 text-white focus:border-gold-500/50"
                                    />
                                </div>
                                <div>
                                    <label className="text-sm text-gray-400 block mb-2">تأكيد كلمة المرور</label>
                                    <input
                                        type="password"
                                        required
                                        value={passwordData.confirmPassword}
                                        onChange={e => setPasswordData({ ...passwordData, confirmPassword: e.target.value })}
                                        className="w-full bg-obsidian-800 border border-gray-700 rounded-xl p-3 text-white focus:border-gold-500/50"
                                    />
                                </div>
                                <div className="pt-4">
                                    <button type="submit" className="w-full bg-obsidian-700 hover:bg-obsidian-600 text-white font-bold px-8 py-3 rounded-xl transition-all border border-gray-600">
                                        تحديث كلمة المرور
                                    </button>
                                </div>
                            </form>
                        </div>

                        {/* Danger Zone */}
                        <div className="mt-12 border-t border-red-500/20 pt-8">
                            <h3 className="text-xl font-bold text-red-500 flex items-center gap-2 mb-4">
                                <FileWarning className="w-5 h-5" />
                                منطقة الخطر
                            </h3>
                            <div className="bg-red-500/5 border border-red-500/20 rounded-xl p-6 flex items-center justify-between">
                                <div>
                                    <h4 className="font-bold text-white mb-2">حذف الحساب نهائياً</h4>
                                    <p className="text-gray-400 text-sm">
                                        سيتم حذف جميع بياناتك، قضاياك، موكليك، ومستنداتك بشكل نهائي. لا يمكن التراجع عن هذا الإجراء.
                                    </p>
                                </div>
                                <button
                                    onClick={() => setShowDeleteModal(true)}
                                    className="px-6 py-3 bg-red-500 hover:bg-red-600 text-white font-bold rounded-xl transition-all shadow-lg hover:shadow-red-500/20"
                                >
                                    حذف الحساب
                                </button>
                            </div>
                        </div>

                        {/* Delete Account Modal */}
                        <AnimatePresence>
                            {showDeleteModal && (
                                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
                                    <motion.div
                                        initial={{ opacity: 0, scale: 0.9 }}
                                        animate={{ opacity: 1, scale: 1 }}
                                        exit={{ opacity: 0, scale: 0.9 }}
                                        className="bg-obsidian-900 border border-red-500/30 rounded-2xl w-full max-w-lg p-8 shadow-2xl relative"
                                    >
                                        <button
                                            onClick={() => setShowDeleteModal(false)}
                                            className="absolute top-4 right-4 text-gray-500 hover:text-white"
                                        >
                                            <X className="w-6 h-6" />
                                        </button>

                                        <div className="text-center mb-8">
                                            <div className="w-20 h-20 bg-red-500/10 rounded-full flex items-center justify-center mx-auto mb-4 border border-red-500/20">
                                                <Shield className="w-10 h-10 text-red-500" />
                                            </div>
                                            <h2 className="text-2xl font-bold text-white mb-2">هل أنت متأكد من حذف الحساب؟</h2>
                                            <p className="text-gray-400">
                                                هذا الإجراء <span className="text-red-500 font-bold">نهائي ولا يمكن التراجع عنه</span>. سيتم مسح جميع البيانات المرتبطة بحسابك فوراً.
                                            </p>
                                        </div>

                                        <div className="space-y-6">
                                            {/* Step 1: Password */}
                                            <div>
                                                <label className="text-sm text-gray-400 block mb-2">أدخل كلمة المرور للمتابعة</label>
                                                <input
                                                    type="password"
                                                    value={deletePassword}
                                                    onChange={e => setDeletePassword(e.target.value)}
                                                    className="w-full bg-obsidian-800 border border-gray-700 rounded-xl p-3 text-white focus:border-red-500/50"
                                                    placeholder="كلمة المرور الحالية..."
                                                />
                                            </div>

                                            {/* Step 2: Confirmation Text */}
                                            {deletePassword.length > 3 && (
                                                <div className="animate-in fade-in slide-in-from-top-4">
                                                    <label className="text-sm text-gray-400 block mb-2">
                                                        اكتب العبارة التالية للتأكيد: <span className="text-red-400 select-all">أقر برغبتي في حذف حسابي نهائياً</span>
                                                    </label>
                                                    <input
                                                        type="text"
                                                        value={deleteConfirmation}
                                                        onChange={e => setDeleteConfirmation(e.target.value)}
                                                        className="w-full bg-obsidian-800 border border-gray-700 rounded-xl p-3 text-white focus:border-red-500/50"
                                                        placeholder="اكتب العبارة هنا..."
                                                    />
                                                </div>
                                            )}

                                            <div className="flex gap-3 pt-4">
                                                <button
                                                    onClick={() => setShowDeleteModal(false)}
                                                    className="flex-1 px-4 py-3 bg-gray-800 hover:bg-gray-700 text-white rounded-xl font-bold transition-all"
                                                >
                                                    إلغاء
                                                </button>
                                                <button
                                                    onClick={handleDeleteAccount}
                                                    disabled={deleteConfirmation !== "أقر برغبتي في حذف حسابي نهائياً" || !deletePassword}
                                                    className="flex-1 px-4 py-3 bg-red-600 hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-xl font-bold transition-all shadow-lg shadow-red-600/20"
                                                >
                                                    حذف حسابي الآن
                                                </button>
                                            </div>
                                        </div>
                                    </motion.div>
                                </div>
                            )}
                        </AnimatePresence>
                    </motion.div>
                )}

            </div >
        </div >
    )
}
