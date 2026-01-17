import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { toast } from 'sonner'
import { supabase, isConfigured } from '../supabaseClient'
import { AuthLayout } from '../components/auth/AuthLayout'
import { Eye, EyeOff, Loader2, CheckCircle2, Globe } from 'lucide-react'

interface Country {
    id: string
    name_ar: string
    name_en: string
    code: string
    phone_prefix: string
    flag_emoji: string
}

export function SignupPage() {
    const navigate = useNavigate()
    const [loading, setLoading] = useState(false)
    const [showPassword, setShowPassword] = useState(false)
    const [showConfirmPassword, setShowConfirmPassword] = useState(false)
    const [countries, setCountries] = useState<Country[]>([])
    const [loadingCountries, setLoadingCountries] = useState(true)

    const [formData, setFormData] = useState({
        fullName: '',
        email: '',
        password: '',
        confirmPassword: '',
        phone: '',
        country_id: '',
        specialization: '',
        license_number: '',
        bio: ''
    })

    const [errors, setErrors] = useState({
        fullName: '',
        email: '',
        password: '',
        confirmPassword: '',
        country_id: ''
    })

    // Fetch countries on mount
    useEffect(() => {
        fetchCountries()
    }, [])

    const fetchCountries = async () => {
        try {
            setLoadingCountries(true)
            const { data, error } = await supabase
                .from('countries')
                .select('*')
                .eq('is_active', true)
                .order('name_ar')

            if (error) throw error

            setCountries(data || [])

            // Auto-select Saudi Arabia if available
            const saudi = data?.find(c => c.code === 'SA')
            if (saudi) {
                setFormData(prev => ({ ...prev, country_id: saudi.id }))
            }
        } catch (error) {
            console.error('Error fetching countries:', error)
            toast.error('فشل تحميل قائمة الدول')
        } finally {
            setLoadingCountries(false)
        }
    }

    // Password strength calculation
    const getPasswordStrength = (password: string) => {
        let strength = 0
        if (password.length >= 8) strength++
        if (/[a-z]/.test(password)) strength++
        if (/[A-Z]/.test(password)) strength++
        if (/[0-9]/.test(password)) strength++
        if (/[^a-zA-Z0-9]/.test(password)) strength++
        return strength
    }

    const passwordStrength = getPasswordStrength(formData.password)
    const strengthColors = ['', 'bg-red-500', 'bg-orange-500', 'bg-yellow-500', 'bg-lime-500', 'bg-green-500']
    const strengthLabels = ['', 'ضعيف جداً', 'ضعيف', 'متوسط', 'جيد', 'قوي']

    // Validation
    const validate = () => {
        const newErrors = {
            fullName: '',
            email: '',
            password: '',
            confirmPassword: '',
            country_id: ''
        }

        if (!formData.fullName.trim()) {
            newErrors.fullName = 'الاسم الكامل مطلوب'
        }

        if (!formData.email.trim()) {
            newErrors.email = 'البريد الإلكتروني مطلوب'
        } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
            newErrors.email = 'البريد الإلكتروني غير صحيح'
        }

        if (!formData.password) {
            newErrors.password = 'كلمة المرور مطلوبة'
        } else if (formData.password.length < 8) {
            newErrors.password = 'كلمة المرور يجب أن تكون 8 أحرف على الأقل'
        }

        if (!formData.confirmPassword) {
            newErrors.confirmPassword = 'تأكيد كلمة المرور مطلوب'
        } else if (formData.password !== formData.confirmPassword) {
            newErrors.confirmPassword = 'كلمة المرور غير متطابقة'
        }

        if (!formData.country_id) {
            newErrors.country_id = 'الدولة مطلوبة'
        }

        setErrors(newErrors)
        return Object.values(newErrors).every(error => !error)
    }

    const handleSignup = async (e: React.FormEvent) => {
        e.preventDefault()

        if (!isConfigured) {
            toast.error('خطأ في الإعدادات', {
                description: 'لم يتم ربط التطبيق بقاعدة البيانات. يرجى ضبط ملف .env'
            })
            return
        }

        if (!validate()) return

        setLoading(true)


        try {
            // Call backend signup API
            const response = await fetch('http://localhost:8000/api/auth/signup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: formData.email,
                    password: formData.password,
                    full_name: formData.fullName,
                    phone: formData.phone || null,
                    country_id: formData.country_id || null,
                    specialization: formData.specialization || null,
                    license_number: formData.license_number || null,
                    bio: formData.bio || null
                })
            })

            const data = await response.json()

            if (!response.ok) {
                throw new Error(data.detail || 'فشل إنشاء الحساب')
            }

            // Save token to localStorage
            localStorage.setItem('access_token', data.access_token)
            localStorage.setItem('user', JSON.stringify(data.user))

            // Success
            toast.success('تم إنشاء الحساب بنجاح! 🎉', {
                description: 'مرحباً بك في النظام القانوني الذكي'
            })

            // Auto-redirect to dashboard
            setTimeout(() => {
                navigate('/dashboard')
            }, 1500)

        } catch (error: any) {
            console.error('Signup error:', error)
            toast.error('فشل إنشاء الحساب', {
                description: error.message || 'حدث خطأ غير متوقع'
            })
        } finally {
            setLoading(false)
        }
    }

    return (
        <AuthLayout
            title="إنشاء حساب جديد"
            subtitle="انضم إلى النظام القانوني الذكي"
        >
            <form onSubmit={handleSignup} className="space-y-5">
                {/* Full Name */}
                <div>
                    <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        الاسم الكامل
                    </label>
                    <input
                        type="text"
                        value={formData.fullName}
                        onChange={(e) => setFormData({ ...formData, fullName: e.target.value })}
                        className="w-full px-4 py-3 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold-500 transition-colors"
                        style={{ fontFamily: 'Cairo, sans-serif' }}
                        placeholder="أدخل اسمك الكامل"
                        disabled={loading}
                    />
                    {errors.fullName && (
                        <p className="mt-1 text-xs text-red-400" style={{ fontFamily: 'Cairo, sans-serif' }}>{errors.fullName}</p>
                    )}
                </div>

                {/* Email */}
                <div>
                    <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        البريد الإلكتروني
                    </label>
                    <input
                        type="email"
                        value={formData.email}
                        onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                        className="w-full px-4 py-3 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold-500 transition-colors"
                        style={{ fontFamily: 'Cairo, sans-serif' }}
                        placeholder="example@law.com"
                        disabled={loading}
                    />
                    {errors.email && (
                        <p className="mt-1 text-xs text-red-400" style={{ fontFamily: 'Cairo, sans-serif' }}>{errors.email}</p>
                    )}
                </div>

                {/* Country Selection */}
                <div>
                    <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        الدولة <span className="text-red-400">*</span>
                    </label>
                    <div className="relative">
                        <Globe className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                        <select
                            value={formData.country_id}
                            onChange={(e) => setFormData({ ...formData, country_id: e.target.value })}
                            className="w-full px-4 py-3 pr-12 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white focus:outline-none focus:border-gold-500 transition-colors appearance-none"
                            style={{ fontFamily: 'Cairo, sans-serif' }}
                            disabled={loading || loadingCountries}
                        >
                            <option value="">اختر الدولة...</option>
                            {countries.map(country => (
                                <option key={country.id} value={country.id}>
                                    {country.flag_emoji} {country.name_ar}
                                </option>
                            ))}
                        </select>
                    </div>
                    {errors.country_id && (
                        <p className="mt-1 text-xs text-red-400" style={{ fontFamily: 'Cairo, sans-serif' }}>{errors.country_id}</p>
                    )}
                </div>

                {/* Phone Number */}
                <div>
                    <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        رقم الجوال (اختياري)
                    </label>
                    <input
                        type="tel"
                        value={formData.phone}
                        onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                        className="w-full px-4 py-3 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold-500 transition-colors"
                        style={{ fontFamily: 'Cairo, sans-serif' }}
                        placeholder="+966 5XXXXXXXX"
                        disabled={loading}
                    />
                </div>

                {/* Password */}
                <div>
                    <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        كلمة المرور
                    </label>
                    <div className="relative">
                        <input
                            type={showPassword ? 'text' : 'password'}
                            value={formData.password}
                            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                            className="w-full px-4 py-3 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold-500 transition-colors"
                            style={{ fontFamily: 'Cairo, sans-serif' }}
                            placeholder="••••••••"
                            disabled={loading}
                        />
                        <button
                            type="button"
                            onClick={() => setShowPassword(!showPassword)}
                            className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gold-500 transition-colors"
                        >
                            {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                        </button>
                    </div>
                    {errors.password && (
                        <p className="mt-1 text-xs text-red-400" style={{ fontFamily: 'Cairo, sans-serif' }}>{errors.password}</p>
                    )}

                    {/* Password Strength Indicator */}
                    {formData.password && (
                        <div className="mt-2">
                            <div className="flex gap-1 mb-1">
                                {[1, 2, 3, 4, 5].map((level) => (
                                    <div
                                        key={level}
                                        className={`h-1 flex-1 rounded-full transition-colors ${level <= passwordStrength ? strengthColors[passwordStrength] : 'bg-gray-700'
                                            }`}
                                    />
                                ))}
                            </div>
                            <p className="text-xs text-gray-400" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                قوة كلمة المرور: {strengthLabels[passwordStrength]}
                            </p>
                        </div>
                    )}
                </div>

                {/* Confirm Password */}
                <div>
                    <label className="block text-sm font-medium text-gold-500 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        تأكيد كلمة المرور
                    </label>
                    <div className="relative">
                        <input
                            type={showConfirmPassword ? 'text' : 'password'}
                            value={formData.confirmPassword}
                            onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                            className="w-full px-4 py-3 bg-obsidian-900/50 border border-gold-500/20 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold-500 transition-colors"
                            style={{ fontFamily: 'Cairo, sans-serif' }}
                            placeholder="••••••••"
                            disabled={loading}
                        />
                        <button
                            type="button"
                            onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                            className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gold-500 transition-colors"
                        >
                            {showConfirmPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                        </button>
                    </div>
                    {errors.confirmPassword && (
                        <p className="mt-1 text-xs text-red-400" style={{ fontFamily: 'Cairo, sans-serif' }}>{errors.confirmPassword}</p>
                    )}
                    {formData.confirmPassword && formData.password === formData.confirmPassword && (
                        <div className="mt-1 flex items-center gap-1 text-green-400">
                            <CheckCircle2 className="w-3 h-3" />
                            <span className="text-xs" style={{ fontFamily: 'Cairo, sans-serif' }}>كلمة المرور متطابقة</span>
                        </div>
                    )}
                </div>

                {/* Optional Professional Information */}
                <div className="pt-4 border-t border-gold-500/10">
                    <p className="text-sm text-gray-400 mb-4" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        معلومات مهنية (اختيارية - يمكن إضافتها لاحقاً)
                    </p>

                    <div className="space-y-4">
                        {/* Specialization */}
                        <div>
                            <label className="block text-sm font-medium text-gray-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                التخصص القانوني
                            </label>
                            <input
                                type="text"
                                value={formData.specialization}
                                onChange={(e) => setFormData({ ...formData, specialization: e.target.value })}
                                className="w-full px-4 py-2.5 bg-obsidian-900/50 border border-gold-500/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold-500/50 transition-colors text-sm"
                                style={{ fontFamily: 'Cairo, sans-serif' }}
                                placeholder="مثال: قضايا مدنية وتجارية"
                                disabled={loading}
                            />
                        </div>

                        {/* License Number */}
                        <div>
                            <label className="block text-sm font-medium text-gray-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                رقم الترخيص
                            </label>
                            <input
                                type="text"
                                value={formData.license_number}
                                onChange={(e) => setFormData({ ...formData, license_number: e.target.value })}
                                className="w-full px-4 py-2.5 bg-obsidian-900/50 border border-gold-500/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold-500/50 transition-colors text-sm"
                                style={{ fontFamily: 'Cairo, sans-serif' }}
                                placeholder="رقم الترخيص من الهيئة"
                                disabled={loading}
                            />
                        </div>

                        {/* Bio */}
                        <div>
                            <label className="block text-sm font-medium text-gray-400 mb-2" style={{ fontFamily: 'Cairo, sans-serif' }}>
                                نبذة مختصرة
                            </label>
                            <textarea
                                value={formData.bio}
                                onChange={(e) => setFormData({ ...formData, bio: e.target.value })}
                                rows={3}
                                className="w-full px-4 py-2.5 bg-obsidian-900/50 border border-gold-500/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-gold-500/50 transition-colors resize-none text-sm"
                                style={{ fontFamily: 'Cairo, sans-serif' }}
                                placeholder="نبذة مختصرة عنك وخبراتك..."
                                disabled={loading}
                            />
                        </div>
                    </div>
                </div>

                {/* Submit Button */}
                <motion.button
                    whileHover={{ scale: loading ? 1 : 1.02 }}
                    whileTap={{ scale: loading ? 1 : 0.98 }}
                    type="submit"
                    disabled={loading}
                    className="w-full py-3 bg-gradient-to-r from-gold-600 to-gold-500 text-obsidian-900 font-bold rounded-lg hover:from-gold-500 hover:to-gold-400 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    style={{ fontFamily: 'Cairo, sans-serif' }}
                >
                    {loading ? (
                        <>
                            <Loader2 className="w-5 h-5 animate-spin" />
                            <span>جاري إنشاء الحساب...</span>
                        </>
                    ) : (
                        <span>إنشاء حساب</span>
                    )}
                </motion.button>

                {/* Login Link */}
                <div className="text-center pt-4 border-t border-gold-500/10">
                    <p className="text-gray-400 text-sm" style={{ fontFamily: 'Cairo, sans-serif' }}>
                        لديك حساب بالفعل؟{' '}
                        <Link
                            to="/login"
                            className="text-gold-500 hover:text-gold-400 font-medium transition-colors"
                        >
                            تسجيل الدخول
                        </Link>
                    </p>
                </div>
            </form>
        </AuthLayout>
    )
}
