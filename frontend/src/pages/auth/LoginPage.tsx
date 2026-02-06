import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Scale, Mail, Lock, LogIn } from 'lucide-react'
import { toast } from 'sonner'
import { useAuth } from '../../contexts/AuthContext'

export function LoginPage() {
    const navigate = useNavigate()
    const { user, refreshProfile, loading } = useAuth()
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [isLoading, setIsLoading] = useState(false)

    // Redirect if already logged in
    useEffect(() => {
        if (!loading && user) {
            navigate('/dashboard', { replace: true })
        }
    }, [user, loading, navigate])

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault()

        if (!email || !password) {
            toast.error('يرجى إدخال البريد الإلكتروني وكلمة المرور')
            return
        }

        setIsLoading(true)

        try {
            const response = await fetch('http://localhost:8000/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password })
            })

            const data = await response.json()

            if (!response.ok) {
                throw new Error(data.detail || 'فشل تسجيل الدخول')
            }

            // Save token and user data
            localStorage.setItem('access_token', data.access_token)
            localStorage.setItem('user', JSON.stringify(data.user))

            // Trigger profile refresh in AuthContext
            await refreshProfile()

            toast.success('مرحباً بعودتك!')

            // Small delay to ensure AuthContext updates
            setTimeout(() => {
                navigate('/dashboard')
            }, 100)
        } catch (error: any) {
            toast.error('فشل تسجيل الدخول', {
                description: error.message || 'البريد الإلكتروني أو كلمة المرور غير صحيحة'
            })
            console.error('Login error:', error)
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <div className="min-h-screen bg-obsidian-900 flex items-center justify-center p-6 relative overflow-hidden">
            {/* Background Decorative Elements */}
            <div className="absolute inset-0 opacity-5">
                <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-cobalt-600 rounded-full blur-3xl" />
                <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-gold-500 rounded-full blur-3xl" />
            </div>

            {/* Abstract Law Scales Pattern */}
            <div className="absolute inset-0 opacity-3">
                <Scale className="absolute top-20 left-20 w-32 h-32 text-gold-500/10" />
                <Scale className="absolute bottom-20 right-20 w-24 h-24 text-gold-500/10" />
            </div>

            {/* Login Card */}
            <div className="relative w-full max-w-md">
                {/* Logo/Brand */}
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br from-cobalt-600 to-cobalt-500 mb-4 ring-4 ring-gold-500/20">
                        <Scale className="w-10 h-10 text-white" />
                    </div>
                    <h1 className="text-3xl font-bold text-white mb-2">نظام المحاماة الذكي</h1>
                    <p className="text-gray-400">منصة إدارة المكاتب القانونية</p>
                </div>

                {/* Card */}
                <div className="glass-dark rounded-2xl p-8 border-2 border-gold-500/20 shadow-2xl">
                    <h2 className="text-2xl font-bold text-gold-500 mb-6 text-center">تسجيل الدخول</h2>

                    <form onSubmit={handleLogin} className="space-y-5">
                        {/* Email Input */}
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">
                                البريد الإلكتروني
                            </label>
                            <div className="relative">
                                <Mail className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                                <input
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    placeholder="lawyer@example.com"
                                    className="input-modern pr-12"
                                    disabled={isLoading}
                                />
                            </div>
                        </div>

                        {/* Password Input */}
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">
                                كلمة المرور
                            </label>
                            <div className="relative">
                                <Lock className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    placeholder="••••••••"
                                    className="input-modern pr-12"
                                    disabled={isLoading}
                                />
                            </div>
                        </div>

                        {/* Forgot Password */}
                        <div className="text-left">
                            <a href="#" className="text-sm text-cobalt-400 hover:text-cobalt-300 transition">
                                نسيت كلمة المرور؟
                            </a>
                        </div>

                        {/* Submit Button */}
                        <button
                            type="submit"
                            disabled={isLoading}
                            className="w-full btn-primary py-3 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {isLoading ? (
                                <>
                                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                    <span>جاري التحقق...</span>
                                </>
                            ) : (
                                <>
                                    <LogIn className="w-5 h-5" />
                                    <span>دخول</span>
                                </>
                            )}
                        </button>
                    </form>

                    {/* Sign Up Link */}
                    <div className="mt-6 text-center">
                        <p className="text-gray-400">
                            لا تملك حساباً?{' '}
                            <Link to="/signup" className="text-gold-500 hover:text-gold-400 font-medium transition">
                                سجّل الآن
                            </Link>
                        </p>
                    </div>
                </div>

                {/* Footer */}
                <p className="text-center text-gray-500 text-sm mt-6">
                    © 2026 Legal AI System - جميع الحقوق محفوظة
                </p>
            </div>
        </div>
    )
}
