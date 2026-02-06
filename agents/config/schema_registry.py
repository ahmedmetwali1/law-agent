"""
Schema Registry - Metadata-Driven Database Architecture
سجل المخطط - بنية قاعدة البيانات المدفوعة بالبيانات الوصفية

This file contains the complete schema metadata for all database tables.
The AI agent uses this to understand the database structure dynamically.
Strictly synced with migrations/db.md.
"""

from typing import Dict, Any, List
from enum import Enum


class ColumnType(Enum):
    """Database column types"""
    UUID = "uuid"
    STRING = "string"
    TEXT = "text"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    TIME = "time"
    VECTOR = "vector"
    JSON = "json"
    ARRAY = "array"


class TableCategory(Enum):
    """Categories of database tables"""
    CORE = "core"
    OPERATIONAL = "operational"
    DOCUMENTS = "documents"
    KNOWLEDGE = "knowledge"
    SYSTEM = "system"


# =============================================================================
# SCHEMA METADATA REGISTRY
# سجل البيانات الوصفية للمخططات
# =============================================================================

SCHEMA_METADATA: Dict[str, Dict[str, Any]] = {
    
    # =========================================================================
    # CORE ENTITIES
    # =========================================================================
    
    "clients": {
        "category": TableCategory.CORE,
        "description": "جدول الموكلين",
        "arabic_name": "الموكلين",
        "primary_key": "id",
        "supports_vector_search": True,
        "lawyer_filtered": True,
        
        "columns": [
            {"name": "id", "type": ColumnType.UUID, "auto_generated": True},
            {"name": "lawyer_id", "type": ColumnType.UUID, "required": True, "references": "users", "security_field": True},
            {"name": "full_name", "type": ColumnType.STRING, "required": True, "searchable": True},
            {"name": "national_id", "type": ColumnType.STRING, "unique": True, "searchable": True},
            {"name": "phone", "type": ColumnType.STRING, "searchable": True},
            {"name": "email", "type": ColumnType.STRING, "searchable": True},
            {"name": "address", "type": ColumnType.TEXT, "searchable": True},
            {"name": "notes", "type": ColumnType.TEXT, "searchable": True},
            {"name": "has_power_of_attorney", "type": ColumnType.BOOLEAN, "default": False},
            {"name": "power_of_attorney_number", "type": ColumnType.STRING},
            {"name": "power_of_attorney_image_url", "type": ColumnType.TEXT},
            {"name": "name_embedding", "type": ColumnType.VECTOR},
            {"name": "created_at", "type": ColumnType.DATETIME, "auto_generated": True},
            {"name": "updated_at", "type": ColumnType.DATETIME, "auto_generated": True}
        ],
        "ai_instructions": """
        تأكد من عدم تكرار الموكلين بالبحث عن الاسم أو الهوية أولاً.
        ⚠️ ملاحظة مهمة: جدول الموكلين لا يحتوي على عمود 'status'. 
        جميع الموكلين نشطون افتراضياً. لا تستخدم filter بـ status.
        """
    },

    "opponents": {
        "category": TableCategory.CORE,
        "description": "جدول الخصوم في القضايا",
        "arabic_name": "الخصوم",
        "primary_key": "id",
        "lawyer_filtered": False,
        
        "columns": [
            {"name": "id", "type": ColumnType.UUID, "auto_generated": True},
            {"name": "case_id", "type": ColumnType.UUID, "required": True, "references": "cases"},
            {"name": "full_name", "type": ColumnType.STRING, "required": True, "searchable": True},
            {"name": "national_id", "type": ColumnType.STRING, "searchable": True},
            {"name": "capacity", "type": ColumnType.STRING, "description": "صفة الخصم (مدعي، مدعى عليه)"},
            {"name": "created_at", "type": ColumnType.DATETIME, "auto_generated": True},
            {"name": "updated_at", "type": ColumnType.DATETIME, "auto_generated": True}
        ],
        "ai_instructions": "استخدم هذا الجدول لتسجيل الخصوم (الأطراف الأخرى) في القضية."
    },
    
    "cases": {
        "category": TableCategory.CORE,
        "description": "جدول القضايا",
        "arabic_name": "القضايا",
        "primary_key": "id",
        "supports_vector_search": True,
        "lawyer_filtered": True,
        
        "columns": [
            {"name": "id", "type": ColumnType.UUID, "auto_generated": True},
            {"name": "client_id", "type": ColumnType.UUID, "required": True, "references": "clients"},
            {"name": "lawyer_id", "type": ColumnType.UUID, "references": "users", "security_field": True},
            {"name": "case_number", "type": ColumnType.STRING, "searchable": True},
            {"name": "court_name", "type": ColumnType.STRING, "searchable": True},
            {"name": "court_circuit", "type": ColumnType.STRING},
            {"name": "case_type", "type": ColumnType.STRING, "searchable": True, "enum": ["مدني", "جزائي", "تجاري", "عمالي", "أحوال شخصية", "إداري"]},
            {"name": "subject", "type": ColumnType.TEXT, "required": True, "searchable": True, "description": "عنوان القضية"},
            {"name": "status", "type": ColumnType.STRING, "default": "active"},
            {"name": "summary", "type": ColumnType.TEXT, "searchable": True},
            {"name": "ai_summary", "type": ColumnType.TEXT},
            {"name": "case_year", "type": ColumnType.STRING},
            {"name": "case_date", "type": ColumnType.DATE},
            {"name": "client_capacity", "type": ColumnType.STRING, "enum": ["مدعي", "مدعى عليه", "متهم", "مجني عليه"]},
            {"name": "verdict_number", "type": ColumnType.STRING},
            {"name": "verdict_year", "type": ColumnType.STRING},
            {"name": "verdict_date", "type": ColumnType.DATE},
            {"name": "search_embedding", "type": ColumnType.VECTOR},
            {"name": "created_at", "type": ColumnType.DATETIME, "auto_generated": True},
            {"name": "updated_at", "type": ColumnType.DATETIME, "auto_generated": True}
        ],
        "ai_instructions": "اسم عمود العنوان هو `subject`."
    },

    "hearings": {
        "category": TableCategory.OPERATIONAL,
        "description": "جدول جلسات المحكمة (Court Hearings)",
        "arabic_name": "الجلسات",
        "primary_key": "id",
        "lawyer_filtered": True,
        
        "columns": [
            {"name": "id", "type": ColumnType.UUID, "auto_generated": True},
            {"name": "case_id", "type": ColumnType.UUID, "required": True, "references": "cases"},
            {"name": "hearing_date", "type": ColumnType.DATE, "required": True},
            {"name": "hearing_time", "type": ColumnType.TIME},
            {"name": "court_room", "type": ColumnType.STRING},
            {"name": "judge_name", "type": ColumnType.STRING},
            {"name": "judge_requests", "type": ColumnType.TEXT},
            {"name": "outcome", "type": ColumnType.TEXT},
            {"name": "notes", "type": ColumnType.TEXT},
            {"name": "next_hearing_date", "type": ColumnType.DATE},
            {"name": "lawyer_id", "type": ColumnType.UUID, "security_field": True},
            {"name": "created_at", "type": ColumnType.DATETIME, "auto_generated": True},
            {"name": "updated_at", "type": ColumnType.DATETIME, "auto_generated": True}
        ],
        "ai_instructions": "هذه جلسات المحكمة فقط. لا تستخدمها لمواعيد المكتب أو الماجتماعات."
    },

    "tasks": {
        "category": TableCategory.OPERATIONAL,
        "description": "جدول المهام والتذكيرات",
        "arabic_name": "المهام",
        "primary_key": "id",
        "lawyer_filtered": True,
        
        "columns": [
            {"name": "id", "type": ColumnType.UUID, "auto_generated": True},
            {"name": "title", "type": ColumnType.STRING, "required": True, "searchable": True},
            {"name": "description", "type": ColumnType.TEXT, "searchable": True},
            {"name": "status", "type": ColumnType.STRING, "default": "pending", "enum": ["pending", "in_progress", "completed", "cancelled"]},
            {"name": "priority", "type": ColumnType.STRING, "enum": ["low", "medium", "high"]},
            {"name": "execution_date", "type": ColumnType.DATE},
            {"name": "case_id", "type": ColumnType.UUID, "references": "cases"},
            {"name": "client_id", "type": ColumnType.UUID, "references": "clients"},
            {"name": "lawyer_id", "type": ColumnType.UUID, "security_field": True},
            {"name": "user_id", "type": ColumnType.UUID, "references": "users"},
            {"name": "assigned_to", "type": ColumnType.UUID, "references": "users"},
            {"name": "assign_to_all", "type": ColumnType.BOOLEAN},
            {"name": "completed_by", "type": ColumnType.UUID, "references": "users"},
            {"name": "completed_at", "type": ColumnType.DATETIME},
            {"name": "is_ai_generated", "type": ColumnType.BOOLEAN},
            {"name": "title_embedding", "type": ColumnType.VECTOR},
            {"name": "created_at", "type": ColumnType.DATETIME, "auto_generated": True},
            {"name": "updated_at", "type": ColumnType.DATETIME, "auto_generated": True}
        ]
    },

    "documents": {
        "category": TableCategory.DOCUMENTS,
        "description": "ملفات القضايا والمستندات",
        "arabic_name": "المستندات",
        "primary_key": "id",
        "lawyer_filtered": True,
        "filter_column": "lawyer_id",
        
        "columns": [
            {"name": "id", "type": ColumnType.UUID, "auto_generated": True},
            {"name": "file_name", "type": ColumnType.STRING, "required": True, "searchable": True},
            {"name": "file_url", "type": ColumnType.TEXT},
            {"name": "case_id", "type": ColumnType.UUID, "references": "cases"},
            {"name": "client_id", "type": ColumnType.UUID, "references": "clients"},
            {"name": "document_type", "type": ColumnType.STRING},
            {"name": "raw_text", "type": ColumnType.TEXT},
            {"name": "ai_summary", "type": ColumnType.TEXT},
            {"name": "lawyer_id", "type": ColumnType.UUID, "security_field": True},
            {"name": "created_at", "type": ColumnType.DATETIME, "auto_generated": True}
        ],
        "ai_instructions": "استخدم هذا الجدول للبحث عن المستندات والأدلة."
    },

    "police_records": {
        "category": TableCategory.OPERATIONAL,
        "description": "محاضر الشرطة",
        "arabic_name": "محاضر الشرطة",
        "primary_key": "id",
        "lawyer_filtered": True,
        "filter_column": "user_id",
        
        "columns": [
            {"name": "id", "type": ColumnType.UUID, "auto_generated": True},
            {"name": "record_number", "type": ColumnType.STRING, "required": True, "searchable": True},
            {"name": "police_station", "type": ColumnType.STRING, "searchable": True},
            {"name": "subject", "type": ColumnType.TEXT, "searchable": True},
            {"name": "complainant_name", "type": ColumnType.STRING},
            {"name": "accused_name", "type": ColumnType.STRING},
            {"name": "record_year", "type": ColumnType.STRING},
            {"name": "record_type", "type": ColumnType.STRING},
            {"name": "decision", "type": ColumnType.TEXT},
            {"name": "case_id", "type": ColumnType.UUID, "references": "cases"},
            {"name": "user_id", "type": ColumnType.UUID, "required": True, "references": "users"},
            {"name": "created_at", "type": ColumnType.DATETIME, "auto_generated": True}
        ]
    },

    "legal_sources": {
        "category": TableCategory.KNOWLEDGE,
        "description": "المصادر القانونية (أنظمة، لوائح، سوابق)",
        "arabic_name": "المصادر القانونية",
        "primary_key": "id",
        "supports_vector_search": False, # Future
        
        "columns": [
            {"name": "id", "type": ColumnType.UUID, "auto_generated": True},
            {"name": "title", "type": ColumnType.TEXT, "required": True, "searchable": True},
            {"name": "doc_type", "type": ColumnType.TEXT},
            {"name": "full_content_md", "type": ColumnType.TEXT},
            {"name": "country_id", "type": ColumnType.UUID, "references": "countries"},
            {"name": "created_at", "type": ColumnType.DATETIME, "auto_generated": True}
        ]
    },

    "countries": {
        "category": TableCategory.SYSTEM,
        "description": "الدول المدعومة",
        "arabic_name": "الدول",
        "primary_key": "id",
        "columns": [
            {"name": "id", "type": ColumnType.UUID, "auto_generated": True},
            {"name": "name_ar", "type": ColumnType.TEXT, "required": True},
            {"name": "name_en", "type": ColumnType.STRING},
            {"name": "code", "type": ColumnType.STRING},
            {"name": "currency", "type": ColumnType.STRING},
            {"name": "is_active", "type": ColumnType.BOOLEAN}
        ]
    },

    "offices": {
        "category": TableCategory.SYSTEM,
        "description": "المكاتب القانونية",
        "arabic_name": "المكاتب",
        "primary_key": "id",
        "columns": [
            {"name": "id", "type": ColumnType.UUID, "auto_generated": True},
            {"name": "name", "type": ColumnType.STRING},
            {"name": "address", "type": ColumnType.TEXT},
            {"name": "phone", "type": ColumnType.STRING}
        ]
    },

    "worksheets": {
        "category": TableCategory.OPERATIONAL,
        "description": "أوراق العمل التفاعلية (Source of Truth)",
        "arabic_name": "أوراق العمل",
        "primary_key": "id",
        "columns": [
            {"name": "id", "type": ColumnType.UUID, "auto_generated": True},
            {"name": "session_id", "type": ColumnType.UUID, "required": True},
            {"name": "status", "type": ColumnType.TEXT},
            {"name": "query", "type": ColumnType.TEXT},
            {"name": "metadata", "type": ColumnType.JSON},
            {"name": "confidence_score", "type": ColumnType.FLOAT},
            {"name": "total_sources_found", "type": ColumnType.INTEGER},
            {"name": "total_iterations", "type": ColumnType.INTEGER},
            {"name": "country_id", "type": ColumnType.UUID},
            {"name": "created_at", "type": ColumnType.DATETIME, "auto_generated": True},
            {"name": "updated_at", "type": ColumnType.DATETIME, "auto_generated": True},
            {"name": "completed_at", "type": ColumnType.DATETIME}
        ]
    },

    "worksheet_sections": {
        "category": TableCategory.OPERATIONAL,
        "description": "أقسام ورقة العمل (Fact, Research, Critique)",
        "arabic_name": "أقسام ورقة العمل",
        "primary_key": "id",
        "columns": [
            {"name": "id", "type": ColumnType.UUID, "auto_generated": True},
            {"name": "worksheet_id", "type": ColumnType.UUID, "required": True, "references": "worksheets"},
            {"name": "section_type", "type": ColumnType.TEXT, "required": True},
            {"name": "title", "type": ColumnType.TEXT},
            {"name": "content", "type": ColumnType.TEXT},
            {"name": "agent_name", "type": ColumnType.TEXT},
            {"name": "thinking_trace", "type": ColumnType.TEXT},
            {"name": "sources", "type": ColumnType.JSON},
            {"name": "is_final", "type": ColumnType.BOOLEAN},
            {"name": "iteration_count", "type": ColumnType.INTEGER},
            {"name": "section_order", "type": ColumnType.INTEGER},
            {"name": "created_at", "type": ColumnType.DATETIME, "auto_generated": True},
            {"name": "updated_at", "type": ColumnType.DATETIME, "auto_generated": True}
        ]
    },
    
    "roles": {
        "category": TableCategory.SYSTEM,
        "description": "جدول الأدوار والصلاحيات",
        "arabic_name": "الأدوار",
        "primary_key": "id",
        "columns": [
            {"name": "id", "type": ColumnType.UUID, "auto_generated": True},
            {"name": "name", "type": ColumnType.STRING, "required": True},
            {"name": "name_ar", "type": ColumnType.STRING, "required": True},
            {"name": "description", "type": ColumnType.TEXT},
            {"name": "permissions", "type": ColumnType.JSON, "description": "صلاحيات الدور"},
            {"name": "is_active", "type": ColumnType.BOOLEAN},
            {"name": "is_default", "type": ColumnType.BOOLEAN},
            {"name": "created_at", "type": ColumnType.DATETIME, "auto_generated": True},
            {"name": "updated_at", "type": ColumnType.DATETIME, "auto_generated": True}
        ]
    },

    "users": {
        "category": TableCategory.SYSTEM,
        "description": "المستخدمين والمحامين والمساعدين",
        "arabic_name": "المستخدمين",
        "primary_key": "id",
        "lawyer_filtered": False,
        "columns": [
            {"name": "id", "type": ColumnType.UUID},
            {"name": "full_name", "type": ColumnType.STRING, "searchable": True},
            {"name": "email", "type": ColumnType.STRING, "required": True},
            {"name": "phone", "type": ColumnType.STRING},
            {"name": "role", "type": ColumnType.STRING, "description": "اسم الدور (محامي/مساعد)"},
            {"name": "role_id", "type": ColumnType.UUID, "references": "roles"},
            {"name": "office_id", "type": ColumnType.UUID, "description": "إذا كان مساعداً، فهذا يشير إلى المحامي الموظِّف (Boss)."},
            {"name": "specialization", "type": ColumnType.STRING},
            {"name": "license_number", "type": ColumnType.STRING},
            {"name": "is_active", "type": ColumnType.BOOLEAN},
            {"name": "created_at", "type": ColumnType.DATETIME, "auto_generated": True},
            {"name": "updated_at", "type": ColumnType.DATETIME, "auto_generated": True}
        ],
        "ai_instructions": """
        👥 إدارة المساعدين والمكاتب:
        1. **المحامي الأساسي**: يكون `office_id` هو معرف مكتبه الخاص.
        2. **المساعد (Assistant)**: 
           - يكون مربوطاً بـ `role_id` الخاص بالمساعدين.
           - حقل `office_id` يشير إلى المحامي الذي يعمل لديه (المدير).
           - عند استرجاع بيانات لمساعد، استخدم `office_id` للوصول لبيانات قضايا وموكلين المدير.
        """
    },
    

    "legal_blackboard": {
        "category": TableCategory.OPERATIONAL,
        "description": "لوحة العمليات المركزية (إدارة الحالة والنسخ)",
        "arabic_name": "لوحة القيادة",
        "primary_key": "id",
        "columns": [
            {"name": "id", "type": ColumnType.UUID, "auto_generated": True},
            {"name": "session_id", "type": ColumnType.UUID, "required": True},
            {"name": "version", "type": ColumnType.INTEGER, "default": 1, "description": "رقم الإصدار لضمان عدم ضياع التعديلات"},
            {"name": "parent_id", "type": ColumnType.UUID, "description": "معرف الإصدار السابق لعمل شجرة تعديلات"},
            {"name": "facts_snapshot", "type": ColumnType.JSON, "description": "(حصري للمحقق) الوقائع المعتمدة بصيغة هيكلية"},
            {"name": "research_data", "type": ColumnType.JSON, "description": "(حصري للباحث) الروابط، نصوص المواد، والسوابق"},
            {"name": "debate_strategy", "type": ColumnType.JSON, "description": "(حصري للمحلل والناقد) الحجج، الثغرات، وتوصيات الدفاع"},
            {"name": "drafting_plan", "type": ColumnType.JSON, "description": "(حصري لوكيل الصياغة) خطة الكتابة المتقطعة"},
            {"name": "final_output", "type": ColumnType.TEXT, "description": "النص النهائي للمذكرة"},
            {"name": "workflow_status", "type": ColumnType.JSON, "description": "أعلام الحالة لتنسيق العمل (Flags)"},
            {"name": "created_at", "type": ColumnType.DATETIME, "auto_generated": True}
        ]
    },    
    
}


def get_table_schema(table_name: str) -> Dict[str, Any]:
    """Get schema for a specific table"""
    return SCHEMA_METADATA.get(table_name)

def get_required_columns(table_name: str) -> List[str]:
    """Get list of required columns for a table"""
    schema = SCHEMA_METADATA.get(table_name)
    if not schema: return []
    return [c["name"] for c in schema["columns"] if c.get("required") and not c.get("auto_generated")]

def get_searchable_columns(table_name: str) -> List[str]:
    """Get list of searchable columns"""
    schema = SCHEMA_METADATA.get(table_name)
    if not schema: return []
    return [c["name"] for c in schema["columns"] if c.get("searchable")]

def has_vector_search(table_name: str) -> bool:
    """Check if table supports vector search"""
    schema = SCHEMA_METADATA.get(table_name)
    return schema.get("supports_vector_search", False) if schema else False
