import { create } from 'zustand';
import { CaseResponse } from '@/api/client';

interface Message {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: Date;
}

interface ChatStore {
    messages: Message[];
    isTyping: boolean;
    addMessage: (role: Message['role'], content: string) => void;
    setTyping: (typing: boolean) => void;
    clearMessages: () => void;
}

export const useChatStore = create<ChatStore>((set) => ({
    messages: [
        {
            id: '1',
            role: 'assistant',
            content: 'مرحباً! أنا المحامي الذكي. كيف يمكنني مساعدتك اليوم؟',
            timestamp: new Date(),
        },
    ],
    isTyping: false,
    addMessage: (role, content) =>
        set((state) => ({
            messages: [
                ...state.messages,
                {
                    id: Date.now().toString(),
                    role,
                    content,
                    timestamp: new Date(),
                },
            ],
        })),
    setTyping: (typing) => set({ isTyping: typing }),
    clearMessages: () =>
        set({
            messages: [
                {
                    id: '1',
                    role: 'assistant',
                    content: 'مرحباً! أنا المحامي الذكي. كيف يمكنني مساعدتك اليوم؟',
                    timestamp: new Date(),
                },
            ],
        }),
}));

interface CaseStore {
    currentCase: CaseResponse | null;
    cases: CaseResponse[];
    isProcessing: boolean;
    setCurrentCase: (caseData: CaseResponse | null) => void;
    setCases: (cases: CaseResponse[]) => void;
    setProcessing: (processing: boolean) => void;
    updateCurrentCase: (updates: Partial<CaseResponse>) => void;
}

export const useCaseStore = create<CaseStore>((set) => ({
    currentCase: null,
    cases: [],
    isProcessing: false,
    setCurrentCase: (caseData) => set({ currentCase: caseData }),
    setCases: (cases) => set({ cases }),
    setProcessing: (processing) => set({ isProcessing: processing }),
    updateCurrentCase: (updates) =>
        set((state) => ({
            currentCase: state.currentCase
                ? { ...state.currentCase, ...updates }
                : null,
        })),
}));

interface UIStore {
    activeTab: 'overview' | 'plan' | 'progress' | 'results';
    sidebarCollapsed: boolean;
    theme: 'light' | 'dark';
    setActiveTab: (tab: UIStore['activeTab']) => void;
    toggleSidebar: () => void;
    setTheme: (theme: 'light' | 'dark') => void;
}

export const useUIStore = create<UIStore>((set) => ({
    activeTab: 'overview',
    sidebarCollapsed: false,
    theme: 'light',
    setActiveTab: (tab) => set({ activeTab: tab }),
    toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
    setTheme: (theme) => set({ theme }),
}));
