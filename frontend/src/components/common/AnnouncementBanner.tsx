import React, { useEffect, useState } from 'react';
import { apiClient } from '../../api/client';
import { AlertCircle, X, Info, AlertTriangle, CheckCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface Announcement {
    id: string;
    title: string;
    content: string;
    announcement_type: 'info' | 'warning' | 'critical' | 'feature';
    is_dismissible: boolean;
    start_date?: string;
    end_date?: string;
}

export const AnnouncementBanner: React.FC = () => {
    const [announcements, setAnnouncements] = useState<Announcement[]>([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [isVisible, setIsVisible] = useState(true);

    useEffect(() => {
        const fetchAnnouncements = async () => {
            try {
                // Fetch from notifications endpoint which filters active ones for current user
                const data = await apiClient.get<Announcement[]>('/api/notifications/announcements');

                // Filter out dismissed announcements from localStorage
                const dismissedIds = JSON.parse(localStorage.getItem('dismissed_announcements') || '[]');
                const active = data.filter((a: Announcement) => !dismissedIds.includes(a.id));
                setAnnouncements(active);
            } catch (error) {
                console.error('Failed to fetch announcements', error);
            }
        };

        fetchAnnouncements();
    }, []);

    if (announcements.length === 0 || !isVisible) return null;

    const currentAnnouncement = announcements[currentIndex];

    const handleDismiss = () => {
        if (currentAnnouncement.is_dismissible) {
            const dismissedIds = JSON.parse(localStorage.getItem('dismissed_announcements') || '[]');
            localStorage.setItem('dismissed_announcements', JSON.stringify([...dismissedIds, currentAnnouncement.id]));
        }

        // Remove from current view
        const remaining = announcements.filter(a => a.id !== currentAnnouncement.id);
        setAnnouncements(remaining);

        if (remaining.length === 0) {
            setIsVisible(false);
        } else {
            setCurrentIndex(prev => (prev >= remaining.length ? 0 : prev));
        }
    };

    const nextAnnouncement = () => {
        setCurrentIndex((prev) => (prev + 1) % announcements.length);
    };

    const getIcon = (type: string) => {
        switch (type) {
            case 'warning': return <AlertTriangle className="w-5 h-5 text-yellow-400" />;
            case 'critical': return <AlertCircle className="w-5 h-5 text-red-400" />;
            case 'feature': return <CheckCircle className="w-5 h-5 text-green-400" />;
            default: return <Info className="w-5 h-5 text-blue-400" />;
        }
    };

    const getColors = (type: string) => {
        switch (type) {
            case 'warning': return 'bg-yellow-900/40 border-yellow-500/30 text-yellow-100';
            case 'critical': return 'bg-red-900/40 border-red-500/30 text-red-100';
            case 'feature': return 'bg-green-900/40 border-green-500/30 text-green-100';
            default: return 'bg-blue-900/40 border-blue-500/30 text-blue-100';
        }
    };

    return (
        <AnimatePresence>
            {isVisible && (
                <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className={`w-full border-b backdrop-blur-md overflow-hidden relative ${getColors(currentAnnouncement.announcement_type)}`}
                >
                    <div className="container mx-auto px-4 py-2 flex items-center justify-between gap-4 h-12">
                        <div className="flex items-center gap-3 shrink-0 z-10 bg-inherit pr-2">
                            <span className="mt-0.5">{getIcon(currentAnnouncement.announcement_type)}</span>
                            <span className="font-bold text-sm whitespace-nowrap">{currentAnnouncement.title}:</span>
                        </div>

                        {/* Marquee Content */}
                        <div className="flex-1 overflow-hidden relative h-full flex items-center group">
                            <div className="animate-marquee whitespace-nowrap text-sm font-medium hover:[animation-play-state:paused]">
                                <span>{currentAnnouncement.content}</span>
                            </div>
                        </div>

                        <div className="flex items-center gap-2 shrink-0 z-10 bg-inherit pl-2">
                            {announcements.length > 1 && (
                                <button
                                    onClick={nextAnnouncement}
                                    className="text-xs underline hover:text-white px-2"
                                >
                                    التالي ({currentIndex + 1}/{announcements.length})
                                </button>
                            )}

                            {currentAnnouncement.is_dismissible && (
                                <button
                                    onClick={handleDismiss}
                                    className="p-1 hover:bg-white/10 rounded-full transition-colors"
                                >
                                    <X className="w-4 h-4" />
                                </button>
                            )}
                        </div>
                    </div>
                </motion.div>
            )}
        </AnimatePresence>
    );
};
