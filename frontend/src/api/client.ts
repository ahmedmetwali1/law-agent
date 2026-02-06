import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, InternalAxiosRequestConfig } from 'axios';

const API_BASE_URL = import.meta.env?.VITE_API_URL || 'http://localhost:8000';

// Extended Request Config to support boolean helper flags if needed (future proofing)
interface CustomRequestConfig extends AxiosRequestConfig {
    _retry?: boolean;
}

// Single Axios Instance
const axiosInstance: AxiosInstance = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request Interceptor: Auth Token
axiosInstance.interceptors.request.use((config: InternalAxiosRequestConfig) => {
    // Check both common storage keys
    const token = localStorage.getItem('auth_token') || localStorage.getItem('access_token');
    if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
}, (error) => Promise.reject(error));

// Response Interceptor: Global Error Handling
axiosInstance.interceptors.response.use(
    (response: AxiosResponse) => response,
    (error) => {
        // Here we could handle 401 Unauthorized globally (redirect to login)
        if (error.response?.status === 401) {
            console.warn("Unauthorized! Redirecting to login...");
            // window.location.href = '/login'; // Optional: Auto-redirect
        }
        // Return a cleaner error object
        const message = error.response?.data?.detail || error.message || 'Unknown API Error';
        return Promise.reject(new Error(message));
    }
);

// --- Shared Types (Mirrors Backend) ---

export interface ChatResponse {
    session_id: string;
    message: string;
    stage: string;
    completed: boolean;
    case_data?: any;
    case_id?: string;
    metadata?: any;
}

export interface NewCaseRequest {
    facts: string;
    client_name?: string;
    case_type?: string;
    additional_data?: Record<string, any>;
}

export interface CaseResponse {
    case_id: string;
    id?: string; // Some views use 'id'
    title?: string;
    client?: {
        full_name: string;
        id: string;
    };
    status: string;
    analysis?: any;
    plan?: any;
    specialist_reports?: any[];
    final_recommendation?: any;
    case_file_path?: string;
}

// --- Unified Client Wrapper ---

export const apiClient = {
    // Generic HTTP Methods (Backward compatibility for fetch wrapper)
    get: async <T = any>(url: string, config?: AxiosRequestConfig): Promise<T> => {
        const response = await axiosInstance.get<T>(url, config);
        return response.data;
    },

    post: async <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
        const response = await axiosInstance.post<T>(url, data, config);
        return response.data;
    },

    put: async <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
        const response = await axiosInstance.put<T>(url, data, config);
        return response.data;
    },

    patch: async <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
        const response = await axiosInstance.patch<T>(url, data, config);
        return response.data;
    },

    delete: async <T = any>(url: string, config?: AxiosRequestConfig): Promise<T> => {
        const response = await axiosInstance.delete<T>(url, config);
        return response.data;
    },

    // --- Domain Specific Methods ---

    chat: {
        start: async (): Promise<ChatResponse> => {
            return apiClient.post<ChatResponse>('/api/chat/start');
        },
        sendMessage: async (sessionId: string, message: string, mode: "auto" | "admin_assistant" | "legal_researcher" = "auto", context_summary?: string): Promise<ChatResponse> => {
            return apiClient.post<ChatResponse>(`/api/chat/${sessionId}/message`, { message, mode, context_summary });
        }
    },

    cases: {
        create: async (data: NewCaseRequest): Promise<CaseResponse> => {
            return apiClient.post<CaseResponse>('/api/cases/new', data);
        },
        get: async (caseId: string): Promise<CaseResponse> => {
            return apiClient.get<CaseResponse>(`/api/cases/${caseId}`);
        },
        list: async (limit = 100): Promise<any> => {
            return apiClient.get(`/api/cases?limit=${limit}`);
        }
    }
};

// Export raw axios instance if needed for special cases
export const api = axiosInstance;
export const caseApi = {
    startChat: apiClient.chat.start,
    sendChatMessage: apiClient.chat.sendMessage,
    createCase: apiClient.cases.create,
    getCase: apiClient.cases.get,
    listCases: apiClient.cases.list,
    deleteCase: (id: string) => apiClient.delete(`/api/cases/${id}`),
    analyzeCase: (id: string) => apiClient.post(`/api/cases/${id}/analyze`),
    processCase: (id: string) => apiClient.post(`/api/cases/${id}/process`)
};

export const healthCheck = async () => apiClient.get('/health');
