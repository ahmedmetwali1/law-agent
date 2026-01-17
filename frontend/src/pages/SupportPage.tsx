import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
    MessageSquare, Plus, Search, Filter, Send, Paperclip,
    MoreVertical, CheckCircle, Clock, AlertCircle, X,
    ChevronRight, ChevronLeft, User, Shield, FileText
} from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { toast } from 'sonner'
import { format } from 'date-fns'
import { arSA } from 'date-fns/locale'

// --- Interfaces ---
interface Message {
    id: string
    sender_id: string
    message: string
    is_staff: boolean
    created_at: string
    attachments: string[]
}

interface Ticket {
    id: string
    subject: string
    status: 'open' | 'pending' | 'resolved' | 'closed'
    priority: 'low' | 'normal' | 'high' | 'urgent'
    created_at: string
    updated_at: string
    last_message?: string
    messages?: Message[]
}

export function SupportPage() {
    const { user } = useAuth()
    const [tickets, setTickets] = useState<Ticket[]>([])
    const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [showNewTicketModal, setShowNewTicketModal] = useState(false)
    const [newMessage, setNewMessage] = useState('')
    const messagesEndRef = useRef<HTMLDivElement>(null)

    // Form State
    const [newTicketData, setNewTicketData] = useState({
        subject: '',
        description: '',
        priority: 'normal'
    })

    // Fetch Tickets
    const fetchTickets = async () => {
        try {
            const token = localStorage.getItem('access_token')
            const response = await fetch('http://localhost:8000/api/support/', {
                headers: { 'Authorization': `Bearer ${token}` }
            })
            if (response.ok) {
                const data = await response.json()
                setTickets(data)
            }
        } catch (error) {
            console.error(error)
        } finally {
            setIsLoading(false)
        }
    }

    // Fetch Ticket Details
    const fetchTicketDetails = async (ticketId: string) => {
        try {
            const token = localStorage.getItem('access_token')
            const response = await fetch(`http://localhost:8000/api/support/${ticketId}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            })
            if (response.ok) {
                const data = await response.json()
                setSelectedTicket(data)
                // Update in list
                setTickets(prev => prev.map(t => t.id === ticketId ? { ...t, messages: data.messages } : t))
            }
        } catch (error) {
            console.error(error)
        }
    }

    // Send Message
    const handleSendMessage = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!selectedTicket || !newMessage.trim()) return

        try {
            const token = localStorage.getItem('access_token')
            const response = await fetch(`http://localhost:8000/api/support/${selectedTicket.id}/messages`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: newMessage, attachments: [] })
            })

            if (response.ok) {
                const msg = await response.json()
                setSelectedTicket(prev => prev ? {
                    ...prev,
                    messages: [...(prev.messages || []), msg]
                } : null)
                setNewMessage('')
                fetchTickets() // Refresh list order
            }
        } catch (error) {
            toast.error('فشل إرسال الرسالة')
        }
    }

    // Create Ticket
    const handleCreateTicket = async (e: React.FormEvent) => {
        e.preventDefault()
        try {
            const token = localStorage.getItem('access_token')
            const response = await fetch('http://localhost:8000/api/support/', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(newTicketData)
            })

            if (response.ok) {
                toast.success('تم إنشاء التذكرة بنجاح')
                setShowNewTicketModal(false)
                setNewTicketData({ subject: '', description: '', priority: 'normal' })
                fetchTickets()
            }
        } catch (error) {
            toast.error('فشل إنشاء التذكرة')
        }
    }

    useEffect(() => {
        fetchTickets()
    }, [])

    useEffect(() => {
        if (selectedTicket?.messages) {
            messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
        }
    }, [selectedTicket?.messages])

    // UI Helpers
    const getStatusColor = (status: string) => {
        switch (status) {
            case 'open': return 'bg-green-500/10 text-green-500 border-green-500/20'
            case 'pending': return 'bg-orange-500/10 text-orange-500 border-orange-500/20'
            case 'resolved': return 'bg-blue-500/10 text-blue-500 border-blue-500/20'
            case 'closed': return 'bg-gray-500/10 text-gray-500 border-gray-500/20'
            default: return 'bg-gray-500/10 text-gray-500'
        }
    }

    const getPriorityColor = (priority: string) => {
        switch (priority) {
            case 'urgent': return 'text-red-500'
            case 'high': return 'text-orange-500'
            case 'normal': return 'text-blue-500'
            case 'low': return 'text-gray-400'
            default: return 'text-gray-400'
        }
    }

    const getStatusText = (status: string) => {
        const map: any = { open: 'مفتوح', pending: 'قيد الانتظار', resolved: 'تم الحل', closed: 'مغلق' }
        return map[status] || status
    }

    const [uploading, setUploading] = useState(false)
    const fileInputRef = useRef<HTMLInputElement>(null)

    // ... (fetch logic remains same)

    // Handle File Select
    const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0]
        if (!file) return

        if (file.size > 5 * 1024 * 1024) {
            toast.error('حجم الملف كبير جداً (أقصى حد 5 ميجابايت)')
            return
        }

        setUploading(true)
        const formData = new FormData()
        formData.append('file', file)

        try {
            const token = localStorage.getItem('access_token')
            const response = await fetch('http://localhost:8000/api/support/upload', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` },
                body: formData
            })

            if (response.ok) {
                const data = await response.json()
                // Send immediately as message
                await sendMessageWithAttachment(data.url, file.type)
            } else {
                toast.error('فشل رفع الملف')
            }
        } catch (error) {
            toast.error('حدث خطأ أثناء الرفع')
        } finally {
            setUploading(false)
            if (fileInputRef.current) fileInputRef.current.value = ''
        }
    }

    const sendMessageWithAttachment = async (url: string, type: string) => {
        if (!selectedTicket) return
        try {
            // Logic similar to handleSendMessage but with attachment
            const token = localStorage.getItem('access_token')
            const response = await fetch(`http://localhost:8000/api/support/${selectedTicket.id}/messages`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: "مرفق: ملف", attachments: [url] })
            })

            if (response.ok) {
                const msg = await response.json()
                setSelectedTicket(prev => prev ? { ...prev, messages: [...(prev.messages || []), msg] } : null)
                fetchTickets()
            }
        } catch (error) { console.error(error) }
    }

    return (
        <div className="flex h-[calc(100vh-8rem)] bg-obsidian-950 rounded-3xl overflow-hidden border border-gray-800 text-sm"> {/* Fill most of viewport */}
            {/* Sidebar List */}
            <div className={`${selectedTicket ? 'hidden md:flex' : 'flex'} w-full md:w-80 flex-col border-l border-gray-800 bg-obsidian-900`}> {/* Reduced width */}
                <div className="p-4 border-b border-gray-800">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-lg font-bold text-white flex items-center gap-2">
                            <Shield className="w-4 h-4 text-gold-500" />
                            الدعم الفني
                        </h2>
                        <button
                            onClick={() => setShowNewTicketModal(true)}
                            className="p-1.5 bg-gold-500 rounded-lg text-black hover:bg-gold-400 transition-colors"
                        >
                            <Plus className="w-4 h-4" />
                        </button>
                    </div>

                    <div className="relative">
                        <Search className="absolute right-3 top-2.5 w-3 h-3 text-gray-500" />
                        <input
                            type="text"
                            placeholder="بحث..."
                            className="w-full bg-obsidian-800 border border-gray-700 rounded-lg py-2 pr-9 pl-3 text-xs text-white focus:border-gold-500/50"
                        />
                    </div>
                </div>

                <div className="flex-1 overflow-y-auto p-3 space-y-2 scrollbar-thin">
                    {tickets.map(ticket => (
                        <motion.div
                            key={ticket.id}
                            onClick={() => fetchTicketDetails(ticket.id)}
                            className={`p-3 rounded-xl border cursor-pointer transition-all hover:bg-obsidian-800/50 ${selectedTicket?.id === ticket.id
                                ? 'bg-obsidian-800 border-gold-500/30'
                                : 'bg-obsidian-900/50 border-gray-800'
                                }`}
                        >
                            <div className="flex justify-between items-start mb-1">
                                <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium border ${getStatusColor(ticket.status)}`}>
                                    {getStatusText(ticket.status)}
                                </span>
                                <span className="text-[10px] text-gray-500">
                                    {format(new Date(ticket.updated_at), 'dd MMM', { locale: arSA })}
                                </span>
                            </div>
                            <h3 className="font-bold text-gray-300 mb-1 line-clamp-1 text-xs">{ticket.subject}</h3>
                            <div className={`flex items-center gap-1 text-[10px] font-medium ${getPriorityColor(ticket.priority)}`}>
                                <AlertCircle className="w-3 h-3" />
                                {ticket.priority.toUpperCase()}
                            </div>
                        </motion.div>
                    ))}
                </div>
            </div>

            {/* Chat Area */}
            <div className={`flex-1 flex flex-col bg-obsidian-950/50 ${!selectedTicket ? 'hidden md:flex' : 'flex'}`}>
                {selectedTicket ? (
                    <>
                        {/* Chat Header */}
                        <div className="bg-obsidian-900 border-b border-gray-800 p-4 flex items-center justify-between h-16 shrink-0">
                            <div className="flex items-center gap-3">
                                <button onClick={() => setSelectedTicket(null)} className="md:hidden p-1 hover:bg-white/5 rounded-lg">
                                    <ChevronRight className="w-5 h-5 text-gray-400" />
                                </button>
                                <div>
                                    <h2 className="text-base font-bold text-white flex items-center gap-2">
                                        {selectedTicket.subject}
                                        <span className={`px-2 py-0.5 text-[10px] rounded-full border ${getStatusColor(selectedTicket.status)}`}>
                                            {getStatusText(selectedTicket.status)}
                                        </span>
                                    </h2>
                                </div>
                            </div>
                        </div>

                        {/* Alert for Screenshots */}
                        <div className="bg-blue-500/5 border-b border-blue-500/10 p-2 text-center">
                            <p className="text-xs text-blue-400 flex items-center justify-center gap-2">
                                <AlertCircle className="w-3 h-3" />
                                لتسريع الحل، يرجى إرفاق صور توضح المشكلة
                            </p>
                        </div>

                        {/* Messages */}
                        <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-dots-pattern scrollbar-thin">
                            {selectedTicket.messages?.map((msg) => (
                                <div
                                    key={msg.id}
                                    className={`flex gap-3 ${msg.is_staff ? 'flex-row' : 'flex-row-reverse'}`}
                                >
                                    <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${msg.is_staff ? 'bg-blue-500/20' : 'bg-gold-500/20'
                                        }`}>
                                        {msg.is_staff ? <Shield className="w-4 h-4 text-blue-500" /> : <User className="w-4 h-4 text-gold-500" />}
                                    </div>
                                    <div className={`max-w-[75%] group`}>
                                        <div className={`flex items-center gap-2 mb-1 text-[10px] text-gray-500 ${!msg.is_staff && 'flex-row-reverse'}`}>
                                            <span>{msg.is_staff ? 'فريق الدعم' : 'أنت'}</span>
                                            <span>{format(new Date(msg.created_at), 'HH:mm', { locale: arSA })}</span>
                                        </div>
                                        <div className={`p-3 rounded-2xl text-xs ${msg.is_staff
                                            ? 'bg-obsidian-800 text-gray-200 rounded-tl-none border border-gray-700'
                                            : 'bg-gold-500 text-black rounded-tr-none shadow-lg shadow-gold-500/5'
                                            }`}>
                                            <p className="whitespace-pre-wrap leading-relaxed">
                                                {msg.message}
                                            </p>
                                            {msg.attachments && msg.attachments.length > 0 && (
                                                <div className="mt-2 space-y-2">
                                                    {msg.attachments.map((url, i) => (
                                                        <a
                                                            key={i}
                                                            href={`http://localhost:8000${url}`}
                                                            target="_blank"
                                                            rel="noopener noreferrer"
                                                            className="block p-2 bg-black/10 rounded-lg hover:bg-black/20 transition-colors flex items-center gap-2"
                                                        >
                                                            <Paperclip className="w-3 h-3" />
                                                            <span className="truncate">ملف مرفق {i + 1}</span>
                                                        </a>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            ))}
                            <div ref={messagesEndRef} />
                        </div>

                        {/* Input Area */}
                        <div className="p-4 bg-obsidian-900 border-t border-gray-800 shrink-0">
                            {selectedTicket.status === 'closed' ? (
                                <div className="text-center py-2 text-gray-500 bg-obsidian-800 rounded-xl border border-gray-700 text-xs">
                                    <AlertCircle className="w-4 h-4 mx-auto mb-1" />
                                    هذه التذكرة مغلقة
                                </div>
                            ) : (
                                <form onSubmit={handleSendMessage} className="flex gap-2 items-end">
                                    <input
                                        type="file"
                                        ref={fileInputRef}
                                        className="hidden"
                                        onChange={handleFileSelect}
                                        accept="image/*,.pdf"
                                    />
                                    <div className="flex-1 bg-obsidian-800 border border-gray-700 rounded-xl p-1 focus-within:border-gold-500/50 transition-colors relative">
                                        <textarea
                                            value={newMessage}
                                            onChange={(e) => setNewMessage(e.target.value)}
                                            placeholder="اكتب ردك هنا..."
                                            className="w-full bg-transparent border-none focus:ring-0 text-white min-h-[40px] max-h-[100px] resize-none p-2 text-xs scrollbar-thin"
                                            onKeyDown={(e) => {
                                                if (e.key === 'Enter' && !e.shiftKey) {
                                                    e.preventDefault()
                                                    handleSendMessage(e)
                                                }
                                            }}
                                        />
                                        <div className="flex justify-between items-center px-1 pb-1">
                                            <button
                                                type="button"
                                                disabled={uploading}
                                                onClick={() => fileInputRef.current?.click()}
                                                className="p-1.5 hover:bg-white/10 rounded-lg text-gray-400 hover:text-white transition-colors"
                                                title="إرفاق ملف"
                                            >
                                                {uploading ? <div className="w-4 h-4 border-2 border-gray-500 border-t-white rounded-full animate-spin" /> : <Paperclip className="w-4 h-4" />}
                                            </button>
                                        </div>
                                    </div>
                                    <button
                                        type="submit"
                                        disabled={!newMessage.trim()}
                                        className="p-3 bg-gold-500 hover:bg-gold-600 disabled:opacity-50 disabled:cursor-not-allowed text-black rounded-xl transition-all shadow-lg shadow-gold-500/20"
                                    >
                                        <Send className="w-5 h-5" />
                                    </button>
                                </form>
                            )}
                        </div>
                    </>
                ) : (
                    <div className="flex-1 flex flex-col items-center justify-center text-gray-500">
                        <div className="w-16 h-16 bg-obsidian-800 rounded-full flex items-center justify-center mb-4 animate-pulse">
                            <Shield className="w-8 h-8 opacity-50" />
                        </div>
                        <h3 className="text-lg font-bold text-white mb-1">مركز الدعم</h3>
                        <p className="text-center text-gray-400 text-xs">
                            اختر تذكرة أو أنشئ جديدة
                        </p>
                    </div>
                )}
            </div>

            {/* Modal Logic (kept roughly same but cleaner/smaller) */}
            <AnimatePresence>
                {showNewTicketModal && (
                    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.95 }}
                            className="bg-obsidian-900 border border-gold-500/20 rounded-2xl w-full max-w-md p-5 shadow-2xl"
                        >
                            <div className="flex items-center justify-between mb-4">
                                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                                    <Plus className="w-5 h-5 text-gold-500" />
                                    تذكرة جديدة
                                </h2>
                                <button onClick={() => setShowNewTicketModal(false)} className="text-gray-500 hover:text-white">
                                    <X className="w-5 h-5" />
                                </button>
                            </div>

                            <form onSubmit={handleCreateTicket} className="space-y-3">
                                <div>
                                    <label className="text-xs text-gray-400 block mb-1">الموضوع</label>
                                    <input
                                        type="text"
                                        required
                                        value={newTicketData.subject}
                                        onChange={e => setNewTicketData({ ...newTicketData, subject: e.target.value })}
                                        className="w-full bg-obsidian-800 border border-gray-700 rounded-lg p-2 text-white focus:border-gold-500/50 text-sm"
                                    />
                                </div>

                                <div>
                                    <label className="text-xs text-gray-400 block mb-1">الأهمية</label>
                                    <div className="flex gap-2">
                                        {['low', 'normal', 'high', 'urgent'].map((p) => (
                                            <button
                                                key={p}
                                                type="button"
                                                onClick={() => setNewTicketData({ ...newTicketData, priority: p })}
                                                className={`flex-1 py-1.5 rounded-lg text-xs border transition-all ${newTicketData.priority === p
                                                    ? 'bg-gold-500 text-black border-gold-500 font-bold'
                                                    : 'bg-obsidian-800 text-gray-400 border-gray-700 hover:border-gray-600'
                                                    }`}
                                            >
                                                {p === 'urgent' ? 'طارئ' : p === 'high' ? 'مهم' : p === 'normal' ? 'عادي' : 'منخفض'}
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                <div>
                                    <label className="text-xs text-gray-400 block mb-1">الوصف</label>
                                    <textarea
                                        required
                                        value={newTicketData.description}
                                        onChange={e => setNewTicketData({ ...newTicketData, description: e.target.value })}
                                        className="w-full h-24 bg-obsidian-800 border border-gray-700 rounded-lg p-2 text-white focus:border-gold-500/50 resize-none text-sm"
                                    />
                                </div>

                                <div className="pt-2 flex gap-2">
                                    <button
                                        type="button"
                                        onClick={() => setShowNewTicketModal(false)}
                                        className="flex-1 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-xl font-bold text-sm"
                                    >
                                        إلغاء
                                    </button>
                                    <button
                                        type="submit"
                                        className="flex-1 py-2 bg-gold-500 hover:bg-gold-600 text-black rounded-xl font-bold shadow-lg shadow-gold-500/10 text-sm"
                                    >
                                        إنشاء
                                    </button>
                                </div>
                            </form>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>
        </div>
    )
}
