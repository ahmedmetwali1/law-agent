import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface TaskSchema {
    task_type: string
    status: 'pending' | 'in_progress' | 'completed' | 'failed'
    steps: Array<{
        step_number: number
        description: string
        status: string
    }>
}

export interface Message {
    id: string
    role: 'user' | 'assistant'
    content: string
    thoughts?: string[] // For thinking steps
    taskJson?: TaskSchema
    timestamp: Date
    isComplete?: boolean  // Track if message finished typing
}

interface ChatState {
    messages: Message[]
    isStreaming: boolean
    currentRoute: string
    abortController: AbortController | null

    sendMessage: (content: string) => Promise<void>
    stopGeneration: () => void
    addMessage: (message: Message) => void
    markMessageComplete: (messageId: string) => void
    updateTaskStatus: (messageId: string, taskJson: TaskSchema) => void
    clearChat: () => void
    setRoute: (route: string) => void
}

export const useChatStore = create<ChatState>()(
    persist(
        (set, get) => ({
            messages: [],
            isStreaming: false,
            currentRoute: '/',
            abortController: null,

            sendMessage: async (content: string) => {
                const { isStreaming, messages } = get()
                if (isStreaming || !content.trim()) return

                // Create AbortController
                const controller = new AbortController()
                set({ isStreaming: true, abortController: controller })

                const userMessage: Message = {
                    id: crypto.randomUUID(),
                    role: 'user',
                    content,
                    timestamp: new Date(),
                    isComplete: true,  // User messages are instant
                }

                set((state) => ({ messages: [...state.messages, userMessage] }))

                // Create placeholder assistant message
                const assistantMessageId = crypto.randomUUID()
                const assistantMessage: Message = {
                    id: assistantMessageId,
                    role: 'assistant',
                    content: '',
                    timestamp: new Date(),
                    isComplete: false,  // Will be marked complete after typing
                }

                set((state) => ({ messages: [...state.messages, assistantMessage] }))

                try {
                    const response = await fetch('/api/chat', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${localStorage.getItem('token') || ''}`,
                        },
                        body: JSON.stringify({
                            message: content,
                            history: get().messages.slice(0, -2).map(m => ({
                                role: m.role,
                                content: m.content
                            })),
                            lawyer_id: JSON.parse(localStorage.getItem('user') || '{}').id,
                        }),
                        signal: controller.signal // Bind abort signal
                    })

                    if (!response.ok) {
                        throw new Error('Chat request failed')
                    }

                    if (!response.body) throw new Error('ReadableStream not supported')

                    const reader = response.body.getReader()
                    const decoder = new TextDecoder()
                    let buffer = ''
                    let accumulatedContent = ''

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

                                    // Handle Events
                                    if (data.type === 'thought') {
                                        set((state) => ({
                                            messages: state.messages.map(m =>
                                                m.id === assistantMessageId
                                                    ? { ...m, thoughts: [...(m.thoughts || []), data.content] }
                                                    : m
                                            )
                                        }))
                                    } else if (data.type === 'text') {
                                        accumulatedContent += data.content
                                        set((state) => ({
                                            messages: state.messages.map(m =>
                                                m.id === assistantMessageId
                                                    ? { ...m, content: accumulatedContent }
                                                    : m
                                            )
                                        }))
                                    } else if (data.type === 'task_json') {
                                        set((state) => ({
                                            messages: state.messages.map(m =>
                                                m.id === assistantMessageId
                                                    ? { ...m, taskJson: data.task }
                                                    : m
                                            )
                                        }))
                                    } else if (data.type === 'done') {
                                        // Finished
                                    } else if (data.type === 'error') {
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
                                ? { ...m, content: 'عذراً، حدث خطأ في الاتصال' }
                                : m
                        )
                    }))
                } finally {
                    set({ isStreaming: false, abortController: null })
                }
            },

            stopGeneration: () => {
                const { abortController } = get()
                if (abortController) {
                    abortController.abort()
                    set({ isStreaming: false, abortController: null })

                    // Optional: Add "Cancelled" message or marker? 
                    // For now just stopping is enough.
                }
            },

            addMessage: (message) => set((state) => ({
                messages: [...state.messages, message]
            })),

            markMessageComplete: (messageId) => set((state) => ({
                messages: state.messages.map(m =>
                    m.id === messageId ? { ...m, isComplete: true } : m
                )
            })),

            updateTaskStatus: (messageId, taskJson) => set((state) => ({
                messages: state.messages.map(m =>
                    m.id === messageId ? { ...m, taskJson } : m
                )
            })),

            clearChat: () => set({ messages: [] }),

            setRoute: (route) => set({ currentRoute: route }),
        }),
        {
            name: 'legal-ai-chat',
            partialize: (state) => ({ messages: state.messages }),
        }
    )
)
