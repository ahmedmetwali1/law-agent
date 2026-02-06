/**
 * useSSE Hook - Real-time Server-Sent Events for Legal Research
 * 
 * Connects to the backend SSE endpoint and provides real-time updates
 * for agent status, thinking steps, and worksheet updates.
 */

import { useState, useEffect, useCallback, useRef } from 'react'

// Event types matching backend
export type SSEEventType =
    | 'agent_status'
    | 'thinking_step'
    | 'tool_call'
    | 'tool_result'
    | 'worksheet_update'
    | 'chat_message'
    | 'error'
    | 'complete'
    | 'heartbeat'

// Event data interfaces
export interface AgentStatusEvent {
    agent: string
    agent_ar: string
    status: string
    message: string
    iteration?: number
    total_iterations?: number
}

export interface ThinkingStepEvent {
    agent: string
    iteration: number
    phase: string
    thought: string
    action?: string
}

export interface WorksheetUpdateEvent {
    worksheet_id: string
    section_type: string
    section_title: string
    content: string
    agent: string
}

export interface SSEEvent {
    type: SSEEventType
    data: AgentStatusEvent | ThinkingStepEvent | WorksheetUpdateEvent | Record<string, unknown>
    timestamp: string
    event_id: string
}

export interface ThinkingStep {
    iteration: number
    phase: string
    message: string
    status: 'pending' | 'active' | 'complete'
    timestamp?: string
}

export interface WorksheetSection {
    section_type: string
    title: string
    content: string
    agent: string
}

export interface UseSSEResult {
    // State
    isConnected: boolean
    isResearchActive: boolean
    thinkingSteps: ThinkingStep[]
    worksheetSections: WorksheetSection[]
    currentAgent: string | null
    currentPhase: string | null
    confidenceScore: number | null
    error: string | null

    // Actions
    startResearch: (message: string, sessionId: string, countryId?: string, caseId?: string) => void
    stopResearch: () => void
    reset: () => void
}

export function useSSE(token: string): UseSSEResult {
    const [isConnected, setIsConnected] = useState(false)
    const [isResearchActive, setIsResearchActive] = useState(false)
    const [thinkingSteps, setThinkingSteps] = useState<ThinkingStep[]>([])
    const [worksheetSections, setWorksheetSections] = useState<WorksheetSection[]>([])
    const [currentAgent, setCurrentAgent] = useState<string | null>(null)
    const [currentPhase, setCurrentPhase] = useState<string | null>(null)
    const [confidenceScore, setConfidenceScore] = useState<number | null>(null)
    const [error, setError] = useState<string | null>(null)

    const eventSourceRef = useRef<EventSource | null>(null)
    const sessionIdRef = useRef<string | null>(null)

    // Handle incoming SSE event
    const handleEvent = useCallback((event: MessageEvent) => {
        try {
            const sseEvent: SSEEvent = JSON.parse(event.data)

            switch (sseEvent.type) {
                case 'agent_status': {
                    const data = sseEvent.data as AgentStatusEvent
                    setCurrentAgent(data.agent_ar || data.agent)

                    // Update thinking steps
                    if (data.iteration !== undefined && data.iteration !== null) {
                        const iteration = data.iteration // Capture for closure
                        setThinkingSteps(prev => {
                            const existing = prev.find(s => s.iteration === iteration)
                            if (existing) {
                                return prev.map(s =>
                                    s.iteration === iteration
                                        ? { ...s, message: data.message, status: data.status === 'completed' ? 'complete' as const : 'active' as const }
                                        : s
                                )
                            }
                            return [...prev, {
                                iteration: iteration,
                                phase: data.status,
                                message: data.message,
                                status: 'active' as const,
                                timestamp: sseEvent.timestamp
                            }]
                        })
                    }
                    break
                }

                case 'thinking_step': {
                    const data = sseEvent.data as ThinkingStepEvent
                    setCurrentPhase(data.phase)

                    setThinkingSteps(prev => {
                        const existing = prev.find(s => s.iteration === data.iteration)
                        if (existing) {
                            return prev.map(s =>
                                s.iteration === data.iteration
                                    ? { ...s, message: data.thought, phase: data.phase, status: 'active' }
                                    : { ...s, status: s.status === 'active' ? 'complete' : s.status }
                            )
                        }
                        // Mark previous as complete
                        const updated = prev.map(s => ({ ...s, status: 'complete' as const }))
                        return [...updated, {
                            iteration: data.iteration,
                            phase: data.phase,
                            message: data.thought,
                            status: 'active' as const,
                            timestamp: sseEvent.timestamp
                        }]
                    })
                    break
                }

                case 'worksheet_update': {
                    const data = sseEvent.data as WorksheetUpdateEvent
                    setWorksheetSections(prev => {
                        const existing = prev.find(s => s.section_type === data.section_type)
                        if (existing) {
                            return prev.map(s =>
                                s.section_type === data.section_type
                                    ? { ...s, content: data.content, title: data.section_title }
                                    : s
                            )
                        }
                        return [...prev, {
                            section_type: data.section_type,
                            title: data.section_title,
                            content: data.content,
                            agent: data.agent
                        }]
                    })
                    break
                }

                case 'complete': {
                    const data = sseEvent.data as { confidence_score?: number; message?: string }
                    setIsResearchActive(false)
                    setConfidenceScore(data.confidence_score ?? null)

                    // Mark all steps as complete
                    setThinkingSteps(prev => prev.map(s => ({ ...s, status: 'complete' as const })))
                    break
                }

                case 'error': {
                    const data = sseEvent.data as { error: string }
                    setError(data.error)
                    setIsResearchActive(false)
                    break
                }

                case 'heartbeat':
                    // Just keep alive
                    break

                default:
                    console.log('Unknown event type:', sseEvent.type)
            }
        } catch (err) {
            console.error('Failed to parse SSE event:', err)
        }
    }, [])

    // Start research with SSE
    const startResearch = useCallback((
        message: string,
        sessionId: string,
        countryId?: string,
        caseId?: string
    ) => {
        // Close existing connection
        if (eventSourceRef.current) {
            eventSourceRef.current.close()
        }

        // Reset state
        setThinkingSteps([])
        setWorksheetSections([])
        setError(null)
        setConfidenceScore(null)
        setIsResearchActive(true)
        setIsConnected(false)

        sessionIdRef.current = sessionId

        // Build URL with query params
        const params = new URLSearchParams({
            message,
            session_id: sessionId,
            ...(countryId && { country_id: countryId }),
            ...(caseId && { case_id: caseId })
        })

        // Create POST request for SSE (using fetch + EventSource pattern)
        // Note: Standard EventSource doesn't support POST, so we use fetch first
        const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

        fetch(`${API_BASE}/api/ai/stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                message,
                session_id: sessionId,
                country_id: countryId,
                case_id: caseId
            })
        }).then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`)
            }

            const reader = response.body?.getReader()
            if (!reader) {
                throw new Error('No readable stream')
            }

            setIsConnected(true)

            const decoder = new TextDecoder()
            let buffer = ''

            const processStream = async () => {
                while (true) {
                    const { done, value } = await reader.read()

                    if (done) {
                        setIsConnected(false)
                        break
                    }

                    buffer += decoder.decode(value, { stream: true })

                    // Process complete SSE messages
                    const messages = buffer.split('\n\n')
                    buffer = messages.pop() || '' // Keep incomplete message

                    for (const msg of messages) {
                        if (msg.startsWith('data: ')) {
                            handleEvent({ data: msg.slice(6) } as MessageEvent)
                        }
                    }
                }
            }

            processStream().catch(err => {
                console.error('Stream error:', err)
                setError(err.message)
                setIsResearchActive(false)
                setIsConnected(false)
            })

        }).catch(err => {
            console.error('Failed to start SSE:', err)
            setError(err.message)
            setIsResearchActive(false)
        })

    }, [token, handleEvent])

    // Stop research
    const stopResearch = useCallback(() => {
        if (eventSourceRef.current) {
            eventSourceRef.current.close()
            eventSourceRef.current = null
        }

        setIsResearchActive(false)
        setIsConnected(false)

        // Notify backend to close stream
        if (sessionIdRef.current) {
            const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
            fetch(`${API_BASE}/api/ai/stream/${sessionIdRef.current}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            }).catch(() => {
                // Ignore errors on cleanup
            })
        }
    }, [token])

    // Reset state
    const reset = useCallback(() => {
        stopResearch()
        setThinkingSteps([])
        setWorksheetSections([])
        setCurrentAgent(null)
        setCurrentPhase(null)
        setConfidenceScore(null)
        setError(null)
    }, [stopResearch])

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (eventSourceRef.current) {
                eventSourceRef.current.close()
            }
        }
    }, [])

    return {
        isConnected,
        isResearchActive,
        thinkingSteps,
        worksheetSections,
        currentAgent,
        currentPhase,
        confidenceScore,
        error,
        startResearch,
        stopResearch,
        reset
    }
}
