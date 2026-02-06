
import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
    MessageSquare, Search, Filter, Send, Paperclip,
    CheckCircle, AlertCircle, X, ChevronRight,
    User, Shield, Clock, Lock
} from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
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
    user_id: string
    users?: {
        full_name: string
        email: string
    }
    messages?: Message[]
}

export default function SupportTicketsPage() {
    const { user } = useAuth()
    const [tickets, setTickets] = useState<Ticket[]>([])
    const [filteredTickets, setFilteredTickets] = useState<Ticket[]>([])
    const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const [filterStatus, setFilterStatus] = useState<string>('all')
    const [searchQuery, setSearchQuery] = useState('')
    const [newMessage, setNewMessage] = useState('')
    const messagesEndRef = useRef<HTMLDivElement>(null)

    // Fetch Tickets
    const fetchTickets = async () => {
        setIsLoading(true)
        try {
            const token = localStorage.getItem('access_token')
            const response = await fetch('http://localhost:8000/api/support/admin/tickets', {
                headers: { 'Authorization': `Bearer ${token}` }
            })
            if (response.ok) {
                const data = await response.json()
                setTickets(data)
                setFilteredTickets(data)
            }
        } catch (error) {
            console.error(error)
            toast.error('فشل تحميل التذاكر')
        } finally {
            setIsLoading(false)
        }
    }

    // Filter Logic
    useEffect(() => {
        let res = tickets
        if (filterStatus !== 'all') {
            res = res.filter(t => t.status === filterStatus)
        }
        if (searchQuery) {
            res = res.filter(t =>
                t.subject.toLowerCase().includes(searchQuery.toLowerCase()) ||
                t.users?.full_name.toLowerCase().includes(searchQuery.toLowerCase())
            )
        }
        setFilteredTickets(res)
    }, [tickets, filterStatus, searchQuery])

    // Load Ticket Details
    const loadFullTicket = async (ticket: Ticket) => {
        try {
            const token = localStorage.getItem('access_token')
            const response = await fetch(`http://localhost:8000/api/support/admin/tickets/${ticket.id}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            })
            if (response.ok) {
                const fullData = await response.json()
                setSelectedTicket(fullData)
            } else {
                setSelectedTicket(ticket)
                toast.error("فشل تحميل تفاصيل التذكرة")
            }
        } catch (e) {
            setSelectedTicket(ticket)
        }
    }

    // Initial Load
    useEffect(() => {
        fetchTickets()
    }, [])

    // Auto-scroll chat
    useEffect(() => {
        if (selectedTicket?.messages) {
            messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
        }
    }, [selectedTicket?.messages])

    // Actions
    const handleStatusChange = async (newStatus: string) => {
        if (!selectedTicket) return
        try {
            const token = localStorage.getItem('access_token')
            const response = await fetch(`http://localhost:8000/api/support/admin/tickets/${selectedTicket.id}/status`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ status: newStatus })
            })

            if (response.ok) {
                toast.success('تم تحديث الحالة')
                // Basic Optimistic Update
                const updatedStatus = newStatus as any
                setSelectedTicket(prev => prev ? { ...prev, status: updatedStatus } : null)
                setTickets(prev => prev.map(t => t.id === selectedTicket.id ? { ...t, status: updatedStatus } : t))
            }
        } catch (error) {
            toast.error('فشل تحديث الحالة')
        }
    }

    const handleReply = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!selectedTicket || !newMessage.trim()) return

        try {
            const token = localStorage.getItem('access_token')
            const response = await fetch(`http://localhost:8000/api/support/admin/tickets/${selectedTicket.id}/reply`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: newMessage, attachments: [] })
            })

            if (response.ok) {
                const msg = await response.json()
                // Optimistically update
                setSelectedTicket(prev => prev ? {
                    ...prev,
                    messages: [...(prev.messages || []), msg],
                    status: 'resolved' // Backend usually sets resolved on admin reply
                } : null)
                setNewMessage('')
                toast.success('تم إرسال الرد')
            }
        } catch (error) {
            toast.error('فشل إرسال الرد')
        }
    }

    // Colors (Matched to Lawyer UI: Gold/Obsidian)
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
            default: return 'text-gray-400'
        }
    }

    const getStatusText = (status: string) => {
        const map: any = { open: 'مفتوح', pending: 'قيد الانتظار', resolved: 'تم الحل', closed: 'مغلق' }
        return map[status] || status
    }

    return (
        <div className="flex h-[calc(100vh-8rem)] bg-obsidian-950 rounded-3xl overflow-hidden border border-gray-800 text-sm">
            {/* Sidebar List */}
            <div className={`${selectedTicket ? 'hidden md:flex' : 'flex'} w-full md:w-80 flex-col border-l border-gray-800 bg-obsidian-900`}>
                <div className="p-4 border-b border-gray-800">
                    <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                        <Shield className="w-5 h-5 text-gold-500" />
                        إدارة التذاكر
                    </h2>

                    <div className="flex gap-2 mb-3">
                        {['all', 'open', 'resolved', 'closed'].map(s => (
                            <button
                                key={s}
                                onClick={() => setFilterStatus(s)}
                                className={`px-2 py-1.5 rounded-lg text-[10px] font-bold transition-colors ${filterStatus === s ? 'bg-gold-500 text-black' : 'bg-obsidian-800 text-gray-400 hover:bg-obsidian-700'}`}
                            >
                                {s === 'all' ? 'الكل' : getStatusText(s)}
                            </button>
                        ))}
                    </div>

                    <div className="relative">
                        <Search className="absolute right-3 top-2.5 w-3 h-3 text-gray-500" />
                        <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="بحث في التذاكر..."
                            className="w-full bg-obsidian-800 border border-gray-700 rounded-lg py-2 pr-9 pl-3 text-xs text-white focus:border-gold-500/50"
                        />
                    </div>
                </div>

                <div className="flex-1 overflow-y-auto p-2 space-y-2 scrollbar-thin">
                    {filteredTickets.map(ticket => (
                        <motion.div
                            key={ticket.id}
                            onClick={() => loadFullTicket(ticket)}
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
                            <h3 className="font-bold text-gray-200 mb-1 line-clamp-1">{ticket.subject}</h3>
                            <div className="flex items-center justify-between mt-2">
                                <div className="flex items-center gap-1 text-xs text-gray-400">
                                    <User className="w-3 h-3" />
                                    <span>{ticket.users?.full_name || 'مستخدم'}</span>
                                </div>
                                <div className={`flex items-center gap-1 text-[10px] font-medium ${getPriorityColor(ticket.priority)}`}>
                                    <AlertCircle className="w-3 h-3" />
                                    {ticket.priority.toUpperCase()}
                                </div>
                            </div>
                        </motion.div>
                    ))}

                    {filteredTickets.length === 0 && (
                        <div className="text-center py-10 text-gray-500">
                            <p>لا توجد تذاكر</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Ticket Details & Chat */}
            <div className={`flex-1 flex flex-col bg-obsidian-950/50 ${!selectedTicket ? 'hidden md:flex' : 'flex'}`}>
                {selectedTicket ? (
                    <>
                        {/* Header */}
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
                                    <p className="text-xs text-gray-400 flex items-center gap-1">
                                        صاحب التذكرة: <span className="text-gold-400">{selectedTicket.users?.full_name || 'مستخدم'}</span>
                                    </p>
                                </div>
                            </div>

                            <div className="flex items-center gap-2">
                                {selectedTicket.status !== 'closed' && (
                                    <button
                                        onClick={() => handleStatusChange('closed')}
                                        className="flex items-center gap-1 px-3 py-1.5 bg-red-500/10 text-red-500 rounded-lg border border-red-500/20 hover:bg-red-500/20 text-xs font-bold transition-all"
                                    >
                                        <Lock className="w-3 h-3" />
                                        إغلاق
                                    </button>
                                )}
                                {selectedTicket.status === 'closed' && (
                                    <button
                                        onClick={() => handleStatusChange('open')}
                                        className="flex items-center gap-1 px-3 py-1.5 bg-green-500/10 text-green-500 rounded-lg border border-green-500/20 hover:bg-green-500/20 text-xs font-bold transition-all"
                                    >
                                        <CheckCircle className="w-3 h-3" />
                                        إعادة فتح
                                    </button>
                                )}
                            </div>
                        </div>

                        {/* Chat History */}
                        <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-dots-pattern scrollbar-thin">
                            {selectedTicket.messages?.map((msg) => (
                                <div
                                    key={msg.id}
                                    className={`flex gap-3 ${msg.is_staff ? 'flex-row-reverse' : 'flex-row'}`} // Admin (staff) is right, User is left (mirrored from SupportPage logic?) 
                                // Wait, in Support Page: Me (User) is Right. Staff is Left.
                                // Here: Me (Admin/Staff) should be Right? Yes.
                                // So msg.is_staff ? flex-row-reverse (Right) : flex-row (Left).
                                >
                                    <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${msg.is_staff ? 'bg-gold-500/20' : 'bg-blue-500/20'
                                        }`}>
                                        {msg.is_staff ? <Shield className="w-4 h-4 text-gold-500" /> : <User className="w-4 h-4 text-blue-500" />}
                                    </div>
                                    <div className={`max-w-[75%] group`}>
                                        <div className={`flex items-center gap-2 mb-1 text-[10px] text-gray-500 ${msg.is_staff && 'flex-row-reverse'}`}>
                                            <span>{msg.is_staff ? 'أنت (الدعم)' : (selectedTicket.users?.full_name || 'المستخدم')}</span>
                                            <span>{format(new Date(msg.created_at), 'HH:mm', { locale: arSA })}</span>
                                        </div>
                                        <div className={`p-3 rounded-2xl text-xs ${msg.is_staff
                                            ? 'bg-gold-500 text-black rounded-tr-none shadow-lg shadow-gold-500/5' // Admin gets the Gold bubble
                                            : 'bg-obsidian-800 text-gray-200 rounded-tl-none border border-gray-700' // User gets Gray bubble
                                            }`}>
                                            <p className="whitespace-pre-wrap leading-relaxed">
                                                {msg.message}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            ))}
                            <div ref={messagesEndRef} />
                        </div>

                        {/* Reply Box */}
                        <div className="p-4 bg-obsidian-900 border-t border-gray-800 shrink-0">
                            {selectedTicket.status === 'closed' ? (
                                <div className="text-center py-2 text-gray-500 bg-obsidian-800 rounded-xl border border-gray-700 text-xs">
                                    <Lock className="w-4 h-4 mx-auto mb-1" />
                                    هذه التذكرة مغلقة
                                </div>
                            ) : (
                                <form onSubmit={handleReply} className="flex gap-2 items-end">
                                    <div className="flex-1 bg-obsidian-800 border border-gray-700 rounded-xl p-1 focus-within:border-gold-500/50 transition-colors relative">
                                        <textarea
                                            value={newMessage}
                                            onChange={(e) => setNewMessage(e.target.value)}
                                            placeholder="اكتب ردك بصفتك الدعم الفني..."
                                            className="w-full bg-transparent border-none focus:ring-0 text-white min-h-[40px] max-h-[100px] resize-none p-2 text-xs scrollbar-thin"
                                            onKeyDown={(e) => {
                                                if (e.key === 'Enter' && !e.shiftKey) {
                                                    e.preventDefault()
                                                    handleReply(e)
                                                }
                                            }}
                                        />
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
                        <h3 className="text-lg font-bold text-white mb-1">مركز مساعدة الأدمن</h3>
                        <p className="text-center text-gray-400 text-xs">
                            اختر تذكرة للرد عليها أو إدارتها
                        </p>
                    </div>
                )}
            </div>
        </div>
    )
}
