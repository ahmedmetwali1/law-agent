"""
Schema Registry - Metadata-Driven Database Architecture
سجل المخطط - بنية قاعدة البيانات المدفوعة بالبيانات الوصفية

This file contains the complete schema metadata for all database tables.
The AI agent uses this to understand the database structure dynamically.

هذا الملف يحتوي على البيانات الوصفية الكاملة لجميع جداول قاعدة البيانات.
يستخدمه وكيل الذكاء الاصطناعي لفهم بنية قاعدة البيانات ديناميكياً.
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
    CORE = "core"  # Main entities (clients, cases)
    OPERATIONAL = "operational"  # Hearings, tasks
    DOCUMENTS = "documents"  # Files and reports
    KNOWLEDGE = "knowledge"  # Legal knowledge base
    SYSTEM = "system"  # Users, settings


# =============================================================================
# SCHEMA METADATA REGISTRY
# سجل البيانات الوصفية للمخططات
# =============================================================================

SCHEMA_METADATA: Dict[str, Dict[str, Any]] = {
    
    # =========================================================================
    # CORE ENTITIES - الكيانات الأساسية
    # =========================================================================
    
    "clients": {
        "category": TableCategory.CORE,
        "description": "جدول الموكلين - يحتوي على معلومات جميع عملاء المحامي",
        "arabic_name": "الموكلين",
        "primary_key": "id",
        "supports_vector_search": True,
        "lawyer_filtered": True,  # يجب تصفية البيانات حسب lawyer_id
        
        "columns": [
            {
                "name": "id",
                "type": ColumnType.UUID,
                "description": "معرف فريد للموكل",
                "required": False,  # Auto-generated
                "auto_generated": True
            },
            {
                "name": "lawyer_id",
                "type": ColumnType.UUID,
                "description": "معرف المحامي المالك لهذا الموكل (للأمان)",
                "required": True,
                "references": "users",
                "security_field": True
            },
            {
                "name": "full_name",
                "type": ColumnType.STRING,
                "description": "الاسم الكامل للموكل (رباعي مفضلاً)",
                "required": True,
                "searchable": True,
                "max_length": 200
            },
            {
                "name": "national_id",
                "type": ColumnType.STRING,
                "description": "رقم الهوية الوطنية أو الإقامة",
                "required": False,
                "unique": True,
                "searchable": True,
                "max_length": 20
            },
            {
                "name": "phone",
                "type": ColumnType.STRING,
                "description": "رقم الجوال الأساسي",
                "required": False,
                "searchable": True,
                "format": "phone",
                "max_length": 20
            },
            {
                "name": "email",
                "type": ColumnType.STRING,
                "description": "البريد الإلكتروني",
                "required": False,
                "searchable": True,
                "format": "email",
                "max_length": 100
            },
            {
                "name": "address",
                "type": ColumnType.TEXT,
                "description": "العنوان الكامل (مدينة، حي، شارع)",
                "required": False,
                "searchable": True
            },

            {
                "name": "notes",
                "type": ColumnType.TEXT,
                "description": "ملاحظات عامة عن الموكل",
                "required": False,
                "searchable": True
            },
            {
                "name": "has_power_of_attorney",
                "type": ColumnType.BOOLEAN,
                "description": "هل يوجد توكيل رسمي؟",
                "required": False,
                "default": False
            },
            {
                "name": "power_of_attorney_number",
                "type": ColumnType.STRING,
                "description": "رقم التوكيل إن وجد",
                "required": False,
                "max_length": 50
            },
            {
                "name": "power_of_attorney_image_url",
                "type": ColumnType.TEXT,
                "description": "رابط صورة التوكيل",
                "required": False,
                "format": "url"
            },
            {
                "name": "name_embedding",
                "type": ColumnType.VECTOR,
                "description": "Vector embedding لبيانات الموكل (للبحث الدلالي)",
                "required": False,
                "dimensions": 1024,
                "vector_for": ["full_name", "notes", "address"]
            },
            {
                "name": "created_at",
                "type": ColumnType.DATETIME,
                "description": "تاريخ إضافة الموكل",
                "required": False,
                "auto_generated": True
            },
            {
                "name": "updated_at",
                "type": ColumnType.DATETIME,
                "description": "تاريخ آخر تحديث",
                "required": False,
                "auto_generated": True
            }
        ],
        
        "relationships": {
            "cases": {
                "type": "one_to_many",
                "foreign_key": "client_id",
                "description": "جميع القضايا المرتبطة بهذا الموكل"
            },
            "police_reports": {
                "type": "one_to_many",
                "foreign_key": "client_id",
                "description": "المحاضر المرتبطة بالموكل"
            }
        },
        
        "ai_instructions": """
        عند إضافة موكل جديد:
        1. تأكد من وجود الاسم الكامل (إجباري)
        2. اطلب رقم الجوال إن لم يزوده المستخدم
        3. lawyer_id يُملأ تلقائياً من سياق المحامي الحالي
        4. لا تطلب name_embedding - سيُحسب تلقائياً
        """
    },
    
    # -------------------------------------------------------------------------
    
    "cases": {
        "category": TableCategory.CORE,
        "description": "جدول القضايا - يحتوي على جميع القضايا القانونية",
        "arabic_name": "القضايا",
        "primary_key": "id",
        "supports_vector_search": True,
        "lawyer_filtered": True,
        
        "columns": [
            {
                "name": "id",
                "type": ColumnType.UUID,
                "description": "معرف فريد للقضية",
                "required": False,
                "auto_generated": True
            },
            {
                "name": "client_id",
                "type": ColumnType.UUID,
                "description": "معرف الموكل صاحب القضية",
                "required": True,
                "references": "clients",
                "foreign_key": True
            },
            {
                "name": "lawyer_id",
                "type": ColumnType.UUID,
                "description": "معرف المحامي (المالك)",
                "required": False,
                "references": "users",
                "foreign_key": True
            },
            {
                "name": "case_number",
                "type": ColumnType.STRING,
                "description": "رقم القضية الرسمي في المحكمة",
                "required": False,
                "unique": True,
                "searchable": True,
                "max_length": 100
            },
            {
                "name": "court_name",
                "type": ColumnType.STRING,
                "description": "اسم المحكمة (مثل: محكمة الرياض الابتدائية)",
                "required": False,
                "searchable": True,
                "max_length": 200
            },
            {
                "name": "court_circuit",
                "type": ColumnType.STRING,
                "description": "الدائرة القضائية",
                "required": False,
                "max_length": 100
            },
            {
                "name": "case_type",
                "type": ColumnType.STRING,
                "description": "نوع القضية: مدني | جزائي | تجاري | عمالي | أحوال شخصية",
                "required": False,
                "enum": ["مدني", "جزائي", "تجاري", "عمالي", "أحوال شخصية", "إداري", "other"],
                "searchable": True
            },
            {
                "name": "subject",
                "type": ColumnType.TEXT,
                "description": "موضوع القضية (مختصر)",
                "required": False,
                "searchable": True
            },
            {
                "name": "status",
                "type": ColumnType.STRING,
                "description": "حالة القضية: active | closed | pending",
                "required": False,
                "enum": ["active", "closed", "pending", "نشطة", "مقفلة"],
                "default": "active"
            },
            {
                "name": "summary",
                "type": ColumnType.TEXT,
                "description": "ملخص القضية",
                "required": False,
                "searchable": True
            },
            {
                "name": "ai_summary",
                "type": ColumnType.TEXT,
                "description": "ملخص مولد بواسطة الذكاء الاصطناعي",
                "required": False
            },
            {
                "name": "case_year",
                "type": ColumnType.STRING,
                "description": "سنة القضية",
                "required": False,
                "max_length": 4
            },
            {
                "name": "case_date",
                "type": ColumnType.DATE,
                "description": "تاريخ القضية",
                "required": False
            },
            {
                "name": "client_capacity",
                "type": ColumnType.STRING,
                "description": "صفة الموكل: مدعي | مدعى عليه",
                "required": False,
                "enum": ["مدعي", "مدعى عليه"]
            },
            {
                "name": "verdict_number",
                "type": ColumnType.STRING,
                "description": "رقم الحكم",
                "required": False,
                "max_length": 50
            },
            {
                "name": "verdict_year",
                "type": ColumnType.STRING,
                "description": "سنة الحكم",
                "required": False,
                "max_length": 4
            },
            {
                "name": "verdict_date",
                "type": ColumnType.DATE,
                "description": "تاريخ الحكم",
                "required": False
            },
            {
                "name": "filing_date",
                "type": ColumnType.DATE,
                "description": "تاريخ رفع الدعوى",
                "required": False
            },
            {
                "name": "last_session_date",
                "type": ColumnType.DATE,
                "description": "تاريخ آخر جلسة",
                "required": False
            },
            {
                "name": "next_session_date",
                "type": ColumnType.DATE,
                "description": "تاريخ الجلسة القادمة",
                "required": False
            },
            {
                "name": "court_decision",
                "type": ColumnType.TEXT,
                "description": "نص الحكم إن صدر",
                "required": False,
                "searchable": True
            },
            {
                "name": "notes",
                "type": ColumnType.TEXT,
                "description": "ملاحظات عامة عن القضية",
                "required": False,
                "searchable": True
            },
            {
                "name": "search_embedding",
                "type": ColumnType.VECTOR,
                "description": "Vector embedding للقضية",
                "required": False,
                "dimensions": 1024,
                "vector_for": ["subject", "summary", "ai_summary"]
            },
            {
                "name": "created_at",
                "type": ColumnType.DATETIME,
                "description": "تاريخ إضافة القضية للنظام",
                "required": False,
                "auto_generated": True
            },
            {
                "name": "updated_at",
                "type": ColumnType.DATETIME,
                "description": "تاريخ آخر تحديث",
                "required": False,
                "auto_generated": True
            }
        ],
        
        "relationships": {
            "client": {
                "type": "many_to_one",
                "references": "clients",
                "description": "الموكل صاحب القضية"
            },
            "hearings": {
                "type": "one_to_many",
                "foreign_key": "case_id",
                "description": "جميع الجلسات المرتبطة بالقضية"
            },
            "opponents": {
                "type": "one_to_many",
                "foreign_key": "case_id",
                "description": "الخصوم في القضية"
            },
            "documents": {
                "type": "one_to_many",
                "foreign_key": "case_id",
                "description": "المستندات المرفقة"
            },
            "tasks": {
                "type": "one_to_many",
                "foreign_key": "related_case_id",
                "description": "المهام المرتبطة بالقضية"
            }
        },
        
        "ai_instructions": """
        عند إضافة قضية جديدة:
        1. تأكد من ربطها بموكل موجود (client_id إجباري)
        2. إذا لم يذكر المستخدم رقم القضية، اتركها فارغة
        3. حدد case_type من القائمة
        4. client_capacity مهم (مدعي أم مدعى عليه)
        5. status افتراضياً = "active"
        6. lawyer_id يُملأ تلقائياً من السياق
        """
    },
    
    # =========================================================================
    # OPERATIONAL TABLES - الجداول التشغيلية
    # =========================================================================
    
    "hearings": {
        "category": TableCategory.OPERATIONAL,
        "description": "جدول الجلسات - جميع جلسات المحكمة المقررة والماضية",
        "arabic_name": "الجلسات",
        "primary_key": "id",
        "supports_vector_search": False,
        "lawyer_filtered": True,  # Protected: Filter by lawyer_id
        
        "columns": [
            {
                "name": "id",
                "type": ColumnType.UUID,
                "description": "معرف فريد للجلسة",
                "required": False,
                "auto_generated": True
            },
            {
                "name": "case_id",
                "type": ColumnType.UUID,
                "description": "معرف القضية المرتبطة",
                "required": True,
                "references": "cases",
                "foreign_key": True
            },
            {
                "name": "hearing_date",
                "type": ColumnType.DATE,
                "description": "تاريخ الجلسة",
                "required": True,
                "searchable": True
            },
            {
                "name": "hearing_time",
                "type": ColumnType.TIME,
                "description": "وقت الجلسة (اختياري)",
                "required": False
            },
            {
                "name": "court_room",
                "type": ColumnType.STRING,
                "description": "رقم القاعة أو الدائرة",
                "required": False,
                "max_length": 50
            },
            {
                "name": "judge_name",
                "type": ColumnType.STRING,
                "description": "اسم القاضي",
                "required": False,
                "max_length": 100
            },
            {
                "name": "lawyer_id",
                "type": ColumnType.UUID,
                "description": "معرف المحامي",
                "required": False,
                "references": "users"
            },
            {
                "name": "judge_requests",
                "type": ColumnType.TEXT,
                "description": "طلبات القاضي في الجلسة",
                "required": False
            },
            {
                "name": "notes",
                "type": ColumnType.TEXT,
                "description": "ملاحظات عن الجلسة",
                "required": False
            },
            {
                "name": "outcome",
                "type": ColumnType.TEXT,
                "description": "نتيجة الجلسة",
                "required": False,
                "searchable": True
            },
            {
                "name": "next_hearing_date",
                "type": ColumnType.DATE,
                "description": "تاريخ الجلسة التالية",
                "required": False
            },
            {
                "name": "created_at",
                "type": ColumnType.DATETIME,
                "description": "تاريخ الإضافة",
                "required": False,
                "auto_generated": True
            },
            {
                "name": "updated_at",
                "type": ColumnType.DATETIME,
                "description": "تاريخ آخر تحديث",
                "required": False,
                "auto_generated": True
            }
        ],
        
        "relationships": {
            "case": {
                "type": "many_to_one",
                "references": "cases",
                "description": "القضية المرتبطة بالجلسة"
            }
        },
        
        "ai_instructions": """
        عند إضافة جلسة:
        1. case_id و hearing_date إجباريان
        2. إذا لم يحدد المستخدم الوقت، اتركه فارغاً
        3. سجل outcome و judge_requests بعد الجلسة
        """
    },
    
    # -------------------------------------------------------------------------
    
    "tasks": {
        "category": TableCategory.OPERATIONAL,
        "description": "جدول المهام - تذكيرات ومهام قانونية",
        "arabic_name": "المهام",
        "primary_key": "id",
        "supports_vector_search": True,
        "lawyer_filtered": True,
        
        "columns": [
            {
                "name": "id",
                "type": ColumnType.UUID,
                "description": "معرف فريد للمهمة",
                "required": False,
                "auto_generated": True
            },
            {
                "name": "lawyer_id",
                "type": ColumnType.UUID,
                "description": "معرف المحامي المسؤول",
                "required": True,
                "references": "users",
                "security_field": True
            },
            {
                "name": "title",
                "type": ColumnType.STRING,
                "description": "عنوان المهمة",
                "required": True,
                "searchable": True,
                "max_length": 200
            },
            {
                "name": "description",
                "type": ColumnType.TEXT,
                "description": "تفاصيل المهمة",
                "required": False,
                "searchable": True
            },
            {
                "name": "case_id",
                "type": ColumnType.UUID,
                "description": "القضية المرتبطة (إن وجدت)",
                "required": False,
                "references": "cases"
            },
            {
                "name": "user_id",
                "type": ColumnType.UUID,
                "description": "المستخدم المرتبط بالمهمة",
                "required": False,
                "references": "users"
            },
            {
                "name": "client_id",
                "type": ColumnType.UUID,
                "description": "الموكل المرتبط",
                "required": False,
                "references": "clients"
            },
            {
                "name": "priority",
                "type": ColumnType.STRING,
                "description": "الأولوية: عالية | متوسطة | منخفضة",
                "required": False,
                "enum": ["عالية", "متوسطة", "منخفضة"],
                "default": "medium"
            },
            {
                "name": "status",
                "type": ColumnType.STRING,
                "description": "الحالة: pending | in_progress | completed",
                "required": False,
                "enum": ["pending", "in_progress", "completed", "قيد التنفيذ", "مكتملة"],
                "default": "pending"
            },
            {
                "name": "is_ai_generated",
                "type": ColumnType.BOOLEAN,
                "description": "هل تم إنشاء المهمة بواسطة الذكاء الاصطناعي؟",
                "required": False,
                "default": False
            },
            {
                "name": "execution_date",
                "type": ColumnType.DATE,
                "description": "تاريخ التنفيذ",
                "required": False
            },
            {
                "name": "assigned_to",
                "type": ColumnType.UUID,
                "description": "المستخدم المسندة إليه المهمة",
                "required": False,
                "references": "users"
            },
            {
                "name": "assign_to_all",
                "type": ColumnType.BOOLEAN,
                "description": "إسناد للجميع؟",
                "required": False,
                "default": False
            },
            {
                "name": "completed_by",
                "type": ColumnType.UUID,
                "description": "المستخدم الذي أكمل المهمة",
                "required": False,
                "references": "users"
            },
            {
                "name": "title_embedding",
                "type": ColumnType.VECTOR,
                "description": "Vector embedding لعنوان المهمة",
                "required": False,
                "dimensions": 1024,
                "vector_for": ["title", "description"]
            },
            {
                "name": "completed_at",
                "type": ColumnType.DATETIME,
                "description": "تاريخ الإكمال",
                "required": False
            },
            {
                "name": "created_at",
                "type": ColumnType.DATETIME,
                "description": "تاريخ الإنشاء",
                "required": False,
                "auto_generated": True
            },
            {
                "name": "updated_at",
                "type": ColumnType.DATETIME,
                "description": "تاريخ آخر تحديث",
                "required": False,
                "auto_generated": True
            }
        ],
        
        "relationships": {
            "case": {
                "type": "many_to_one",
                "references": "cases",
                "description": "القضية المرتبطة"
            },
            "assignee": {
                "type": "many_to_one",
                "references": "users",
                "description": "الموظف المسند إليه"
            },
            "client": {
                "type": "many_to_one",
                "required": False,
                "references": "clients"
            }
        },
        
        "ai_instructions": """
        عند التعامل مع المهام:
        1. دائماً اربط المهمة بمحامي (lawyer_id)
        2. استخدم case_id إذا كانت المهمة مرتبطة بقضية
        3. المهام "assign_to_all" يراها جميع المساعدين
        """
    },

    # -------------------------------------------------------------------------
    
    "police_records": {
        "category": TableCategory.OPERATIONAL,
        "description": "سجل محاضر الشرطة والشكاوى",
        "arabic_name": "محاضر الشرطة",
        "primary_key": "id",
        "supports_vector_search": True,
        "lawyer_filtered": True,  # ✅ SECURITY: Restricted access
        "filter_column": "user_id",  # ✅ FILTER: Map to user_id instead of default lawyer_id
        
        "columns": [
            {
                "name": "id",
                "type": ColumnType.UUID,
                "description": "معرف المحضر",
                "required": False,
                "auto_generated": True
            },
            {
                "name": "record_number",
                "type": ColumnType.STRING,
                "description": "رقم المحضر",
                "required": True,
                "searchable": True
            },
            {
                "name": "record_year",
                "type": ColumnType.STRING,
                "description": "سنة المحضر",
                "required": False
            },
            {
                "name": "record_type",
                "type": ColumnType.STRING,
                "description": "نوع المحضر (إداري، جنح، الخ)",
                "required": False
            },
            {
                "name": "police_station",
                "type": ColumnType.STRING,
                "description": "قسم الشرطة",
                "required": False,
                "searchable": True
            },
            {
                "name": "complainant_name",
                "type": ColumnType.STRING,
                "description": "اسم الشاكي",
                "required": False,
                "searchable": True
            },
            {
                "name": "accused_name",
                "type": ColumnType.STRING,
                "description": "اسم المشكو في حقه",
                "required": False,
                "searchable": True
            },
            {
                "name": "subject",
                "type": ColumnType.TEXT,
                "description": "موضوع المحضر",
                "required": False,
                "searchable": True
            },
            {
                "name": "decision",
                "type": ColumnType.TEXT,
                "description": "قرار النيابة/الشرطة",
                "required": False
            },
            {
                "name": "case_id",
                "type": ColumnType.UUID,
                "description": "القضية المرتبطة",
                "references": "cases",
                "required": False
            },
            {
                "name": "user_id",  # ✅ Reverted to user_id to match DB schema
                "type": ColumnType.UUID,
                "description": "المحامي المالك",
                "references": "users",
                "required": True
            },
            {
                "name": "file_url",
                "type": ColumnType.STRING,
                "description": "رابط الملف المرفق",
                "required": False
            },
            {
                "name": "ai_analysis",
                "type": ColumnType.TEXT,
                "description": "تحليل الذكاء الاصطناعي",
                "required": False
            }
        ],
        
        "ai_instructions": """
        عند التعامل مع محاضر الشرطة:
        1. البحث عن المحاضر يقتصر تلقائياً على المحاضر الخاصة بالمحامي الحالي.
        2. عند إضافة محضر، سيتم ربطه بـ lawyer_id تلقائياً.
        """
    },
    
    # =========================================================================
    # DOCUMENTS & REPORTS - المستندات والمحاضر
    # =========================================================================
    
    "documents": {
        "category": TableCategory.DOCUMENTS,
        "description": "جدول المستندات - ملفات مرفقة بالقضايا",
        "arabic_name": "المستندات",
        "primary_key": "id",
        "supports_vector_search": True,
        "lawyer_filtered": False,
        
        "columns": [
            {
                "name": "id",
                "type": ColumnType.UUID,
                "description": "معرف فريد للمستند",
                "required": False,
                "auto_generated": True
            },
            {
                "name": "case_id",
                "type": ColumnType.UUID,
                "description": "القضية المرتبطة",
                "required": True,
                "references": "cases",
                "foreign_key": True
            },
            {
                "name": "file_name",
                "type": ColumnType.STRING,
                "description": "اسم الملف",
                "required": True,
                "searchable": True,
                "max_length": 255
            },
            {
                "name": "file_path",
                "type": ColumnType.STRING,
                "description": "مسار الملف في التخزين",
                "required": True,
                "max_length": 500
            },
            {
                "name": "file_type",
                "type": ColumnType.STRING,
                "description": "نوع الملف: PDF | Image | Word | Other",
                "required": False,
                "enum": ["PDF", "Image", "Word", "Excel", "Other"]
            },
            {
                "name": "document_category",
                "type": ColumnType.STRING,
                "description": "تصنيف المستند: عقد | صك | شهادة | مرافعة | حكم",
                "required": False,
                "enum": ["عقد", "صك", "شهادة", "مرافعة", "حكم", "other"]
            },
            {
                "name": "extracted_text",
                "type": ColumnType.TEXT,
                "description": "النص المستخرج من الملف (OCR)",
                "required": False,
                "searchable": True
            },
            {
                "name": "file_size_bytes",
                "type": ColumnType.INTEGER,
                "description": "حجم الملف بالبايتات",
                "required": False
            },
            {
                "name": "embedding",
                "type": ColumnType.VECTOR,
                "description": "Vector embedding للنص المستخرج",
                "required": False,
                "dimensions": 1024,
                "vector_for": ["extracted_text"]
            },
            {
                "name": "uploaded_at",
                "type": ColumnType.DATETIME,
                "description": "تاريخ الرفع",
                "required": False,
                "auto_generated": True
            }
        ],
        
        "relationships": {
            "case": {
                "type": "many_to_one",
                "references": "cases",
                "description": "القضية المرتبطة"
            }
        },
        
        "ai_instructions": """
عند رفع مستند:
1. case_id, file_name, file_path إجبارية
2. إذا تم استخراج نص (OCR)، سجله في extracted_text
3. حدد document_category لتسهيل التصنيف
        """
    },
    
    # -------------------------------------------------------------------------
    
    "opponents": {
        "category": TableCategory.CORE,
        "description": "جدول الخصوم - الطرف الآخر في القضية",
        "arabic_name": "الخصوم",
        "primary_key": "id",
        "supports_vector_search": False,
        "lawyer_filtered": False,
        
        "columns": [
            {
                "name": "id",
                "type": ColumnType.UUID,
                "description": "معرف فريد للخصم",
                "required": False,
                "auto_generated": True
            },
            {
                "name": "case_id",
                "type": ColumnType.UUID,
                "description": "القضية المرتبطة",
                "required": True,
                "references": "cases",
                "foreign_key": True
            },
            {
                "name": "full_name",
                "type": ColumnType.STRING,
                "description": "اسم الخصم الكامل",
                "required": True,
                "searchable": True,
                "max_length": 200
            },
            {
                "name": "national_id",
                "type": ColumnType.STRING,
                "description": "رقم هوية الخصم",
                "required": False,
                "max_length": 20
            },
            {
                "name": "capacity",
                "type": ColumnType.STRING,
                "description": "صفة الخصم: مدعي | مدعى عليه",
                "required": False,
                "enum": ["مدعي", "مدعى عليه"]
            },
            {
                "name": "created_at",
                "type": ColumnType.DATETIME,
                "description": "تاريخ الإضافة",
                "required": False,
                "auto_generated": True
            },
            {
                "name": "updated_at",
                "type": ColumnType.DATETIME,
                "description": "تاريخ آخر تحديث",
                "required": False,
                "auto_generated": True
            }
        ],
        
        "relationships": {
            "case": {
                "type": "many_to_one",
                "references": "cases",
                "description": "القضية المرتبطة"
            }
        },
        
        "ai_instructions": """
        عند إضافة خصم:
        1. case_id و full_name إجباريان
        2. يمكن أن يكون للقضية عدة خصوم
        """
    },
    
    # -------------------------------------------------------------------------
    
    "police_reports": {
        "category": TableCategory.DOCUMENTS,
        "description": "جدول محاضر الشرطة - محاضر رسمية",
        "arabic_name": "المحاضر",
        "primary_key": "id",
        "supports_vector_search": True,
        "lawyer_filtered": False,
        
        "columns": [
            {
                "name": "id",
                "type": ColumnType.UUID,
                "description": "معرف فريد للمحضر",
                "required": False,
                "auto_generated": True
            },
            {
                "name": "client_id",
                "type": ColumnType.UUID,
                "description": "الموكل المرتبط",
                "required": True,
                "references": "clients",
                "foreign_key": True
            },
            {
                "name": "report_number",
                "type": ColumnType.STRING,
                "description": "رقم المحضر الرسمي",
                "required": True,
                "unique": True,
                "searchable": True,
                "max_length": 100
            },
            {
                "name": "police_station",
                "type": ColumnType.STRING,
                "description": "اسم المركز أو الشرطة",
                "required": False,
                "searchable": True,
                "max_length": 200
            },
            {
                "name": "report_date",
                "type": ColumnType.DATE,
                "description": "تاريخ المحضر",
                "required": False
            },
            {
                "name": "incident_type",
                "type": ColumnType.STRING,
                "description": "نوع الحادث: سرقة | اعتداء | احتيال | حادث مروري | other",
                "required": False,
                "enum": ["سرقة", "اعتداء", "احتيال", "حادث مروري", "other"]
            },
            {
                "name": "description",
                "type": ColumnType.TEXT,
                "description": "وصف الحادث",
                "required": False,
                "searchable": True
            },
            {
                "name": "status",
                "type": ColumnType.STRING,
                "description": "حالة المحضر: قيد التحقيق | محال للنيابة | مقفل",
                "required": False,
                "enum": ["قيد التحقيق", "محال للنيابة", "مقفل", "pending"],
                "default": "pending"
            },
            {
                "name": "file_path",
                "type": ColumnType.STRING,
                "description": "مسار ملف المحضر",
                "required": False,
                "max_length": 500
            },
            {
                "name": "embedding",
                "type": ColumnType.VECTOR,
                "description": "Vector embedding للمحضر",
                "required": False,
                "dimensions": 1024,
                "vector_for": ["description"]
            },
            {
                "name": "created_at",
                "type": ColumnType.DATETIME,
                "description": "تاريخ الإضافة",
                "required": False,
                "auto_generated": True
            }
        ],
        
        "relationships": {
            "client": {
                "type": "many_to_one",
                "references": "clients",
                "description": "الموكل المرتبط"
            }
        },
        
        "ai_instructions": """
عند إضافة محضر:
1. client_id و report_number إجباريان
2. سجل تفاصيل الحادث في description
3. حدد incident_type بدقة
        """
    },
    
    # =========================================================================
    # SYSTEM TABLES - جداول النظام
    # =========================================================================
    
    # =========================================================================
    # REFERENCE TABLES - الجداول المرجعية
    # =========================================================================
    
    "countries": {
        "category": TableCategory.SYSTEM,
        "description": "جدول الدول - قائمة الدول المدعومة",
        "arabic_name": "الدول",
        "primary_key": "id",
        "supports_vector_search": False,
        "lawyer_filtered": False,
        
        "columns": [
            {
                "name": "id",
                "type": ColumnType.UUID,
                "description": "معرف فريد للدولة",
                "required": False,
                "auto_generated": True
            },
            {
                "name": "name_ar",
                "type": ColumnType.STRING,
                "description": "اسم الدولة بالعربي",
                "required": True,
                "max_length": 100
            },
            {
                "name": "name_en",
                "type": ColumnType.STRING,
                "description": "اسم الدولة بالإنجليزي",
                "required": True,
                "max_length": 100
            },
            {
                "name": "code",
                "type": ColumnType.STRING,
                "description": "كود الدولة (SA, AE, EG)",
                "required": True,
                "unique": True,
                "max_length": 3
            },
            {
                "name": "phone_prefix",
                "type": ColumnType.STRING,
                "description": "كود الاتصال (+966, +971)",
                "required": False,
                "max_length": 10
            },
            {
                "name": "currency",
                "type": ColumnType.STRING,
                "description": "العملة (SAR, AED, EGP)",
                "required": False,
                "max_length": 3
            },
            {
                "name": "flag_emoji",
                "type": ColumnType.STRING,
                "description": "Emoji علم الدولة",
                "required": False,
                "max_length": 10
            },
            {
                "name": "is_active",
                "type": ColumnType.BOOLEAN,
                "description": "هل الدولة مفعلة؟",
                "required": False,
                "default": True
            },
            {
                "name": "created_at",
                "type": ColumnType.DATETIME,
                "description": "تاريخ الإضافة",
                "required": False,
                "auto_generated": True
            },
            {
                "name": "updated_at",
                "type": ColumnType.DATETIME,
                "description": "تاريخ آخر تحديث",
                "required": False,
                "auto_generated": True
            }
        ],
        
        "ai_instructions": """
هذا جدول مرجعي للدول. البيانات ثابتة ويتم تحديثها من قبل المدراء فقط.
        """
    },
    
    # -------------------------------------------------------------------------
    
    "roles": {
        "category": TableCategory.SYSTEM,
        "description": "جدول الصلاحيات - أدوار المستخدمين في النظام",
        "arabic_name": "الصلاحيات",
        "primary_key": "id",
        "supports_vector_search": False,
        "lawyer_filtered": False,
        
        "columns": [
            {
                "name": "id",
                "type": ColumnType.UUID,
                "description": "معرف فريد للصلاحية",
                "required": False,
                "auto_generated": True
            },
            {
                "name": "name",
                "type": ColumnType.STRING,
                "description": "اسم الصلاحية بالإنجليزي (lawyer, assistant, admin)",
                "required": True,
                "unique": True,
                "max_length": 50
            },
            {
                "name": "name_ar",
                "type": ColumnType.STRING,
                "description": "اسم الصلاحية بالعربي",
                "required": True,
                "max_length": 50
            },
            {
                "name": "description",
                "type": ColumnType.TEXT,
                "description": "وصف الصلاحية ومهامها",
                "required": False
            },
            {
                "name": "permissions",
                "type": ColumnType.JSON,
                "description": "قائمة الصلاحيات التفصيلية (JSON)",
                "required": False
            },
            {
                "name": "is_active",
                "type": ColumnType.BOOLEAN,
                "description": "هل الصلاحية مفعلة؟",
                "required": False,
                "default": True
            },
            {
                "name": "is_default",
                "type": ColumnType.BOOLEAN,
                "description": "هل هي الصلاحية الافتراضية عند التسجيل؟",
                "required": False,
                "default": False
            },
            {
                "name": "created_at",
                "type": ColumnType.DATETIME,
                "description": "تاريخ الإنشاء",
                "required": False,
                "auto_generated": True
            },
            {
                "name": "updated_at",
                "type": ColumnType.DATETIME,
                "description": "تاريخ آخر تحديث",
                "required": False,
                "auto_generated": True
            }
        ],
        
        "ai_instructions": """
جدول الصلاحيات يحدد أدوار المستخدمين.
الصلاحية الافتراضية (is_default=true) هي "محامي" (lawyer).
        """
    },
    
    # -------------------------------------------------------------------------
    
    "users": {
        "category": TableCategory.CORE,
        "description": "جدول المستخدمين - المحامين والمساعدين والمدراء",
        "arabic_name": "المستخدمين",
        "primary_key": "id",
        "supports_vector_search": False,
        "lawyer_filtered": False,
        
        "columns": [
            {
                "name": "id",
                "type": ColumnType.UUID,
                "description": "معرف فريد للمستخدم",
                "required": False,
                "auto_generated": True
            },
            {
                "name": "email",
                "type": ColumnType.STRING,
                "description": "البريد الإلكتروني (للدخول)",
                "required": True,
                "unique": True,
                "format": "email",
                "max_length": 100
            },
            {
                "name": "password_hash",
                "type": ColumnType.STRING,
                "description": "كلمة المرور المشفرة",
                "required": True,
                "sensitive": True
            },
            {
                "name": "full_name",
                "type": ColumnType.STRING,
                "description": "الاسم الكامل",
                "required": True,
                "max_length": 200
            },
            {
                "name": "phone",
                "type": ColumnType.STRING,
                "description": "رقم الجوال",
                "required": False,
                "max_length": 20
            },
            
            # Foreign Keys - العلاقات
            {
                "name": "country_id",
                "type": ColumnType.UUID,
                "description": "الدولة التي ينتمي إليها المستخدم",
                "required": True,
                "references": "countries",
                "foreign_key": True
            },
            {
                "name": "role",
                "type": ColumnType.STRING,
                "description": "دور المستخدم (assistant)",
                "required": False,
                "default": "assistant",
                "max_length": 50
            },
            {
                "name": "role_id",
                "type": ColumnType.UUID,
                "description": "صلاحية المستخدم",
                "required": False,
                "default": "e3fedef1-5387-4d6d-a90b-6bb8ed45e5f2",
                "references": "roles",
                "foreign_key": True
            },
            {
                "name": "office_id",
                "type": ColumnType.UUID,
                "description": "المكتب التابع له (للمساعدين)",
                "required": False,
                "references": "users",
                "foreign_key": True
            },
            
            # Professional Information - المعلومات المهنية
            {
                "name": "specialization",
                "type": ColumnType.STRING,
                "description": "التخصص القانوني",
                "required": False,
                "max_length": 200
            },
            {
                "name": "license_number",
                "type": ColumnType.STRING,
                "description": "رقم الترخيص",
                "required": False,
                "max_length": 50
            },
            {
                "name": "lawyer_license_type",
                "type": ColumnType.STRING,
                "description": "نوع الترخيص: ممارس | محاضر | استشاري",
                "required": False,
                "enum": ["ممارس", "محاضر", "استشاري", "other"],
                "max_length": 50
            },
            {
                "name": "bar_association",
                "type": ColumnType.STRING,
                "description": "الهيئة المانحة للترخيص (مثل: الهيئة السعودية للمحامين)",
                "required": False,
                "max_length": 200
            },
            {
                "name": "years_of_experience",
                "type": ColumnType.INTEGER,
                "description": "سنوات الخبرة",
                "required": False
            },
            {
                "name": "languages",
                "type": ColumnType.TEXT,
                "description": "اللغات التي يتحدثها",
                "required": False
            },
            
            # Contact & Social - التواصل
            {
                "name": "website",
                "type": ColumnType.STRING,
                "description": "الموقع الإلكتروني",
                "required": False,
                "format": "url",
                "max_length": 200
            },
            {
                "name": "linkedin_profile",
                "type": ColumnType.STRING,
                "description": "رابط LinkedIn",
                "required": False,
                "format": "url",
                "max_length": 200
            },
            {
                "name": "bio",
                "type": ColumnType.TEXT,
                "description": "نبذة تعريفية عن المحامي",
                "required": False
            },
            {
                "name": "profile_image_url",
                "type": ColumnType.STRING,
                "description": "رابط الصورة الشخصية",
                "required": False,
                "format": "url",
                "max_length": 500
            },
            
            # Office Details - تفاصيل المكتب
            {
                "name": "office_address",
                "type": ColumnType.TEXT,
                "description": "عنوان المكتب بالتفصيل",
                "required": False
            },
            {
                "name": "office_city",
                "type": ColumnType.STRING,
                "description": "مدينة المكتب",
                "required": False,
                "max_length": 100
            },
            {
                "name": "office_postal_code",
                "type": ColumnType.STRING,
                "description": "الرمز البريدي",
                "required": False,
                "max_length": 20
            },
            {
                "name": "business_hours",
                "type": ColumnType.JSON,
                "description": "أوقات العمل (JSON)",
                "required": False
            },
            
            # System Settings - إعدادات النظام
            {
                "name": "timezone",
                "type": ColumnType.STRING,
                "description": "المنطقة الزمنية (مثل: Asia/Riyadh)",
                "required": False,
                "max_length": 50,
                "default": "Asia/Riyadh"
            },
            {
                "name": "notification_preferences",
                "type": ColumnType.JSON,
                "description": "تفضيلات الإشعارات (JSON)",
                "required": False
            },
            {
                "name": "is_active",
                "type": ColumnType.BOOLEAN,
                "description": "هل الحساب نشط؟",
                "required": False,
                "default": True
            },
            {
                "name": "last_login",
                "type": ColumnType.DATETIME,
                "description": "آخر تسجيل دخول",
                "required": False
            },
            {
                "name": "created_at",
                "type": ColumnType.DATETIME,
                "description": "تاريخ الإنشاء",
                "required": False,
                "auto_generated": True
            },
            {
                "name": "updated_at",
                "type": ColumnType.DATETIME,
                "description": "تاريخ آخر تحديث",
                "required": False,
                "auto_generated": True
            }
        ],
        
        "relationships": {
            "country": {
                "type": "many_to_one",
                "references": "countries",
                "description": "الدولة التي ينتمي إليها المستخدم"
            },
            "role": {
                "type": "many_to_one",
                "references": "roles",
                "description": "صلاحية المستخدم"
            },
            "clients": {
                "type": "one_to_many",
                "foreign_key": "lawyer_id",
                "description": "جميع موكلي المحامي"
            },
            "tasks": {
                "type": "one_to_many",
                "foreign_key": "lawyer_id",
                "description": "مهام المحامي"
            }
        },
        
        "ai_instructions": """
        ⚠️ CRITICAL SECURITY RULES - READ CAREFULLY:
        1. YOU ARE RESTRICTED from searching or listing this table globally.
        2. EXCEPTION: You MAY list your own assistants by filtering `office_id` = [Your ID].
        3. YOU ARE RESTRICTED from deleting any records.
        4. MODIFICATION:
           - You may ONLY update the profile of the current lawyer (yourself/context) or your assistants.
           - FORBIDDEN: You cannot change 'email' or 'password_hash' for the lawyer.
        5. CREATION (Assistants Only):
           - You can create new assistants.
           - MANDATORY: Set 'office_id' = [Current Lawyer ID].
           - MANDATORY: Set 'role_id' = 'e3fedef1-5387-4d6d-a90b-6bb8ed45e5f2'.
           - MANDATORY: Set 'role' = 'assistant'.
        
        DATA STRUCTURE & LINKING:
        - Lawyers are root users (office_id is NULL).
        - Assistants are linked users where `office_id` == Lawyer's ID.
        - To find/count assistants: query `users` where `office_id` is matched.
        """

    },
    
    "audit_logs": {
        "category": TableCategory.OPERATIONAL,
        "description": "سجل التدقيق - يسجل جميع العمليات التي تتم على النظام",
        "arabic_name": "سجل العمليات",
        "primary_key": "id",
        "supports_vector_search": False,
        "lawyer_filtered": True,  # Filter (via lawyer_id column assumption, though schema request has lawyer_id)
        
        "columns": [
            {
                "name": "id",
                "type": ColumnType.UUID,
                "description": "معرف السجل",
                "required": False,
                "auto_generated": True
            },
            {
                "name": "action",
                "type": ColumnType.STRING,
                "description": "نوع العملية (INSERT, UPDATE, DELETE)",
                "required": True,
                "max_length": 50
            },
            {
                "name": "table_name",
                "type": ColumnType.STRING,
                "description": "اسم الجدول المتأثر",
                "required": True,
                "max_length": 100
            },
            {
                "name": "record_id",
                "type": ColumnType.UUID,
                "description": "معرف السجل المتأثر",
                "required": False
            },
            {
                "name": "user_id",
                "type": ColumnType.UUID,
                "description": "معرف المستخدم الذي قام بالعملية",
                "required": False,
                "references": "users"
            },
            {
                "name": "user_name",
                "type": ColumnType.STRING,
                "description": "اسم المستخدم",
                "required": False,
                "max_length": 200
            },
            {
                "name": "user_role",
                "type": ColumnType.STRING,
                "description": "دور المستخدم",
                "required": False,
                "max_length": 50
            },
            {
                "name": "changes",
                "type": ColumnType.JSON,
                "description": "التغييرات (old_values, new_values)",
                "required": False
            },
            {
                "name": "description",
                "type": ColumnType.TEXT,
                "description": "وصف العملية للنظام",
                "required": False
            },
            {
                "name": "created_at",
                "type": ColumnType.DATETIME,
                "description": "تاريخ العملية",
                "required": False,
                "auto_generated": True
            },
            {
                "name": "lawyer_id",
                "type": ColumnType.UUID,
                "description": "معرف المحامي (للتصفية)",
                "required": False,
                "references": "users"
            }
        ],
        
        "ai_instructions": """
        READ-ONLY TABLE. INTEGRITY CRITICAL.
        
        REPORTING RULES (STRICT):
        1. TRANSLATE ALL VALUES: Never show English status (e.g., 'pending' -> 'قيد الانتظار', 'completed' -> 'مكتملة').
        2. NO UUIDS: Never display raw IDs. Always JOIN with related tables (cases, tasks, clients) to get the Name/Title.
        3. HUMAN FRIENDLY: Describe the event generally (e.g., 'تم تحديث قضية النزاع التجاري' instead of technical details).
        4. INTEGRITY: You are STRICTLY FORBIDDEN from updating, deleting, or manually inserting into this table.
        """
    }
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_table_schema(table_name: str) -> Dict[str, Any]:
    """
    Get schema for a specific table
    
    Args:
        table_name: Name of the table
        
    Returns:
        Schema metadata dictionary
    """
    return SCHEMA_METADATA.get(table_name)


def get_required_columns(table_name: str) -> List[str]:
    """
    Get list of required columns for a table
    
    Args:
        table_name: Name of the table
        
    Returns:
        List of required column names
    """
    schema = get_table_schema(table_name)
    if not schema:
        return []
    
    return [
        col["name"] 
        for col in schema.get("columns", []) 
        if col.get("required", False) and not col.get("auto_generated", False)
    ]


def get_searchable_columns(table_name: str) -> List[str]:
    """
    Get list of searchable columns
    
    Args:
        table_name: Name of the table
        
    Returns:
        List of searchable column names
    """
    schema = get_table_schema(table_name)
    if not schema:
        return []
    
    return [
        col["name"] 
        for col in schema.get("columns", []) 
        if col.get("searchable", False)
    ]


def has_vector_search(table_name: str) -> bool:
    """
    Check if table supports vector search
    
    Args:
        table_name: Name of the table
        
    Returns:
        True if supports vector search
    """
    schema = get_table_schema(table_name)
    return schema.get("supports_vector_search", False) if schema else False


def get_all_tables() -> List[str]:
    """Get list of all table names"""
    return list(SCHEMA_METADATA.keys())


def get_tables_by_category(category: TableCategory) -> List[str]:
    """
    Get tables filtered by category
    
    Args:
        category: Table category
        
    Returns:
        List of table names
    """
    return [
        name 
        for name, schema in SCHEMA_METADATA.items() 
        if schema.get("category") == category
    ]


__all__ = [
    "SCHEMA_METADATA",
    "ColumnType",
    "TableCategory",
    "get_table_schema",
    "get_required_columns",
    "get_searchable_columns",
    "has_vector_search",
    "get_all_tables",
    "get_tables_by_category"
]
