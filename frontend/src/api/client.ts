import axios from 'axios';

const API_BASE_URL = import.meta.env?.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add auth token to all requests
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('auth_token'); // ✅ Fixed: was 'token', now 'auth_token'
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Types
export interface NewCaseRequest {
    facts: string;
    client_name?: string;
    case_type?: string;
    additional_data?: Record<string, any>;
}

export interface CaseResponse {
    case_id: string;
    status: string;
    analysis?: any;
    plan?: any;
    specialist_reports?: any[];
    final_recommendation?: any;
    case_file_path?: string;
}

export interface Message {
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp?: string;
}

// API Functions
export interface ChatResponse {
    session_id: string;
    message: string;
    stage: string;
    completed: boolean;
    case_data?: any;
    case_id?: string;
    response_type?: string;
}

// API Functions
export const caseApi = {
    // Chat interactions
    startChat: async (): Promise<ChatResponse> => {
        const response = await api.post('/api/chat/start');
        return response.data;
    },

    sendChatMessage: async (sessionId: string, message: string): Promise<ChatResponse> => {
        const response = await api.post(`/api/chat/${sessionId}/message`, { message });
        return response.data;
    },

    // Create new case
    createCase: async (data: NewCaseRequest): Promise<CaseResponse> => {
        const response = await api.post('/api/cases/new', data);
        return response.data;
    },

    // Analyze case
    analyzeCase: async (caseId: string): Promise<CaseResponse> => {
        const response = await api.post(`/api/cases/${caseId}/analyze`);
        return response.data;
    },

    // Process complete case
    processCase: async (caseId: string): Promise<CaseResponse> => {
        const response = await api.post(`/api/cases/${caseId}/process`);
        return response.data;
    },

    // Get case details
    getCase: async (caseId: string): Promise<CaseResponse> => {
        const response = await api.get(`/api/cases/${caseId}`);
        return response.data;
    },

    // List cases
    listCases: async (limit = 100): Promise<any> => {
        const response = await api.get(`/api/cases?limit=${limit}`);
        return response.data;
    },

    // Delete case
    deleteCase: async (caseId: string): Promise<void> => {
        await api.delete(`/api/cases/${caseId}`);
    },
};

export const healthCheck = async (): Promise<any> => {
    const response = await api.get('/health');
    return response.data;
};

/**
 * Simplified API Client for non-axios endpoints
 * Used for dashboard, settings, audit logs
 */
export const apiClient = {
    async get<T = any>(endpoint: string): Promise<T> {
        const token = localStorage.getItem('access_token')
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'GET',
            headers: {
                'Authorization': token ? `Bearer ${token}` : '',
                'Content-Type': 'application/json'
            }
        })
        if (!response.ok) {
            throw new Error(`API Error: ${response.statusText}`)
        }
        return response.json()
    },

    async post<T = any>(endpoint: string, data: any): Promise<T> {
        const token = localStorage.getItem('access_token')
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'POST',
            headers: {
                'Authorization': token ? `Bearer ${token}` : '',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        if (!response.ok) {
            throw new Error(`API Error: ${response.statusText}`)
        }
        return response.json()
    }
}
