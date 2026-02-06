/**
 * Admin API Client
 * TypeScript client for Super Admin Dashboard API endpoints
 */

import { apiClient } from './client';

// ============================================================================
// Types & Interfaces
// ============================================================================

export interface PlatformSettings {
    id: string;
    // Platform Info
    platform_name: string;
    platform_name_en: string;
    platform_description?: string;
    platform_logo_url?: string;
    platform_favicon_url?: string;

    // Lawyers Control
    lawyers_activation_status?: Record<string, any>;
    max_lawyers_allowed?: number;
    max_assistants_per_lawyer?: number;
    max_clients_per_lawyer?: number;
    max_cases_per_lawyer?: number;

    // Redis
    redis_enabled?: boolean;
    redis_host?: string;
    redis_port?: number;
    redis_password?: string;
    redis_db?: number;
    redis_max_connections?: number;
    redis_ttl_default?: number;

    // AI
    ai_provider?: string;
    ai_api_url?: string;
    ai_api_key?: string;
    ai_model_name?: string;
    ai_temperature?: number;
    ai_max_tokens?: number;

    // Embedding
    embedding_provider?: string;
    embedding_api_url?: string;
    embedding_api_key?: string;
    embedding_model_name?: string;
    embedding_dimensions?: number;

    // SMTP
    smtp_enabled?: boolean;
    smtp_host?: string;
    smtp_port?: number;
    smtp_username?: string;
    smtp_password?: string;
    smtp_from_email?: string;
    smtp_from_name?: string;
    smtp_use_tls?: boolean;

    // STT
    stt_api_url?: string;
    stt_api_key?: string;

    // SEO
    seo_title?: string;
    seo_description?: string;
    seo_keywords?: string[];
    seo_og_image_url?: string;
    seo_twitter_card_type?: string;

    // Social & Contact
    social_media_links?: Record<string, string>;
    contact_email?: string;
    contact_phone?: string;
    contact_whatsapp?: string;
    contact_address?: string;
    support_hours?: string;

    // Interactive Elements
    popup_enabled?: boolean;
    popup_title?: string;
    popup_content?: string;
    popup_button_text?: string;
    popup_button_link?: string;
    popup_display_after_seconds?: number;
    popup_display_frequency?: string;

    // Footer Settings
    footer_copyright_text?: string;
    footer_powered_by?: string;
    footer_links?: Array<{ text: string, url: string }> | string;

    // Telegram Bot
    telegram_enabled?: boolean;
    telegram_bot_token?: string;
    telegram_chat_id?: string;
    telegram_notifications_types?: string[];

    // Email Verification
    email_verification_enabled?: boolean;
    email_verification_expiry_hours?: number;


    alert_bar_enabled?: boolean;
    alert_bar_message?: string;
    alert_bar_type?: string;
    alert_bar_dismissible?: boolean;
    alert_bar_link?: string;
    alert_bar_link_text?: string;

    maintenance_mode_enabled?: boolean;
    maintenance_mode_message?: string;
    maintenance_mode_allowed_ips?: string[];
    maintenance_mode_estimated_end?: string;

    // System Settings
    timezone?: string;
    default_language?: string;
    supported_languages?: string[];
    date_format?: string;
    time_format?: string;
    currency?: string;

    // Limits
    max_file_upload_size_mb?: number;
    allowed_file_types?: string[];
    max_audio_recording_duration_seconds?: number;

    // Security
    session_timeout_minutes?: number;
    max_login_attempts?: number;
    lockout_duration_minutes?: number;
    require_2fa?: boolean;
    password_min_length?: number;
    password_require_special_chars?: boolean;

    // Audit
    audit_log_retention_days?: number;
    enable_detailed_logging?: boolean;

    // Additional
    additional_config?: Record<string, any>;

    // Metadata
    created_at: string;
    updated_at: string;
    updated_by?: string;
    version: number;
}

export interface LawyerInfo {
    id: string;
    full_name: string;
    email: string;
    phone?: string;
    role: string;
    is_active: boolean;
    created_at: string;

    // Professional Details
    specialization?: string;
    license_number?: string;
    lawyer_license_type?: string;
    bar_association?: string;
    years_of_experience?: number;
    languages?: string[];
    bio?: string;

    // Office & Presence
    office_address?: string;
    office_city?: string;
    office_postal_code?: string;
    website?: string;
    linkedin_profile?: string;
    profile_image_url?: string;
    role_info?: {
        name: string;
        name_ar: string;
    };

    // Statistics
    total_cases?: number;
    total_clients?: number;
    total_hearings?: number;
}

export interface LawyersStats {
    total_lawyers: number;
    active_lawyers: number;
    inactive_lawyers: number;
    total_assistants: number;
    total_cases_all: number;
    total_clients_all: number;
}

export interface SystemHealth {
    status: string;
    timestamp: string;
    services: {
        database: {
            status: string;
            latency_ms: number;
        };
        cache: {
            status: string;
            enabled: boolean;
            available: boolean;
            hit_rate: string;
            server_info?: any;
        };
    };
    metrics: {
        cache: {
            hits: number;
            misses: number;
            sets: number;
            deletes: number;
            errors: number;
        };
    };
}

export interface SupportTemplate {
    id: string;
    template_name: string;
    template_category?: string;
    template_content: string;
    is_active: boolean;
    usage_count: number;
    created_at: string;
    created_by?: string;
    updated_at: string;
}

export interface SystemAnnouncement {
    id: string;
    title: string;
    content: string;
    announcement_type: string;
    target_audience: string;
    start_date?: string;
    end_date?: string;
    is_active: boolean;
    is_dismissible: boolean;
    priority: number;
    created_at: string;
    created_by?: string;
}

// ============================================================================
// API Functions
// ============================================================================

// Platform Settings
export const getPlatformSettings = async (): Promise<PlatformSettings> => {
    return await apiClient.get<PlatformSettings>('/api/admin/platform-settings');
};

export const updatePlatformSettings = async (
    settings: Partial<PlatformSettings>
): Promise<PlatformSettings> => {
    return await apiClient.put<PlatformSettings>('/api/admin/platform-settings', settings);
};

export const resetPlatformSettings = async (): Promise<{ message: string }> => {
    return await apiClient.post<{ message: string }>('/api/admin/platform-settings/reset', {});
};

// Lawyers Management
export const getAllLawyers = async (): Promise<LawyerInfo[]> => {
    return await apiClient.get<LawyerInfo[]>('/api/admin/lawyers');
};

export const toggleLawyerActivation = async (
    lawyerId: string,
    isActive: boolean,
    reason?: string
): Promise<{ message: string; lawyer_id: string; is_active: boolean }> => {
    return await apiClient.put<{ message: string; lawyer_id: string; is_active: boolean }>(
        `/api/admin/lawyers/${lawyerId}/activation`,
        {
            lawyer_id: lawyerId,
            is_active: isActive,
            reason
        }
    );
};

export const getLawyersStats = async (): Promise<LawyersStats> => {
    return await apiClient.get<LawyersStats>('/api/admin/lawyers/stats');
};

// System Health & Monitoring
export const getSystemHealth = async (): Promise<SystemHealth> => {
    return await apiClient.get<SystemHealth>('/api/admin/system/health');
};

export const clearCache = async (): Promise<{ message: string }> => {
    return await apiClient.post<{ message: string }>('/api/admin/system/cache/clear', {});
};

export const testConnection = async (
    service: string,
    config?: Record<string, any>
): Promise<{
    service: string;
    success: boolean;
    message: string;
    details?: any;
}> => {
    return await apiClient.post<{
        service: string;
        success: boolean;
        message: string;
        details?: any;
    }>('/api/admin/system/test-connection', {
        service,
        config
    });
};

// Support Templates
export const getSupportTemplates = async (): Promise<SupportTemplate[]> => {
    return await apiClient.get<SupportTemplate[]>('/api/admin/support/templates');
};

export const createSupportTemplate = async (
    template: Omit<SupportTemplate, 'id' | 'usage_count' | 'created_at' | 'created_by' | 'updated_at'>
): Promise<SupportTemplate> => {
    return await apiClient.post<SupportTemplate>('/api/admin/support/templates', template);
};

export const updateSupportTemplate = async (
    id: string,
    template: Partial<SupportTemplate>
): Promise<SupportTemplate> => {
    return await apiClient.put<SupportTemplate>(`/api/admin/support/templates/${id}`, template);
};

export const deleteSupportTemplate = async (id: string): Promise<{ message: string }> => {
    return await apiClient.delete<{ message: string }>(`/api/admin/support/templates/${id}`);
};

// System Announcements
export const getAnnouncements = async (): Promise<SystemAnnouncement[]> => {
    return await apiClient.get<SystemAnnouncement[]>('/api/admin/announcements');
};

export const createAnnouncement = async (
    announcement: Omit<SystemAnnouncement, 'id' | 'created_at' | 'created_by'>
): Promise<SystemAnnouncement> => {
    return await apiClient.post<SystemAnnouncement>('/api/admin/announcements', announcement);
};

export const updateAnnouncement = async (
    id: string,
    announcement: Partial<SystemAnnouncement>
): Promise<SystemAnnouncement> => {
    return await apiClient.put<SystemAnnouncement>(`/api/admin/announcements/${id}`, announcement);
};

export const deleteAnnouncement = async (id: string): Promise<{ message: string }> => {
    return await apiClient.delete<{ message: string }>(`/api/admin/announcements/${id}`);
};

// Audit Logs
export const getAuditLogs = async (
    limit: number = 100,
    offset: number = 0
): Promise<{
    logs: any[];
    total: number;
    limit: number;
    offset: number;
}> => {
    return await apiClient.get<{
        logs: any[];
        total: number;
        limit: number;
        offset: number;
    }>(`/api/admin/audit-logs?limit=${limit}&offset=${offset}`);
};

// ============================================================================
// Role Management Types & Functions
// ============================================================================

export interface RolePermissions {
    read: boolean;
    create: boolean;
    update: boolean;
    delete: boolean;
}

export interface Role {
    id: string;
    name: string;
    name_ar: string;
    description?: string;
    permissions: Record<string, RolePermissions>;
    is_active: boolean;
    is_default: boolean;
    created_at: string;
    updated_at: string;
}

export interface RoleCreate {
    name: string;
    name_ar: string;
    description?: string;
    permissions: Record<string, RolePermissions>;
    is_active?: boolean;
    is_default?: boolean;
}

export interface RoleUpdate {
    name?: string;
    name_ar?: string;
    description?: string;
    permissions?: Record<string, any>;
    is_active?: boolean;
    is_default?: boolean;
}

// Role Management API Functions
export const getAllRoles = async (): Promise<Role[]> => {
    return await apiClient.get<Role[]>('/api/admin/roles');
};

export const getRole = async (roleId: string): Promise<Role> => {
    return await apiClient.get<Role>(`/api/admin/roles/${roleId}`);
};

export const createRole = async (role: RoleCreate): Promise<Role> => {
    return await apiClient.post<Role>('/api/admin/roles', role);
};

export const updateRole = async (roleId: string, role: RoleUpdate): Promise<Role> => {
    return await apiClient.put<Role>(`/api/admin/roles/${roleId}`, role);
};

export const deleteRole = async (roleId: string): Promise<{ message: string }> => {
    return await apiClient.delete<{ message: string }>(`/api/admin/roles/${roleId}`);
};

export const updateUserRole = async (
    userId: string,
    roleId: string
): Promise<{ message: string; user_id: string; role_id: string; role_name: string }> => {
    return await apiClient.put<{ message: string; user_id: string; role_id: string; role_name: string }>(
        `/api/admin/users/${userId}/role`,
        { user_id: userId, role_id: roleId }
    );
};

// Admin role ID constant
export const ADMIN_ROLE_ID = 'e2d8b2c0-7b8d-4b46-88e8-cb0071467901';

