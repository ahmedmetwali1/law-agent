import React, { useState } from 'react';
import { Plus, MessageSquare, Search, Clock, Trash2, Edit2, Check, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { apiClient } from '@/api/client';
import { toast } from 'sonner';

export interface Session {
    id: string;
    title: string;
    last_message_at: string;
}

interface ChatSidebarProps {
    sessions: Session[];
    activeSessionId?: string;
    onSelectSession: (id: string) => void;
    onNewChat: () => void;
    onRefresh: () => void;
    onDelete?: (id: string) => void;
}

export const ChatSidebar: React.FC<ChatSidebarProps> = ({
    sessions,
    activeSessionId,
    onSelectSession,
    onNewChat,
    onRefresh,
    onDelete
}) => {
    const [editingId, setEditingId] = useState<string | null>(null);
    const [editTitle, setEditTitle] = useState('');

    const handleDelete = async (e: React.MouseEvent, id: string) => {
        e.stopPropagation();
        if (!confirm('هل أنت متأكد من حذف هذه المحادثة بالكامل؟')) return;

        try {
            await apiClient.delete(`/api/chat/sessions/${id}`);
            toast.success('تم حذف المحادثة');
            if (onDelete) onDelete(id);
            else onRefresh();
        } catch (error) {
            toast.error('فشل حذف المحادثة');
        }
    };

    const startEditing = (e: React.MouseEvent, session: Session) => {
        e.stopPropagation();
        setEditingId(session.id);
        setEditTitle(session.title);
    };

    const handleRename = async (e: React.MouseEvent, id: string) => {
        e.stopPropagation();
        if (!editTitle.trim()) return;

        try {
            await apiClient.patch(`/api/chat/sessions/${id}`, { title: editTitle });
            await apiClient.patch(`/api/chat/sessions/${id}`, { title: editTitle });
            setEditingId(null);
            onRefresh();
        } catch (error) {
            toast.error('فشل تغيير الاسم');
        }
    };

    const [searchQuery, setSearchQuery] = useState('');

    // Client-side filtering for instant search
    const filteredSessions = sessions.filter(s =>
        s.title.toLowerCase().includes(searchQuery.toLowerCase())
    );

    return (
        <div className="w-80 h-full bg-obsidian-900/50 backdrop-blur-xl border-l border-gold-500/10 flex flex-col shadow-2xl z-20">

            <div className="p-4 border-b border-gold-500/10">
                <div className="flex gap-2">
                    <div className="relative flex-1 group">
                        <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 group-focus-within:text-gold-500 transition-colors" />
                        <input
                            type="text"
                            placeholder="بحث..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="w-full bg-obsidian-800/50 border border-gray-700/50 rounded-lg pr-9 pl-4 py-2 text-sm text-gray-200 focus:ring-1 focus:ring-gold-500/50 focus:border-gold-500/50 transition-all outline-none placeholder:text-gray-600"
                        />
                    </div>
                    <button
                        onClick={onNewChat}
                        className="w-10 h-10 bg-gold-500 hover:bg-gold-400 text-obsidian-950 rounded-lg flex items-center justify-center shadow-lg shadow-gold-500/10 transition-all transform hover:scale-105 active:scale-95"
                        title="محادثة جديدة"
                    >
                        <Plus className="w-5 h-5 font-bold" />
                    </button>
                </div>
            </div>

            <div className="flex-1 overflow-y-auto p-3 space-y-1 scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
                <div className="text-[10px] font-bold text-gray-500 uppercase tracking-wider px-3 mb-2 mt-2">السجل الحديث</div>

                {filteredSessions.length === 0 ? (
                    <div className="text-center py-10 text-gray-600 text-xs">لا توجد محادثات</div>
                ) : (
                    filteredSessions.map((session) => (
                        <div
                            key={session.id}
                            onClick={() => onSelectSession(session.id)}
                            className={cn(
                                "w-full text-right p-2 rounded-lg transition-all duration-200 group relative overflow-hidden flex items-center gap-2 cursor-pointer mb-0.5",
                                activeSessionId === session.id
                                    ? "bg-gradient-to-l from-gold-500/10 to-transparent border-r-2 border-gold-500 bg-white/5"
                                    : "hover:bg-white/5 border-r-2 border-transparent"
                            )}
                        >
                            <div className={cn(
                                "p-1.5 rounded-lg shrink-0 transition-colors",
                                activeSessionId === session.id ? "bg-gold-500/20 text-gold-400" : "bg-obsidian-800 text-gray-600 group-hover:text-gray-400"
                            )}>
                                <MessageSquare className="w-3.5 h-3.5" />
                            </div>

                            <div className="min-w-0 flex-1">
                                {editingId === session.id ? (
                                    <div className="flex items-center gap-1">
                                        <input
                                            autoFocus
                                            className="bg-obsidian-700 border border-gold-500/30 text-xs rounded px-1 py-0.5 w-full outline-none text-white"
                                            value={editTitle}
                                            onChange={(e) => setEditTitle(e.target.value)}
                                            onClick={(e) => e.stopPropagation()}
                                        />
                                        <button onClick={(e) => handleRename(e, session.id)} className="text-emerald-500 hover:text-emerald-400">
                                            <Check className="w-3 h-3" />
                                        </button>
                                        <button onClick={(e) => { e.stopPropagation(); setEditingId(null); }} className="text-rose-500 hover:text-rose-400">
                                            <X className="w-3 h-3" />
                                        </button>
                                    </div>
                                ) : (
                                    <>
                                        <h3 className={cn(
                                            "text-xs font-medium truncate ml-2",
                                            activeSessionId === session.id ? "text-gold-50" : "text-gray-400 group-hover:text-gray-200"
                                        )}>
                                            {session.title || "محادثة جديدة"}
                                        </h3>
                                    </>
                                )}
                            </div>

                            {/* Actions Overlay */}
                            {editingId !== session.id && (
                                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                    <button
                                        onClick={(e) => startEditing(e, session)}
                                        className="p-1 text-gray-500 hover:text-gold-400"
                                        title="تعديل الاسم"
                                    >
                                        <Edit2 className="w-3.5 h-3.5" />
                                    </button>
                                    <button
                                        onClick={(e) => handleDelete(e, session.id)}
                                        className="p-1 text-gray-500 hover:text-rose-400"
                                        title="حذف"
                                    >
                                        <Trash2 className="w-3.5 h-3.5" />
                                    </button>
                                </div>
                            )}
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};
