import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, MessageSquare, Clock, X, ChevronRight, Hash } from 'lucide-react';
import { format } from 'date-fns';
import { arSA } from 'date-fns/locale';
import { apiClient } from '../../api/client';

interface GlobalSearchModalProps {
    isOpen: boolean;
    onClose: () => void;
    onNavigate: (sessionId: string) => void;
}

interface SearchResult {
    sessions: Array<{
        id: string;
        title: string;
        last_message_at: string;
    }>;
    messages: Array<{
        id: string;
        content: string;
        created_at: string;
        session_id: string;
        ai_chat_sessions?: {
            title: string;
        }
    }>;
}

export const GlobalSearchModal: React.FC<GlobalSearchModalProps> = ({ isOpen, onClose, onNavigate }) => {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState<SearchResult | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    // Debounce Search
    useEffect(() => {
        if (!query.trim()) {
            setResults(null);
            return;
        }

        const timeoutId = setTimeout(async () => {
            setIsLoading(true);
            try {
                const data = await apiClient.get<SearchResult>(`/api/chat/search?q=${encodeURIComponent(query)}`);
                setResults(data);
            } catch (err) {
                console.error("Search failed", err);
            } finally {
                setIsLoading(false);
            }
        }, 500);

        return () => clearTimeout(timeoutId);
    }, [query]);

    if (!isOpen) return null;

    return (
        <AnimatePresence>
            <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-start justify-center pt-24 px-4" onClick={onClose}>
                <motion.div
                    initial={{ opacity: 0, scale: 0.95, y: -20 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95, y: -20 }}
                    onClick={e => e.stopPropagation()}
                    className="w-full max-w-2xl bg-obsidian-900 border border-gray-700 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[70vh]"
                >
                    {/* Header / Input */}
                    <div className="p-4 border-b border-gray-800 flex items-center gap-3">
                        <Search className="w-5 h-5 text-gold-500" />
                        <input
                            autoFocus
                            placeholder="ابحث في المحادثات والرسائل..."
                            className="flex-1 bg-transparent border-none outline-none text-white text-lg placeholder:text-gray-600"
                            value={query}
                            onChange={e => setQuery(e.target.value)}
                        />
                        <button onClick={onClose} className="p-1 hover:bg-gray-800 rounded-lg text-gray-400">
                            <X className="w-5 h-5" />
                        </button>
                    </div>

                    {/* Results Area */}
                    <div className="flex-1 overflow-y-auto p-2 scrollbar-thin">
                        {isLoading ? (
                            <div className="py-12 text-center text-gray-500">
                                <Search className="w-8 h-8 mx-auto mb-2 animate-pulse opacity-50" />
                                <p>جاري البحث...</p>
                            </div>
                        ) : !results && query ? (
                            <div className="py-12 text-center text-gray-500">
                                <p>لا توجد نتائج</p>
                            </div>
                        ) : results ? (
                            <div className="space-y-6 p-2">
                                {/* Session Results */}
                                {results.sessions.length > 0 && (
                                    <div>
                                        <h3 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-3 px-2 flex items-center gap-2">
                                            <Hash className="w-3 h-3" /> الجلسات
                                        </h3>
                                        <div className="space-y-1">
                                            {results.sessions.map(session => (
                                                <button
                                                    key={session.id}
                                                    onClick={() => { onNavigate(session.id); onClose(); }}
                                                    className="w-full text-right p-3 rounded-xl hover:bg-obsidian-800 flex items-center justify-between group transition-colors"
                                                >
                                                    <div className="flex items-center gap-3">
                                                        <div className="w-8 h-8 rounded-lg bg-blue-500/10 flex items-center justify-center">
                                                            <MessageSquare className="w-4 h-4 text-blue-500" />
                                                        </div>
                                                        <div>
                                                            <p className="font-bold text-gray-200 group-hover:text-gold-500 transition-colors">{session.title}</p>
                                                            <p className="text-[10px] text-gray-500">
                                                                {format(new Date(session.last_message_at), 'dd MMM yyyy', { locale: arSA })}
                                                            </p>
                                                        </div>
                                                    </div>
                                                    <ChevronRight className="w-4 h-4 text-gray-600 group-hover:text-gold-500 opacity-0 group-hover:opacity-100 transition-all" />
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Message Results */}
                                {results.messages.length > 0 && (
                                    <div>
                                        <h3 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-3 px-2 flex items-center gap-2">
                                            <MessageSquare className="w-3 h-3" /> الرسائل
                                        </h3>
                                        <div className="space-y-1">
                                            {results.messages.map(msg => (
                                                <button
                                                    key={msg.id}
                                                    onClick={() => { onNavigate(msg.session_id); onClose(); }}
                                                    className="w-full text-right p-3 rounded-xl hover:bg-obsidian-800 group transition-colors block"
                                                >
                                                    <div className="flex justify-between mb-1">
                                                        <span className="text-xs text-gold-500 font-medium">
                                                            {msg.ai_chat_sessions?.title || 'محادثة'}
                                                        </span>
                                                        <span className="text-[10px] text-gray-600">
                                                            {format(new Date(msg.created_at), 'HH:mm', { locale: arSA })}
                                                        </span>
                                                    </div>
                                                    <p className="text-sm text-gray-300 line-clamp-2 group-hover:text-white transition-colors">
                                                        {msg.content}
                                                    </p>
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="py-20 text-center text-gray-600">
                                <Search className="w-12 h-12 mx-auto mb-4 opacity-20" />
                                <p>ابحث عن قضايا، استشارات، أو رسائل سابقة...</p>
                            </div>
                        )}
                    </div>
                </motion.div>
            </div>
        </AnimatePresence>
    );
};
