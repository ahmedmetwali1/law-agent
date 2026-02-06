import { useState, useEffect, useRef, useCallback } from 'react';
import { toast } from 'sonner';

export interface AgentEvent {
    type: 'THOUGHT' | 'QUESTION' | 'FINAL_ANSWER' | 'ERROR' | 'STATUS_UPDATE';
    content: string;
    step?: number;
    metadata?: any;
    timestamp: number;
}

export const useAgentEvents = (clientId: string) => {
    const [status, setStatus] = useState<string | null>(null);
    const [thoughtLogs, setThoughtLogs] = useState<any[]>([]);
    const [pendingQuestion, setPendingQuestion] = useState<string | null>(null);
    const [isConnected, setIsConnected] = useState(false);

    // Store logs in ref to avoid dependency loops in effect
    const logsRef = useRef<any[]>([]);

    const wsRef = useRef<WebSocket | null>(null);

    const connect = useCallback(() => {
        if (!clientId) return;
        if (wsRef.current?.readyState === WebSocket.OPEN) return;

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = import.meta.env.VITE_API_URL
            ? import.meta.env.VITE_API_URL.replace('http', 'ws')
            : `${protocol}//${window.location.host}`;

        // Use full URL logic
        const wsUrl = `${host.includes('localhost') ? 'ws://localhost:8000' : host}/ws/${clientId}`;

        console.log('🔌 Connecting to WebSocket:', wsUrl);
        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            console.log('✅ WebSocket Connected');
            setIsConnected(true);
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                handleEvent(data);
            } catch (e) {
                console.error('WS Parse Error:', e);
            }
        };

        ws.onclose = () => {
            console.log('❌ WebSocket Disconnected');
            setIsConnected(false);
            // Reconnect logic could go here
            setTimeout(connect, 3000);
        };

        ws.onerror = (err) => {
            console.error('WS Error:', err);
        };

        wsRef.current = ws;
    }, [clientId]);

    useEffect(() => {
        connect();
        return () => {
            wsRef.current?.close();
        };
    }, [connect]);

    const handleEvent = (event: AgentEvent) => {
        const timestamp = Date.now();

        switch (event.type) {
            case 'STATUS_UPDATE':
                // ✅ Exclusive for the "Thinking..." header/bubble
                console.log('🔵 Status Update:', event.content);
                setStatus(event.content);
                break;

            case 'THOUGHT':
                // ✅ Exclusive for the detailed log stream
                // Do NOT overwrite the main status bar to keep it stable
                const newLog = {
                    id: Math.random().toString(36).substr(2, 9),
                    content: event.content,
                    type: 'thought',
                    timestamp
                };

                logsRef.current = [newLog, ...logsRef.current];
                setThoughtLogs([...logsRef.current]);
                break;

            case 'QUESTION':
                setStatus("Waiting for your input..."); // Clear obscure status
                setPendingQuestion(event.content);
                break;

            case 'FINAL_ANSWER':
                setStatus(null); // Finish
                // We might want to clear logs or keep them? Keep them.
                break;

            case 'ERROR':
                toast.error(event.content);
                setStatus("Error occurred");
                break;
        }
    };

    const sendAnswer = (answer: string) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({
                type: 'human_feedback',
                content: answer
            }));
            setPendingQuestion(null); // Clear question UI
            setStatus("جاري استكمال المعالجة..."); // Optimistic status
        }
    };

    return {
        status,
        thoughtLogs,
        pendingQuestion,
        isConnected,
        sendAnswer,
        clearLogs: () => {
            logsRef.current = [];
            setThoughtLogs([]);
        }
    };
};
