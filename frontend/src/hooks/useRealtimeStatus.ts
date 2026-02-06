import { useState, useEffect } from 'react';
import { apiClient } from '../api/client';

export interface ExecutionLog {
    id: string;
    status: 'pending' | 'running' | 'success' | 'error';
    message: string;
    tool?: string;
    timestamp?: number;
}

export const useRealtimeStatus = (sessionId: string | null, isWaiting: boolean) => {
    const [status, setStatus] = useState<string | null>(null);
    const [executionLogs, setExecutionLogs] = useState<ExecutionLog[]>([]);

    useEffect(() => {
        if (!sessionId || !isWaiting) {
            setStatus(null);
            setExecutionLogs([]);
            return;
        }

        const interval = setInterval(async () => {
            try {
                // Fetch full session including execution_logs
                const session = await apiClient.get<any>(`/api/chat/sessions/${sessionId}`);

                if (session.current_action) {
                    setStatus(session.current_action);
                } else {
                    setStatus(null);
                }

                if (session.execution_logs && Array.isArray(session.execution_logs)) {
                    setExecutionLogs(session.execution_logs);
                }
            } catch (e) {
                // Ignore errors during polling
            }
        }, 1000);

        return () => clearInterval(interval);
    }, [sessionId, isWaiting]);

    return { status, executionLogs };
};
