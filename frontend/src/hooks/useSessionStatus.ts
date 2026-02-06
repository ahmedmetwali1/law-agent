/**
 * useSessionStatus Hook
 * Real-time subscription to Agent thinking status via Supabase
 */
import { useState, useEffect } from 'react';
import { supabase } from '../supabaseClient';
import { apiClient } from '../api/client';

interface UseSessionStatusOptions {
    sessionId: string | null;
    isGenerating: boolean;
}

export function useSessionStatus({
    sessionId,
    isGenerating,
}: UseSessionStatusOptions) {
    const [currentAction, setCurrentAction] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        // Only subscribe if we have a sessionId and agent is generating
        if (!sessionId || !isGenerating) {
            setCurrentAction(null);
            return;
        }

        // Initial fetch
        const fetchStatus = async () => {
            try {
                setIsLoading(true);

                // ✅ Get session status via Backend API
                const response = await apiClient.get(`/api/chat/sessions/${sessionId}`);

                if (response.success && response.session?.current_action) {
                    setCurrentAction(response.session.current_action);
                }
            } catch (err) {
                console.error('Unexpected error fetching session status:', err);
            } finally {
                setIsLoading(false);
            }
        };

        fetchStatus();

        // ✅ Real-time subscription to session updates
        const channel = supabase
            .channel(`session-status-${sessionId}`)
            .on(
                'postgres_changes',
                {
                    event: 'UPDATE',
                    schema: 'public',
                    table: 'ai_chat_sessions',
                    filter: `id=eq.${sessionId}`,
                },
                (payload: any) => {
                    console.log('📡 Realtime update:', payload.new.current_action);
                    if (payload.new.current_action) {
                        setCurrentAction(payload.new.current_action);
                    } else {
                        setCurrentAction(null);
                    }
                }
            )
            .subscribe();

        // Cleanup
        return () => {
            console.log('🔌 Unsubscribing from session status');
            supabase.removeChannel(channel);
            setCurrentAction(null);
        };
    }, [sessionId, isGenerating]);

    return {
        currentAction,
        isLoading,
    };
}
