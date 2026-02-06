"""
Admin Models - Pydantic Models للسوبر أدمن
جميع النماذج الخاصة بإدارة المنصة
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, Any, List
from datetime import datetime


# ============================================================================
# Platform Settings Models
# ============================================================================

class PlatformSettingsBase(BaseModel):
    """Base model for platform settings"""
    platform_name: Optional[str] = None
    platform_name_en: Optional[str] = None
    platform_description: Optional[str] = None
    platform_logo_url: Optional[str] = None
    platform_favicon_url: Optional[str] = None
    
    # Lawyers Control
    lawyers_activation_status: Optional[Dict[str, Any]] = None
    max_lawyers_allowed: Optional[int] = None
    max_assistants_per_lawyer: Optional[int] = None
    max_clients_per_lawyer: Optional[int] = None
    max_cases_per_lawyer: Optional[int] = None
    
    # Redis
    redis_enabled: Optional[bool] = None
    redis_host: Optional[str] = None
    redis_port: Optional[int] = None
    redis_password: Optional[str] = None
    redis_db: Optional[int] = None
    redis_max_connections: Optional[int] = None
    redis_ttl_default: Optional[int] = None
    
    # AI Configuration
    ai_provider: Optional[str] = None
    ai_api_url: Optional[str] = None
    ai_api_key: Optional[str] = None
    ai_model_name: Optional[str] = None
    ai_temperature: Optional[float] = None
    ai_max_tokens: Optional[int] = None
    
    # Embedding
    embedding_provider: Optional[str] = None
    embedding_api_url: Optional[str] = None
    embedding_api_key: Optional[str] = None
    embedding_model_name: Optional[str] = None
    embedding_dimensions: Optional[int] = None
    
    # SMTP
    smtp_enabled: Optional[bool] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: Optional[str] = None
    smtp_from_name: Optional[str] = None
    smtp_use_tls: Optional[bool] = None
    
    # STT
    stt_api_url: Optional[str] = None
    stt_api_key: Optional[str] = None
    
    # SEO
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None
    seo_keywords: Optional[List[str]] = None
    seo_og_image_url: Optional[str] = None
    seo_twitter_card_type: Optional[str] = None
    
    # Social & Contact
    social_media_links: Optional[Dict[str, str]] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_whatsapp: Optional[str] = None
    contact_address: Optional[str] = None
    support_hours: Optional[str] = None
    
    # Popup
    popup_enabled: Optional[bool] = None
    popup_title: Optional[str] = None
    popup_content: Optional[str] = None
    popup_button_text: Optional[str] = None
    popup_button_link: Optional[str] = None
    popup_display_after_seconds: Optional[int] = None
    popup_display_frequency: Optional[str] = None
    
    # Alert Bar
    alert_bar_enabled: Optional[bool] = None
    alert_bar_message: Optional[str] = None
    alert_bar_type: Optional[str] = None
    alert_bar_dismissible: Optional[bool] = None
    alert_bar_link: Optional[str] = None
    alert_bar_link_text: Optional[str] = None
    
    # Maintenance Mode
    maintenance_mode_enabled: Optional[bool] = None
    maintenance_mode_message: Optional[str] = None
    maintenance_mode_allowed_ips: Optional[List[str]] = None
    maintenance_mode_estimated_end: Optional[datetime] = None
    
    # System Settings
    timezone: Optional[str] = None
    default_language: Optional[str] = None
    supported_languages: Optional[List[str]] = None
    date_format: Optional[str] = None
    time_format: Optional[str] = None
    currency: Optional[str] = None
    
    # System Limits
    max_file_upload_size_mb: Optional[int] = None
    allowed_file_types: Optional[List[str]] = None
    max_audio_recording_duration_seconds: Optional[int] = None
    
    # Security
    session_timeout_minutes: Optional[int] = None
    max_login_attempts: Optional[int] = None
    lockout_duration_minutes: Optional[int] = None
    require_2fa: Optional[bool] = None
    password_min_length: Optional[int] = None
    password_require_special_chars: Optional[bool] = None
    
    # Audit
    audit_log_retention_days: Optional[int] = None
    enable_detailed_logging: Optional[bool] = None
    
    # Additional
    additional_config: Optional[Dict[str, Any]] = None


class PlatformSettingsUpdate(PlatformSettingsBase):
    """Model for updating platform settings"""
    pass


class PlatformSettingsResponse(PlatformSettingsBase):
    """Response model including metadata"""
    id: str
    created_at: datetime
    updated_at: datetime
    updated_by: Optional[str] = None
    version: int
    
    class Config:
        from_attributes = True


# ============================================================================
# Lawyer Management Models
# ============================================================================

class LawyerActivationStatus(BaseModel):
    """Model for lawyer activation/deactivation"""
    lawyer_id: str
    is_active: bool
    reason: Optional[str] = None


class LawyerInfo(BaseModel):
    """Expanded lawyer information for Manager view"""
    id: str
    full_name: str
    email: str
    phone: Optional[str]
    role: str
    is_active: bool
    created_at: datetime
    
    # Professional Details
    specialization: Optional[str] = None
    license_number: Optional[str] = None
    lawyer_license_type: Optional[str] = None
    bar_association: Optional[str] = None
    years_of_experience: Optional[int] = None
    languages: Optional[List[str]] = None
    bio: Optional[str] = None
    
    # Office & Presence
    office_address: Optional[str] = None
    office_city: Optional[str] = None
    office_postal_code: Optional[str] = None
    website: Optional[str] = None
    linkedin_profile: Optional[str] = None
    profile_image_url: Optional[str] = None
    
    # Statistics
    total_cases: Optional[int] = 0
    total_clients: Optional[int] = 0
    total_hearings: Optional[int] = 0


class LawyersStatsResponse(BaseModel):
    """Overall lawyers statistics"""
    total_lawyers: int
    active_lawyers: int
    inactive_lawyers: int
    total_assistants: int
    total_cases_all: int
    total_clients_all: int


# ============================================================================
# Support Templates Models
# ============================================================================

class SupportTemplateBase(BaseModel):
    """Base model for support templates"""
    template_name: str
    template_category: Optional[str] = None
    template_content: str
    is_active: bool = True


class SupportTemplateCreate(SupportTemplateBase):
    """Model for creating template"""
    pass


class SupportTemplateUpdate(BaseModel):
    """Model for updating template"""
    template_name: Optional[str] = None
    template_category: Optional[str] = None
    template_content: Optional[str] = None
    is_active: Optional[bool] = None


class SupportTemplateResponse(SupportTemplateBase):
    """Response model"""
    id: str
    usage_count: int
    created_at: datetime
    created_by: Optional[str] = None
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# System Announcements Models
# ============================================================================

class SystemAnnouncementBase(BaseModel):
    """Base model for announcements"""
    title: str
    content: str
    announcement_type: str = 'info'  # 'info', 'warning', 'critical', 'feature'
    target_audience: str = 'all'  # 'all', 'lawyers', 'assistants'
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: bool = True
    is_dismissible: bool = True
    priority: int = 0


class SystemAnnouncementCreate(SystemAnnouncementBase):
    """Model for creating announcement"""
    pass


class SystemAnnouncementUpdate(BaseModel):
    """Model for updating announcement"""
    title: Optional[str] = None
    content: Optional[str] = None
    announcement_type: Optional[str] = None
    target_audience: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None
    is_dismissible: Optional[bool] = None
    priority: Optional[int] = None


class SystemAnnouncementResponse(SystemAnnouncementBase):
    """Response model"""
    id: str
    created_at: datetime
    created_by: Optional[str] = None
    
    class Config:
        from_attributes = True


# ============================================================================
# System Health Models
# ============================================================================

class SystemHealthResponse(BaseModel):
    """System health status"""
    status: str
    timestamp: datetime
    services: Dict[str, Any]
    metrics: Dict[str, Any]


class ConnectionTestRequest(BaseModel):
    """Request for testing specific connection"""
    service: str  # 'redis', 'ai', 'smtp', 'database'
    config: Optional[Dict[str, Any]] = None


class ConnectionTestResponse(BaseModel):
    """Response from connection test"""
    service: str
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None


# ============================================================================
# Role Management Models
# ============================================================================

class RolePermissions(BaseModel):
    """Permissions structure for a role"""
    read: bool = False
    create: bool = False
    update: bool = False
    delete: bool = False


class RoleBase(BaseModel):
    """Base model for roles"""
    name: str
    name_ar: str
    description: Optional[str] = None
    permissions: Dict[str, RolePermissions]
    is_active: bool = True
    is_default: bool = False


class RoleCreate(RoleBase):
    """Model for creating a role"""
    pass


class RoleUpdate(BaseModel):
    """Model for updating a role"""
    name: Optional[str] = None
    name_ar: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class RoleResponse(RoleBase):
    """Response model for roles"""
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserRoleUpdate(BaseModel):
    """Model for updating a user's role"""
    user_id: str
    role_id: str

