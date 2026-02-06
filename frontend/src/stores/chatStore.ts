import { create } from 'zustand'
import { persist } from 'zustand/middleware'

// --- Interfaces ---

export interface TaskSchema {
    task_type: string
    status: 'pending' | 'in_progress' | 'completed' | 'failed'
    steps: Array<{
        step_number: number
        description: string
        status: string
    }>
}

export interface MonologueEntry {
    id: string
    agent: string // Strategist, Auditor...
    content: string
    timestamp: Date
}

export interface Message {
    id: string
    role: 'user' | 'assistant'
    content: string
    taskJson?: TaskSchema
    timestamp: Date
    isComplete?: boolean
}

export interface ActivityState {
    stage: 'ROUTING' | 'INVESTIGATING' | 'DELIBERATING' | 'VERDICT' | 'IDLE'
    actor: string
    action: string
    isThinking: boolean
}

export interface HCFDecision {
    path: 'DIRECT' | 'ANALOGICAL' | 'BOUNDING' | 'FALLBACK' | 'UNKNOWN';
    status: 'VERIFIED_SOURCE' | 'VERIFIED_ANALOGY' | 'UNVERIFIED_ESTIMATE' | 'UNVERIFIED' | 'UNKNOWN';
    confidence: number;
    timestamp: Date;
}

interface ChatState {
    messages: Message[]
    isStreaming: boolean
    currentRoute: string
    abortController: AbortController | null

    // Vital V3.0 State
    currentActivity: ActivityState
    councilSession: {
        activeAgents: string[]
        monologues: MonologueEntry[]
    }
    hcfDecisions: HCFDecision[];

    sendMessage: (content: string, options?: { session_id?: string }) => Promise<void>
    stopGeneration: () => void
    addMessage: (message: Message) => void
    clearChat: () => void
    setRoute: (route) => void
    resetActivity: () => void
    hydrateFromMessages: (messages: Message[]) => void
}

export const useChatStore = create<ChatState>()(
    persist(
        (set, get) => ({
            messages: [],
            isStreaming: false,
            currentRoute: '/',
            abortController: null,

            // Initial Vital State
            currentActivity: {
                stage: 'IDLE',
                actor: 'System',
                action: 'Ready',
                isThinking: false
            },
            councilSession: {
                activeAgents: [],
                monologues: []
            },
            hcfDecisions: [],

            resetActivity: () => {
                set({
                    currentActivity: { stage: 'IDLE', actor: 'System', action: 'Ready', isThinking: false },
                    councilSession: { activeAgents: [], monologues: [] },
                    hcfDecisions: []
                })
            },

            sendMessage: async (content: string, options = {}) => {
                const { isStreaming } = get()
                if (isStreaming || !content.trim()) return

                const controller = new AbortController()
                set({ isStreaming: true, abortController: controller })

                // Reset Activity for new turn
                set({
                    currentActivity: { stage: 'ROUTING', actor: 'System', action: 'Starting...', isThinking: true },
                    councilSession: { activeAgents: [], monologues: [] }, // Clear previous council session
                    hcfDecisions: []
                })

                const userMessage: Message = {
                    id: crypto.randomUUID(),
                    role: 'user',
                    content,
                    timestamp: new Date(),
                    isComplete: true,
                }

                set((state) => ({ messages: [...state.messages, userMessage] }))

                const assistantMessageId = crypto.randomUUID()
                const assistantMessage: Message = {
                    id: assistantMessageId,
                    role: 'assistant',
                    content: '', // Will stream
                    timestamp: new Date(),
                    isComplete: false,
                }

                set((state) => ({ messages: [...state.messages, assistantMessage] }))

                let accumulatedContent = ''
                try {
                    // Use the specific stream endpoint!
                    const response = await fetch('/api/chat/stream', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${localStorage.getItem('token') || ''}`,
                        },
                        body: JSON.stringify({
                            message: content,
                            session_id: options.session_id,
                            mode: 'auto'
                        }),
                        signal: controller.signal
                    })

                    if (!response.ok) throw new Error('Chat request failed')
                    if (!response.body) throw new Error('ReadableStream not supported')

                    const reader = response.body.getReader()
                    const decoder = new TextDecoder()
                    let buffer = ''


                    while (true) {
                        const { done, value } = await reader.read()
                        if (done) break

                        buffer += decoder.decode(value, { stream: true })
                        const lines = buffer.split('\n\n')
                        buffer = lines.pop() || ''

                        for (const line of lines) {
                            if (line.startsWith('data: ')) {
                                try {
                                    const jsonStr = line.slice(6)
                                    if (!jsonStr || jsonStr === '[DONE]') continue

                                    const data = JSON.parse(jsonStr)

                                    // --- EVENT HANDLERS (VITAL V3.0) ---

                                    if (data.type === 'stage_change') {
                                        set((state) => ({
                                            currentActivity: { ...state.currentActivity, stage: data.stage }
                                        }))
                                    }
                                    else if (data.type === 'hcf_decision') {
                                        const { selected_path, verification_status, confidence_score } = data.payload
                                        set((state) => ({
                                            hcfDecisions: [...state.hcfDecisions, {
                                                path: selected_path,
                                                status: verification_status,
                                                confidence: confidence_score,
                                                timestamp: new Date()
                                            }]
                                        }))
                                    }
                                    else if (data.type === 'step_update') {
                                        const { actor, status, message } = data.payload
                                        set((state) => ({
                                            currentActivity: {
                                                ...state.currentActivity,
                                                actor: actor || state.currentActivity.actor,
                                                action: message || status,
                                                isThinking: true
                                            }
                                        }))
                                    }
                                    else if (data.type === 'council_thought') {
                                        const { agent, content } = data.payload
                                        const entry: MonologueEntry = {
                                            id: crypto.randomUUID(),
                                            agent,
                                            content,
                                            timestamp: new Date()
                                        }

                                        set((state) => {
                                            // Limit History (Genius Tweak #2)
                                            const newMonologues = [...state.councilSession.monologues, entry].slice(-20)
                                            const newAgents = Array.from(new Set([...state.councilSession.activeAgents, agent]))

                                            return {
                                                councilSession: {
                                                    activeAgents: newAgents,
                                                    monologues: newMonologues
                                                }
                                            }
                                        })
                                    }
                                    else if (data.type === 'token') {
                                        accumulatedContent += data.content
                                        set((state) => ({
                                            messages: state.messages.map(m =>
                                                m.id === assistantMessageId
                                                    ? { ...m, content: accumulatedContent }
                                                    : m
                                            ),
                                            // Ensure activity is Verdict when tokens start flow
                                            currentActivity: {
                                                ...state.currentActivity,
                                                isThinking: false, // Typing is not "thinking"
                                                action: 'Typing...',
                                                stage: state.currentActivity.stage === 'IDLE' ? 'VERDICT' : state.currentActivity.stage
                                            }
                                        }))
                                    }
                                    else if (data.type === 'error') {
                                        accumulatedContent += `\n❌ ${data.content}`
                                        set((state) => ({
                                            messages: state.messages.map(m =>
                                                m.id === assistantMessageId
                                                    ? { ...m, content: accumulatedContent }
                                                    : m
                                            )
                                        }))
                                    }

                                } catch (e) {
                                    console.error('SSE Parse Error', e)
                                }
                            }
                        }
                    }

                } catch (error) {
                    console.error('Chat error:', error)
                    set((state) => ({
                        messages: state.messages.map(m =>
                            m.id === assistantMessageId
                                ? { ...m, content: accumulatedContent || 'عذراً، حدث خطأ في الاتصال' }
                                : m
                        )
                    }))
                } finally {
                    set((state) => ({
                        isStreaming: false,
                        abortController: null,
                        currentActivity: { ...state.currentActivity, isThinking: false, action: 'Complete' }
                    }))
                }
            },

            stopGeneration: () => {
                const { abortController } = get()
                if (abortController) {
                    abortController.abort()
                    set({ isStreaming: false, abortController: null })
                }
            },

            addMessage: (message) => set((state) => ({
                messages: [...state.messages, message]
            })),

            clearChat: () => set({ messages: [], councilSession: { activeAgents: [], monologues: [] }, hcfDecisions: [] }),

            setRoute: (route: string) => set({ currentRoute: route }),

            hydrateFromMessages: (messages) => {
                const monologues: MonologueEntry[] = [];
                const decisions: HCFDecision[] = [];
                const agents = new Set<string>();

                messages.forEach(msg => {
                    // Check for metadata in the message object (needs to be added to interface if strict)
                    // We assume it might be passed or we need to fetch it.
                    // Actually, the Message interface needs 'metadata' property.
                    const meta = (msg as any).metadata;
                    if (meta) {
                        if (meta.council_log && Array.isArray(meta.council_log)) {
                            meta.council_log.forEach((log: any) => {
                                monologues.push({
                                    id: crypto.randomUUID(),
                                    agent: log.agent,
                                    content: log.content,
                                    timestamp: new Date(log.timestamp)
                                });
                                agents.add(log.agent);
                            });
                        }
                        if (meta.hcf_log && Array.isArray(meta.hcf_log)) {
                            meta.hcf_log.forEach((dec: any) => {
                                decisions.push({
                                    path: dec.selected_path,
                                    status: dec.verification_status,
                                    confidence: dec.confidence_score,
                                    timestamp: new Date() // fallback if no timestamp in log
                                });
                            });
                        }
                    }
                });

                if (monologues.length > 0 || decisions.length > 0) {
                    set({
                        councilSession: {
                            activeAgents: Array.from(agents),
                            monologues: monologues.sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime())
                        },
                        hcfDecisions: decisions
                    });
                }
            }
        }),
        {
            name: 'legal-ai-chat-v3', // New storage key to avoid conflict
            partialize: (state) => ({ messages: state.messages }), // Only persist messages, not ephemeral state
        }
    )
)
