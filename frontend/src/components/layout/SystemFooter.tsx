import { useEffect, useState } from 'react'

export function SystemFooter() {
    const [latency, setLatency] = useState(0)
    const [dbStatus, setDbStatus] = useState<'connected' | 'disconnected'>('connected')

    useEffect(() => {
        // Ping check every 5 seconds
        const checkHealth = async () => {
            try {
                const start = Date.now()
                const response = await fetch('http://localhost:8000/api/health', {
                    method: 'GET',
                    signal: AbortSignal.timeout(3000),
                })

                if (response.ok) {
                    setLatency(Date.now() - start)
                    setDbStatus('connected')
                } else {
                    setDbStatus('disconnected')
                }
            } catch (error) {
                setDbStatus('disconnected')
                setLatency(0)
            }
        }

        checkHealth()
        const interval = setInterval(checkHealth, 5000)

        return () => clearInterval(interval)
    }, [])

    return (
        <footer className="fixed bottom-0 left-0 right-0 h-8 glass-dark border-t border-gold-500/10 z-50">
            <div className="flex items-center justify-between h-full px-6 text-xs">
                {/* Right - System Status */}
                <div className="flex items-center gap-4 text-gray-400">
                    <div className="flex items-center gap-2">
                        <span
                            className={`w-2 h-2 rounded-full ${dbStatus === 'connected' ? 'bg-success' : 'bg-error'
                                } animate-pulse`}
                        />
                        <span>
                            {dbStatus === 'connected' ? 'النظام يعمل' : 'فقد الاتصال'}
                        </span>
                    </div>

                    <span className="text-gray-600">•</span>

                    <div className="flex items-center gap-1">
                        <span className="text-cobalt-400">⚡</span>
                        <span>
                            {dbStatus === 'connected'
                                ? 'قاعدة البيانات متصلة'
                                : 'قاعدة البيانات غير متصلة'}
                        </span>
                    </div>
                </div>

                {/* Center - Copyright */}
                <span className="text-gray-500">
                    © 2026 Legal AI System - v2.0.0
                </span>

                {/* Left - Latency */}
                <div className="flex items-center gap-2 text-gray-400">
                    <span className="text-gray-600">Latency:</span>
                    <span
                        className={
                            latency === 0
                                ? 'text-error'
                                : latency < 50
                                    ? 'text-success'
                                    : latency < 100
                                        ? 'text-warning'
                                        : 'text-error'
                        }
                    >
                        {latency > 0 ? `${latency}ms` : '---'}
                    </span>
                </div>
            </div>
        </footer>
    )
}
