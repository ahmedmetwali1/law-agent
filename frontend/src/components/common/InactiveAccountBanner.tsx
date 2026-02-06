import { useState, useEffect } from 'react'
import { AlertCircle, Phone, MessageCircle } from 'lucide-react'
import { apiClient } from '../../api/client'

export function InactiveAccountBanner() {
    const [contactInfo, setContactInfo] = useState({
        contact_phone: '',
        contact_whatsapp: ''
    })

    useEffect(() => {
        const fetchSettings = async () => {
            try {
                const settings = await apiClient.get('/api/settings/public-settings')
                setContactInfo({
                    contact_phone: settings.contact_phone || '+966XXXXXXXX',
                    contact_whatsapp: settings.contact_whatsapp || '+966XXXXXXXX'
                })
            } catch (error) {
                console.error('Failed to fetch contact info:', error)
            }
        }
        fetchSettings()
    }, [])

    return (
        <div className="bg-red-500/10 border border-red-500/20 rounded-2xl p-6 mb-6">
            <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-full bg-red-500/20 flex items-center justify-center shrink-0">
                    <AlertCircle className="w-6 h-6 text-red-500" />
                </div>
                <div className="flex-1">
                    <h3 className="text-xl font-bold text-white mb-2 font-cairo text-right">الحساب متوقف حالياً</h3>
                    <p className="text-gray-400 mb-6 font-cairo text-right">
                        عذراً، يبدو أن حسابك غير نشط حالياً. يرجى التواصل مع الإدارة لتفعيل الحساب أو للاستفسار عن السبب.
                    </p>

                    <div className="flex flex-wrap gap-4 justify-end">
                        <a
                            href={`tel:${contactInfo.contact_phone}`}
                            className="flex items-center gap-2 bg-obsidian-800 hover:bg-obsidian-700 text-white px-4 py-2 rounded-xl border border-gray-700 transition-colors"
                        >
                            <Phone className="w-4 h-4 text-gold-500" />
                            <span className="font-cairo">{contactInfo.contact_phone}</span>
                        </a>
                        <a
                            href={`https://wa.me/${contactInfo.contact_whatsapp.replace('+', '')}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-2 bg-green-500/10 hover:bg-green-500/20 text-green-500 px-4 py-2 rounded-xl border border-green-500/20 transition-colors"
                        >
                            <MessageCircle className="w-4 h-4" />
                            <span className="font-cairo">واتساب الإدارة</span>
                        </a>
                    </div>
                </div>
            </div>
        </div>
    )
}
