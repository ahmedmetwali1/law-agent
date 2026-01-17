"""
Advanced Intelligent Prompts System v2.0
نظام البرومبتات الذكية المتقدم

التحسينات:
1. Semantic Domain Detection
2. Fuzzy Keyword Matching
3. Dynamic Keyword Expansion
4. Few-Shot Learning Templates
5. Prompt Versioning & A/B Testing
6. User Preference Learning
7. Context-Aware Magic Words
8. Prompt Chaining
9. Performance Tracking
10. Adaptive Complexity Assessment
"""

import re
import logging
import hashlib
import json
from typing import List, Dict, Any, Optional, Tuple, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from collections import defaultdict
import numpy as np
from difflib import SequenceMatcher
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


# ============================================================
# ENUMS - تعدادات محسّنة
# ============================================================

class LegalDomain(Enum):
    """
    المجالات القانونية المحسّنة
    مع metadata إضافية لكل مجال
    """
    PERSONAL_STATUS = ("أحوال شخصية", "family", ["حضانة", "طلاق", "نفقة", "زواج"])
    CIVIL = ("مدني", "civil", ["عقد", "تعويض", "ملكية"])
    CRIMINAL = ("جنائي", "criminal", ["جريمة", "عقوبة", "متهم"])
    COMMERCIAL = ("تجاري", "commercial", ["شركة", "تجارة", "شيك"])
    LABOR = ("عمالي", "labor", ["عامل", "فصل", "راتب"])
    ADMINISTRATIVE = ("إداري", "administrative", ["قرار", "تظلم", "حكومة"])
    REAL_ESTATE = ("عقاري", "real_estate", ["عقار", "صك", "إفراغ"])
    WAQF_INHERITANCE = ("وقف وتركات", "inheritance", ["ميراث", "وصية", "تركة"])
    EXECUTION = ("تنفيذ وإجراءات", "execution", ["تنفيذ", "حجز", "سند"])
    GENERAL_REGULATIONS = ("أنظمة عامة", "general", ["نظام", "لائحة"])
    UNKNOWN = ("غير محدد", "unknown", [])
    
    def __init__(self, arabic_name: str, english_key: str, core_keywords: List[str]):
        self.arabic_name = arabic_name
        self.english_key = english_key
        self.core_keywords = core_keywords
    
    @property
    def db_value(self) -> str:
        return self.arabic_name
    
    @classmethod
    def from_string(cls, value: str) -> 'LegalDomain':
        """تحويل من نص إلى enum"""
        for domain in cls:
            if domain.arabic_name == value or domain.english_key == value:
                return domain
        return cls.UNKNOWN


class QuestionComplexity(Enum):
    """مستوى التعقيد مع أوزان"""
    SIMPLE = ("simple", 1, "سؤال مباشر")
    MODERATE = ("moderate", 2, "يحتاج تحليل")
    COMPLEX = ("complex", 3, "متعدد الأبعاد")
    EXPERT = ("expert", 4, "يحتاج خبرة عميقة")  # جديد
    
    def __init__(self, key: str, level: int, description: str):
        self.key = key
        self.level = level
        self.description = description


class PromptStyle(Enum):
    """أنماط البرومبت"""
    FORMAL = "formal"           # رسمي قانوني
    CONVERSATIONAL = "conversational"  # محادثة
    ACADEMIC = "academic"       # أكاديمي
    PRACTICAL = "practical"     # عملي تطبيقي


class MagicWordCategory(Enum):
    """فئات الكلمات السحرية"""
    STEP_BY_STEP = "step_by_step"
    DEEP_THINKING = "deep_thinking"
    EXPERT_ROLE = "expert_role"
    VERIFICATION = "verification"
    COUNTER_ARGUMENT = "counter_argument"
    STRUCTURED_OUTPUT = "structured_output"
    CONFIDENCE = "confidence"       # جديد
    EXAMPLES = "examples"           # جديد
    LIMITATIONS = "limitations"     # جديد


# ============================================================
# DATA STRUCTURES - هياكل البيانات المحسّنة
# ============================================================

@dataclass
class KeywordMatch:
    """مطابقة كلمة مفتاحية"""
    keyword: str
    matched_text: str
    similarity: float
    domain: LegalDomain
    is_exact: bool


@dataclass
class DomainScore:
    """نتيجة تحديد المجال"""
    domain: LegalDomain
    score: float
    matched_keywords: List[str]
    confidence: float
    reasoning: str


@dataclass
class AnalyzedQuestion:
    """نتيجة تحليل السؤال المحسّنة"""
    original: str
    normalized: str  # جديد: النص المنظف
    keywords: List[str]
    legal_keywords: List[KeywordMatch]  # محسّن
    domain: LegalDomain
    domain_scores: List[DomainScore]  # جديد: كل النتائج
    secondary_domains: List[LegalDomain]  # جديد
    complexity: QuestionComplexity
    complexity_factors: Dict[str, float]  # جديد
    sub_questions: List[str]
    search_queries: List[str]
    intent: str  # جديد: نية السؤال
    entities: Dict[str, List[str]]  # جديد: الكيانات المستخرجة
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "original": self.original,
            "domain": self.domain.arabic_name,
            "complexity": self.complexity.key,
            "keywords": self.keywords,
            "legal_keywords": [k.keyword for k in self.legal_keywords],
            "sub_questions": self.sub_questions,
            "search_queries": self.search_queries,
            "intent": self.intent
        }


@dataclass
class PromptTemplate:
    """قالب برومبت محسّن"""
    template_id: str
    name: str
    version: str
    template: str
    variables: List[str]
    category: str
    style: PromptStyle
    performance_score: float = 0.0
    usage_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    
    def render(self, **kwargs) -> str:
        """تقديم القالب بالمتغيرات"""
        result = self.template
        for var in self.variables:
            if var in kwargs:
                result = result.replace(f"{{{var}}}", str(kwargs[var]))
        return result


@dataclass
class FewShotExample:
    """مثال للتعلم"""
    question: str
    answer: str
    domain: LegalDomain
    quality_score: float
    source: str


@dataclass
class PromptPerformance:
    """أداء البرومبت"""
    template_id: str
    success_rate: float
    avg_response_quality: float
    avg_response_time: float
    usage_count: int
    last_used: datetime


# ============================================================
# MAGIC WORDS - الكلمات السحرية المحسّنة
# ============================================================

class MagicWordsManager:
    """مدير الكلمات السحرية"""
    
    def __init__(self):
        self.words = self._initialize_words()
        self.context_rules = self._initialize_context_rules()
        self.performance = defaultdict(lambda: {"uses": 0, "success": 0})
    
    def _initialize_words(self) -> Dict[MagicWordCategory, List[Dict[str, Any]]]:
        """تهيئة الكلمات السحرية مع metadata"""
        return {
            MagicWordCategory.STEP_BY_STEP: [
                {"text": "فكّر خطوة بخطوة", "weight": 1.0, "lang": "ar"},
                {"text": "Let's think step by step", "weight": 0.9, "lang": "en"},
                {"text": "حلل هذا بشكل منهجي ومتسلسل", "weight": 0.95, "lang": "ar"},
                {"text": "قبل الإجابة، رتّب أفكارك بتسلسل منطقي", "weight": 0.85, "lang": "ar"},
                {"text": "ابدأ بالأساسيات ثم انتقل للتفاصيل", "weight": 0.8, "lang": "ar"}
            ],
            MagicWordCategory.DEEP_THINKING: [
                {"text": "فكّر بعمق وتأنٍّ في كل جانب", "weight": 1.0, "lang": "ar"},
                {"text": "خذ وقتك في التحليل الشامل", "weight": 0.9, "lang": "ar"},
                {"text": "لا تتسرع، الدقة أهم من السرعة", "weight": 0.85, "lang": "ar"},
                {"text": "تأمل في جميع الاحتمالات", "weight": 0.8, "lang": "ar"}
            ],
            MagicWordCategory.EXPERT_ROLE: [
                {"text": "أنت محامٍ سعودي خبير بخبرة 20 عاماً في {domain}", "weight": 1.0, "lang": "ar", "vars": ["domain"]},
                {"text": "تصرّف كقاضٍ في المحكمة العليا يفحص القضية", "weight": 0.95, "lang": "ar"},
                {"text": "أنت مستشار قانوني أول في مكتب محاماة رائد", "weight": 0.9, "lang": "ar"},
                {"text": "بصفتك خبيراً في {domain}، قدم تحليلك المهني", "weight": 0.85, "lang": "ar", "vars": ["domain"]}
            ],
            MagicWordCategory.VERIFICATION: [
                {"text": "تحقق من صحة استنتاجاتك قبل تقديمها", "weight": 1.0, "lang": "ar"},
                {"text": "ما الأدلة القانونية التي تدعم هذا الرأي؟", "weight": 0.95, "lang": "ar"},
                {"text": "هل هناك استثناءات لهذه القاعدة؟", "weight": 0.9, "lang": "ar"},
                {"text": "راجع المنطق القانوني مرة أخرى", "weight": 0.85, "lang": "ar"}
            ],
            MagicWordCategory.COUNTER_ARGUMENT: [
                {"text": "ما الحجج المضادة المحتملة التي قد يثيرها الخصم؟", "weight": 1.0, "lang": "ar"},
                {"text": "فكّر من وجهة نظر الطرف الآخر", "weight": 0.95, "lang": "ar"},
                {"text": "ما الذي قد يُضعف هذا الموقف القانوني؟", "weight": 0.9, "lang": "ar"},
                {"text": "كيف يمكن للخصم أن يطعن في هذا؟", "weight": 0.85, "lang": "ar"}
            ],
            MagicWordCategory.STRUCTURED_OUTPUT: [
                {"text": "نظّم إجابتك بوضوح مع عناوين وفقرات", "weight": 1.0, "lang": "ar"},
                {"text": "ابدأ بالخلاصة ثم قدم التفاصيل", "weight": 0.95, "lang": "ar"},
                {"text": "استخدم تعداداً نقطياً للوضوح", "weight": 0.9, "lang": "ar"},
                {"text": "قسّم الإجابة إلى: القاعدة، التطبيق، الاستنتاج", "weight": 0.85, "lang": "ar"}
            ],
            MagicWordCategory.CONFIDENCE: [
                {"text": "حدد مستوى ثقتك في كل استنتاج (عالي/متوسط/منخفض)", "weight": 1.0, "lang": "ar"},
                {"text": "إذا لم تكن متأكداً، اذكر ذلك صراحة", "weight": 0.95, "lang": "ar"},
                {"text": "ميّز بين الحقائق المؤكدة والاحتمالات", "weight": 0.9, "lang": "ar"}
            ],
            MagicWordCategory.EXAMPLES: [
                {"text": "قدم أمثلة عملية توضيحية", "weight": 1.0, "lang": "ar"},
                {"text": "استشهد بسوابق قضائية إن وجدت", "weight": 0.95, "lang": "ar"},
                {"text": "وضّح بحالة افتراضية مشابهة", "weight": 0.9, "lang": "ar"}
            ],
            MagicWordCategory.LIMITATIONS: [
                {"text": "اذكر حدود هذا الرأي القانوني", "weight": 1.0, "lang": "ar"},
                {"text": "وضّح الحالات التي لا ينطبق عليها هذا", "weight": 0.95, "lang": "ar"},
                {"text": "نبّه إلى ما يحتاج استشارة متخصص", "weight": 0.9, "lang": "ar"}
            ]
        }
    
    def _initialize_context_rules(self) -> Dict[str, List[MagicWordCategory]]:
        """قواعد اختيار الكلمات حسب السياق"""
        return {
            "simple": [MagicWordCategory.STRUCTURED_OUTPUT],
            "moderate": [
                MagicWordCategory.STEP_BY_STEP,
                MagicWordCategory.STRUCTURED_OUTPUT
            ],
            "complex": [
                MagicWordCategory.DEEP_THINKING,
                MagicWordCategory.STEP_BY_STEP,
                MagicWordCategory.VERIFICATION,
                MagicWordCategory.COUNTER_ARGUMENT
            ],
            "expert": [
                MagicWordCategory.DEEP_THINKING,
                MagicWordCategory.EXPERT_ROLE,
                MagicWordCategory.VERIFICATION,
                MagicWordCategory.COUNTER_ARGUMENT,
                MagicWordCategory.CONFIDENCE,
                MagicWordCategory.LIMITATIONS
            ],
            "controversial": [
                MagicWordCategory.COUNTER_ARGUMENT,
                MagicWordCategory.VERIFICATION,
                MagicWordCategory.CONFIDENCE
            ]
        }
    
    def get_words(
        self,
        categories: List[MagicWordCategory],
        domain: Optional[LegalDomain] = None,
        max_per_category: int = 2
    ) -> List[str]:
        """الحصول على كلمات سحرية"""
        result = []
        
        for category in categories:
            if category not in self.words:
                continue
            
            words = self.words[category]
            # ترتيب حسب الوزن
            sorted_words = sorted(words, key=lambda w: w["weight"], reverse=True)
            
            for word_data in sorted_words[:max_per_category]:
                text = word_data["text"]
                
                # استبدال المتغيرات
                if "vars" in word_data and domain:
                    text = text.replace("{domain}", domain.arabic_name)
                
                result.append(text)
        
        return result
    
    def get_context_words(
        self,
        complexity: QuestionComplexity,
        domain: Optional[LegalDomain] = None,
        is_controversial: bool = False
    ) -> List[str]:
        """الحصول على كلمات حسب السياق"""
        context = complexity.key
        if is_controversial:
            context = "controversial"
        
        categories = self.context_rules.get(context, [MagicWordCategory.STEP_BY_STEP])
        return self.get_words(categories, domain)
    
    def record_usage(self, category: MagicWordCategory, success: bool):
        """تسجيل الاستخدام"""
        self.performance[category.value]["uses"] += 1
        if success:
            self.performance[category.value]["success"] += 1


# ============================================================
# FUZZY KEYWORD MATCHER - مطابقة الكلمات الضبابية
# ============================================================

class FuzzyKeywordMatcher:
    """مطابق الكلمات المفتاحية الذكي"""
    
    def __init__(self, similarity_threshold: float = 0.7):
        self.threshold = similarity_threshold
        self.keyword_cache: Dict[str, List[str]] = {}
        self.synonyms = self._load_synonyms()
    
    def _load_synonyms(self) -> Dict[str, List[str]]:
        """تحميل المترادفات"""
        return {
            # أحوال شخصية
            "حضانة": ["رعاية", "كفالة", "حفظ"],
            "طلاق": ["فراق", "انفصال", "تطليق"],
            "نفقة": ["إنفاق", "معاش", "مصروف"],
            "زيارة": ["رؤية", "مشاهدة", "لقاء"],
            # جنائي
            "جريمة": ["جناية", "جرم", "مخالفة"],
            "عقوبة": ["جزاء", "عقاب", "حد"],
            "سجن": ["حبس", "إيداع", "توقيف"],
            # مدني
            "عقد": ["اتفاق", "اتفاقية", "عهد"],
            "تعويض": ["جبر", "تعويضات", "أرش"],
            "ملكية": ["تملك", "استحقاق", "حيازة"],
            # عمالي
            "فصل": ["إنهاء", "طرد", "إقالة"],
            "راتب": ["أجر", "مرتب", "مقابل"],
            "عامل": ["موظف", "مستخدم", "عمال"],
            # إضافات
            "دعوى": ["قضية", "دعاوى", "شكوى"],
            "حكم": ["قرار", "أمر", "فصل"],
        }
    
    def similarity(self, text1: str, text2: str) -> float:
        """حساب التشابه بين نصين"""
        return SequenceMatcher(None, text1, text2).ratio()
    
    def find_matches(
        self,
        text: str,
        keywords: List[str],
        domain: Optional[LegalDomain] = None
    ) -> List[KeywordMatch]:
        """البحث عن مطابقات"""
        matches = []
        words = text.split()
        
        for keyword in keywords:
            # مطابقة مباشرة
            if keyword in text:
                matches.append(KeywordMatch(
                    keyword=keyword,
                    matched_text=keyword,
                    similarity=1.0,
                    domain=domain or LegalDomain.UNKNOWN,
                    is_exact=True
                ))
                continue
            
            # مطابقة مع المترادفات
            synonyms = self.synonyms.get(keyword, [])
            for synonym in synonyms:
                if synonym in text:
                    matches.append(KeywordMatch(
                        keyword=keyword,
                        matched_text=synonym,
                        similarity=0.9,
                        domain=domain or LegalDomain.UNKNOWN,
                        is_exact=False
                    ))
                    break
            
            # مطابقة ضبابية
            for word in words:
                sim = self.similarity(keyword, word)
                if sim >= self.threshold:
                    matches.append(KeywordMatch(
                        keyword=keyword,
                        matched_text=word,
                        similarity=sim,
                        domain=domain or LegalDomain.UNKNOWN,
                        is_exact=False
                    ))
                    break
        
        return matches
    
    def expand_keywords(self, keywords: List[str]) -> List[str]:
        """توسيع الكلمات بالمترادفات"""
        expanded = set(keywords)
        
        for keyword in keywords:
            if keyword in self.synonyms:
                expanded.update(self.synonyms[keyword])
        
        return list(expanded)


# ============================================================
# SEMANTIC DOMAIN DETECTOR - كاشف المجال الدلالي
# ============================================================

class SemanticDomainDetector:
    """كاشف المجال القانوني الدلالي"""
    
    def __init__(self):
        self.fuzzy_matcher = FuzzyKeywordMatcher()
        self.domain_keywords = self._initialize_domain_keywords()
        self.domain_patterns = self._initialize_patterns()
        self.domain_weights = self._initialize_weights()
    
    def _initialize_domain_keywords(self) -> Dict[LegalDomain, List[str]]:
        """كلمات كل مجال"""
        return {
            LegalDomain.PERSONAL_STATUS: [
                # الحضانة والزيارة
                "حضانة", "زيارة", "طلاق", "نفقة", "مهر", "عدة", "خلع",
                "أب", "أم", "طفل", "أطفال", "ولي", "ولاية", "وصاية",
                "محكمة الأحوال الشخصية", "صك الطلاق", "عقد الزواج",
                "حق الرؤية", "سفر الأطفال", "انتقال الحضانة",
                "إسقاط الحضانة", "سن الحضانة", "مصلحة الطفل",
                "نفقة الأولاد", "نفقة الزوجة", "نفقة المطلقة",
                "السكن", "المسكن", "الملابس", "التعليم", "العلاج",
                "زوج", "زوجة", "إرضاع", "حاضنة", "محضون"
            ],
            LegalDomain.CRIMINAL: [
                "جريمة", "جناية", "جنحة", "مخالفة", "عقوبة", "سجن",
                "حبس", "غرامة", "إعدام", "قصاص", "حد", "تعزير",
                "متهم", "مدعى عليه", "نيابة", "ادعاء عام",
                "محكمة جزائية", "استئناف جزائي",
                "سرقة", "قتل", "اعتداء", "تحرش", "مخدرات", "رشوة",
                "احتيال", "تزوير", "ابتزاز", "إرهاب", "غسيل أموال"
            ],
            LegalDomain.CIVIL: [
                "عقد", "بيع", "شراء", "إيجار", "رهن", "كفالة",
                "ملكية", "حيازة", "تعويض", "ضرر", "مسؤولية",
                "دين", "دائن", "مدين", "وفاء", "مقاصة",
                "محكمة عامة", "دعوى مدنية", "إخلاء", "فسخ",
                "ضمان", "عيب", "غبن", "تدليس", "إكراه"
            ],
            LegalDomain.COMMERCIAL: [
                "شركة", "تجارة", "تاجر", "سجل تجاري", "إفلاس",
                "شيك", "كمبيالة", "سند", "وكالة تجارية",
                "علامة تجارية", "منافسة", "احتكار",
                "شراكة", "أسهم", "حصص", "تصفية", "اندماج"
            ],
            LegalDomain.LABOR: [
                "عامل", "موظف", "صاحب عمل", "عقد عمل", "راتب",
                "إجازة", "فصل", "استقالة", "مكافأة نهاية الخدمة",
                "تأمينات", "ساعات عمل", "إصابة عمل",
                "نقل", "ترقية", "إنذار", "خصم", "بدلات"
            ],
            LegalDomain.ADMINISTRATIVE: [
                "جهة حكومية", "قرار إداري", "تظلم", "طعن",
                "ديوان المظالم", "محكمة إدارية", "لائحة", "نظام",
                "موظف حكومي", "خدمة مدنية", "ترخيص"
            ],
            LegalDomain.REAL_ESTATE: [
                "عقار", "أرض", "صك", "ملكية عقارية", "بيع عقار",
                "إيجار عقار", "رهن عقاري", "كتابة العدل", "إفراغ",
                "فرز", "تجزئة", "وثيقة عقارية", "نظام التسجيل العيني"
            ],
            LegalDomain.WAQF_INHERITANCE: [
                "ميراث", "تركة", "ورثة", "وارث", "فريضة",
                "وقف", "وصية", "حصر إرث", "قسمة تركة",
                "نصيب", "عصبة", "فرض", "تعصيب"
            ],
            LegalDomain.EXECUTION: [
                "تنفيذ", "حكم", "سند تنفيذي", "محكمة التنفيذ",
                "حجز", "منع سفر", "إيقاف خدمات", "مهلة",
                "إجراءات", "مرافعات", "نظام المرافعات"
            ],
            LegalDomain.GENERAL_REGULATIONS: [
                "نظام", "لائحة", "قرار وزاري", "مرسوم ملكي",
                "أمر سامي", "تعميم", "قواعد", "ضوابط"
            ]
        }
    
    def _initialize_patterns(self) -> Dict[LegalDomain, List[str]]:
        """أنماط regex لكل مجال"""
        return {
            LegalDomain.PERSONAL_STATUS: [
                r"حق\s*(الحضانة|الزيارة|الرؤية)",
                r"(أب|أم|والد|والدة)\s*(المحضون|الطفل)",
                r"نفقة\s*(الأولاد|الزوجة|المطلقة)"
            ],
            LegalDomain.CRIMINAL: [
                r"(اتهام|تهمة)\s*ب",
                r"عقوبة\s*(السجن|الحبس|الغرامة)",
                r"جريمة\s*(القتل|السرقة|الاحتيال)"
            ],
            LegalDomain.CIVIL: [
                r"عقد\s*(بيع|إيجار|شراء)",
                r"(فسخ|إلغاء)\s*العقد",
                r"تعويض\s*عن\s*(الضرر|الخسارة)"
            ],
            LegalDomain.LABOR: [
                r"عقد\s*عمل",
                r"(فصل|إنهاء\s*خدمات)\s*(تعسفي)?",
                r"مكافأة\s*نهاية\s*الخدمة"
            ]
        }
    
    def _initialize_weights(self) -> Dict[str, float]:
        """أوزان عوامل التحديد"""
        return {
            "keyword_match": 0.4,
            "pattern_match": 0.3,
            "synonym_match": 0.2,
            "context_match": 0.1
        }
    
    def detect(self, question: str) -> List[DomainScore]:
        """تحديد المجال مع الدرجات"""
        scores = []
        
        for domain, keywords in self.domain_keywords.items():
            if domain == LegalDomain.UNKNOWN:
                continue
            
            score = 0.0
            matched = []
            
            # مطابقة الكلمات
            keyword_matches = self.fuzzy_matcher.find_matches(question, keywords, domain)
            if keyword_matches:
                exact_matches = [m for m in keyword_matches if m.is_exact]
                fuzzy_matches = [m for m in keyword_matches if not m.is_exact]
                
                score += len(exact_matches) * self.domain_weights["keyword_match"]
                score += len(fuzzy_matches) * self.domain_weights["synonym_match"]
                matched.extend([m.keyword for m in keyword_matches])
            
            # مطابقة الأنماط
            if domain in self.domain_patterns:
                for pattern in self.domain_patterns[domain]:
                    if re.search(pattern, question):
                        score += self.domain_weights["pattern_match"]
                        matched.append(f"pattern:{pattern[:20]}")
            
            if score > 0:
                confidence = min(1.0, score / 3)  # normalize
                scores.append(DomainScore(
                    domain=domain,
                    score=score,
                    matched_keywords=matched,
                    confidence=confidence,
                    reasoning=f"تطابق {len(matched)} كلمة/نمط"
                ))
        
        # ترتيب حسب النتيجة
        scores.sort(key=lambda x: x.score, reverse=True)
        return scores
    
    def get_primary_domain(self, question: str) -> Tuple[LegalDomain, float]:
        """الحصول على المجال الرئيسي"""
        scores = self.detect(question)
        if scores:
            return scores[0].domain, scores[0].confidence
        return LegalDomain.UNKNOWN, 0.0


# ============================================================
# COMPLEXITY ANALYZER - محلل التعقيد
# ============================================================

class ComplexityAnalyzer:
    """محلل تعقيد السؤال المتقدم"""
    
    def __init__(self):
        self.indicators = self._initialize_indicators()
        self.thresholds = {
            "simple": 3,
            "moderate": 7,
            "complex": 12,
            "expert": float('inf')
        }
    
    def _initialize_indicators(self) -> Dict[str, Dict[str, Any]]:
        """مؤشرات التعقيد"""
        return {
            "conditionals": {
                "patterns": ["إذا", "في حالة", "بشرط", "عند", "لو", "متى"],
                "weight": 2.0
            },
            "exceptions": {
                "patterns": ["إلا", "ماعدا", "باستثناء", "لكن", "غير أن"],
                "weight": 2.5
            },
            "multiple_aspects": {
                "patterns": ["و", "أيضاً", "بالإضافة", "كما", "فضلاً"],
                "weight": 1.0
            },
            "comparison": {
                "patterns": ["الفرق", "قارن", "أيهما", "مقارنة"],
                "weight": 2.0
            },
            "explanation": {
                "patterns": ["كيف", "لماذا", "وضح", "اشرح", "فسّر"],
                "weight": 1.5
            },
            "legal_terms": {
                "patterns": ["حسب النظام", "وفقاً لـ", "بموجب", "طبقاً"],
                "weight": 1.5
            },
            "multi_party": {
                "patterns": ["والمدعى عليه", "الطرفين", "كلا", "جميع"],
                "weight": 1.5
            },
            "temporal": {
                "patterns": ["قبل", "بعد", "خلال", "منذ", "حتى"],
                "weight": 1.0
            }
        }
    
    def analyze(self, question: str) -> Tuple[QuestionComplexity, Dict[str, float]]:
        """تحليل تعقيد السؤال"""
        scores = {}
        total_score = 0.0
        
        for indicator_name, config in self.indicators.items():
            patterns = config["patterns"]
            weight = config["weight"]
            
            count = sum(1 for p in patterns if p in question)
            score = count * weight
            
            scores[indicator_name] = score
            total_score += score
        
        # طول السؤال
        word_count = len(question.split())
        length_score = word_count / 10  # 10 كلمات = 1 نقطة
        scores["length"] = length_score
        total_score += length_score
        
        # تحديد المستوى
        if total_score < self.thresholds["simple"]:
            complexity = QuestionComplexity.SIMPLE
        elif total_score < self.thresholds["moderate"]:
            complexity = QuestionComplexity.MODERATE
        elif total_score < self.thresholds["complex"]:
            complexity = QuestionComplexity.COMPLEX
        else:
            complexity = QuestionComplexity.EXPERT
        
        return complexity, scores


# ============================================================
# INTENT DETECTOR - كاشف النية
# ============================================================

class IntentDetector:
    """كاشف نية السؤال"""
    
    def __init__(self):
        self.intents = {
            "definition": {
                "patterns": ["ما هو", "ما هي", "ما المقصود", "عرّف", "تعريف"],
                "description": "طلب تعريف"
            },
            "procedure": {
                "patterns": ["كيف", "ما الإجراءات", "ما الخطوات", "طريقة"],
                "description": "طلب إجراء"
            },
            "eligibility": {
                "patterns": ["هل يحق", "هل يجوز", "هل أستطيع", "هل يمكن"],
                "description": "استفسار عن الأهلية"
            },
            "comparison": {
                "patterns": ["ما الفرق", "قارن", "أيهما أفضل"],
                "description": "طلب مقارنة"
            },
            "consequence": {
                "patterns": ["ماذا يحدث", "ما النتيجة", "ما العقوبة"],
                "description": "استفسار عن النتائج"
            },
            "deadline": {
                "patterns": ["متى", "ما المدة", "كم يوم", "ما الموعد"],
                "description": "استفسار عن مواعيد"
            },
            "advice": {
                "patterns": ["ماذا أفعل", "أنصحني", "ما رأيك"],
                "description": "طلب نصيحة"
            }
        }
    
    def detect(self, question: str) -> str:
        """تحديد النية"""
        for intent_name, config in self.intents.items():
            if any(p in question for p in config["patterns"]):
                return intent_name
        return "general"


# ============================================================
# ENTITY EXTRACTOR - مستخرج الكيانات
# ============================================================

class EntityExtractor:
    """مستخرج الكيانات القانونية"""
    
    def __init__(self):
        self.entity_patterns = {
            "مبالغ": r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(ريال|دولار|جنيه)',
            "مدد": r'(\d+)\s*(يوم|شهر|سنة|أسبوع)',
            "نسب": r'(\d+(?:\.\d+)?)\s*[%٪]',
            "أعمار": r'(\d+)\s*(?:سنة|عام)(?:\s*(?:هجري|ميلادي))?',
            "تواريخ": r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
            "مواد_نظامية": r'(?:المادة|مادة)\s*(?:رقم\s*)?(\d+)',
        }
    
    def extract(self, text: str) -> Dict[str, List[str]]:
        """استخراج الكيانات"""
        entities = {}
        
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                if isinstance(matches[0], tuple):
                    entities[entity_type] = [" ".join(m) for m in matches]
                else:
                    entities[entity_type] = matches
        
        return entities


# ============================================================
# FEW-SHOT MANAGER - مدير الأمثلة
# ============================================================

class FewShotManager:
    """مدير أمثلة التعلم"""
    
    def __init__(self):
        self.examples: Dict[LegalDomain, List[FewShotExample]] = defaultdict(list)
        self._initialize_examples()
    
    def _initialize_examples(self):
        """تهيئة الأمثلة الأولية"""
        # أمثلة الأحوال الشخصية
        self.examples[LegalDomain.PERSONAL_STATUS] = [
            FewShotExample(
                question="متى تسقط حضانة الأم؟",
                answer="""تسقط حضانة الأم في الحالات التالية:
1. زواجها من أجنبي عن المحضون
2. إهمالها للمحضون بما يضره
3. إصابتها بمرض معدٍ خطير
4. سوء خلقها الظاهر
5. عدم أمانتها على المحضون

**المصدر:** نظام الأحوال الشخصية، المادة 127""",
                domain=LegalDomain.PERSONAL_STATUS,
                quality_score=0.95,
                source="expert_validated"
            ),
            FewShotExample(
                question="كم مدة حضانة الأم للطفل الذكر؟",
                answer="""حسب نظام الأحوال الشخصية السعودي:
- الطفل الذكر: تستمر الحضانة حتى يبلغ **سبع سنوات**
- بعدها يُخيَّر بين أبويه
- يمكن للمحكمة تمديدها لمصلحة المحضون

**المصدر:** المادة 126 من نظام الأحوال الشخصية""",
                domain=LegalDomain.PERSONAL_STATUS,
                quality_score=0.9,
                source="expert_validated"
            )
        ]
        
        # أمثلة العمل
        self.examples[LegalDomain.LABOR] = [
            FewShotExample(
                question="كم مكافأة نهاية الخدمة للعامل؟",
                answer="""تُحسب مكافأة نهاية الخدمة كالتالي:

**للسنوات الخمس الأولى:**
- نصف شهر عن كل سنة

**للسنوات التي تزيد عن خمس:**
- شهر كامل عن كل سنة

**ملاحظة:** يستحق العامل المستقيل:
- ثلث المكافأة: 2-5 سنوات
- ثلثي المكافأة: 5-10 سنوات
- المكافأة كاملة: أكثر من 10 سنوات

**المصدر:** المادة 84 و 85 من نظام العمل""",
                domain=LegalDomain.LABOR,
                quality_score=0.95,
                source="expert_validated"
            )
        ]
    
    def get_examples(
        self,
        domain: LegalDomain,
        max_examples: int = 2,
        min_quality: float = 0.8
    ) -> List[FewShotExample]:
        """الحصول على أمثلة"""
        examples = self.examples.get(domain, [])
        
        # تصفية حسب الجودة
        filtered = [e for e in examples if e.quality_score >= min_quality]
        
        # ترتيب حسب الجودة
        filtered.sort(key=lambda x: x.quality_score, reverse=True)
        
        return filtered[:max_examples]
    
    def format_examples(self, examples: List[FewShotExample]) -> str:
        """تنسيق الأمثلة للبرومبت"""
        if not examples:
            return ""
        
        formatted = "\n**أمثلة توضيحية:**\n"
        
        for i, ex in enumerate(examples, 1):
            formatted += f"\n--- مثال {i} ---\n"
            formatted += f"**السؤال:** {ex.question}\n"
            formatted += f"**الإجابة:**\n{ex.answer}\n"
        
        formatted += "\n--- نهاية الأمثلة ---\n\n"
        return formatted
    
    def add_example(self, example: FewShotExample):
        """إضافة مثال جديد"""
        self.examples[example.domain].append(example)


# ============================================================
# PROMPT TEMPLATE MANAGER - مدير القوالب
# ============================================================

class PromptTemplateManager:
    """مدير قوالب البرومبت مع A/B Testing"""
    
    def __init__(self):
        self.templates: Dict[str, List[PromptTemplate]] = defaultdict(list)
        self.performance: Dict[str, PromptPerformance] = {}
        self._initialize_templates()
    
    def _initialize_templates(self):
        """تهيئة القوالب"""
        
        # قوالب تحليل السؤال
        self.templates["question_analyzer"] = [
            PromptTemplate(
                template_id="qa_v1",
                name="محلل السؤال الأساسي",
                version="1.0",
                template="""أنت محلل قانوني متخصص. حلل السؤال التالي:

**السؤال:** {question}

**المطلوب:**
1. استخرج الكلمات المفتاحية القانونية (5-10 كلمات)
2. حدد المجال القانوني
3. قيّم مستوى التعقيد
4. اقترح أسئلة فرعية للبحث

**أجب بـ JSON:**
{{
    "keywords": ["كلمة1", "كلمة2"],
    "domain": "المجال",
    "complexity": "simple/moderate/complex",
    "sub_questions": ["سؤال فرعي"]
}}""",
                variables=["question"],
                category="analysis",
                style=PromptStyle.FORMAL
            ),
            PromptTemplate(
                template_id="qa_v2",
                name="محلل السؤال المحسّن",
                version="2.0",
                template="""بصفتك خبيراً في تحليل الاستشارات القانونية:

{magic_words}

**السؤال المطروح:**
{question}

**حلل السؤال واستخرج:**
1. الكلمات المفتاحية القانونية الدقيقة
2. المجال القانوني الرئيسي والفرعي
3. درجة التعقيد والسبب
4. النية من السؤال (استفسار/طلب إجراء/نصيحة)
5. أسئلة فرعية تساعد في الإجابة الشاملة

**الإجابة بـ JSON:**
{{
    "keywords": [],
    "primary_domain": "",
    "secondary_domain": "",
    "complexity": "",
    "complexity_reason": "",
    "intent": "",
    "sub_questions": []
}}""",
                variables=["question", "magic_words"],
                category="analysis",
                style=PromptStyle.FORMAL
            )
        ]
        
        # قوالب الاستدلال القانوني
        self.templates["legal_reasoning"] = [
            PromptTemplate(
                template_id="lr_v1",
                name="الاستدلال القانوني الأساسي",
                version="1.0",
                template="""أنت محامٍ سعودي خبير في {domain}.

{magic_words}

**السؤال:** {question}

**المعلومات المتاحة:**
{context}

**قدم إجابة شاملة تتضمن:**
1. القاعدة القانونية المنطبقة
2. تطبيقها على الحالة
3. الاستثناءات إن وجدت
4. التوصية النهائية

**ملاحظة:** استشهد بالمواد النظامية حيث أمكن.""",
                variables=["domain", "magic_words", "question", "context"],
                category="reasoning",
                style=PromptStyle.FORMAL
            ),
            PromptTemplate(
                template_id="lr_v2",
                name="الاستدلال القانوني المتقدم",
                version="2.0",
                template="""{expert_role}

{magic_words}

**القضية المطروحة:**
{question}

**السياق والمعلومات:**
{context}

{few_shot_examples}

**التعليمات:**
1. حدد الإطار القانوني المنطبق بدقة
2. حلل الوقائع في ضوء النظام
3. ناقش الاحتمالات المختلفة
4. قدم الرأي القانوني مع درجة الثقة
5. اذكر المحاذير والاستثناءات

**البنية المطلوبة:**
- **الخلاصة:** (جملة واحدة)
- **التحليل:** (مفصل)
- **الأساس القانوني:** (المواد والأنظمة)
- **التوصيات:** (عملية)
- **التحذيرات:** (إن وجدت)
- **درجة الثقة:** (عالية/متوسطة/منخفضة)""",
                variables=["expert_role", "magic_words", "question", "context", "few_shot_examples"],
                category="reasoning",
                style=PromptStyle.FORMAL
            )
        ]
        
        # قوالب التحقق
        self.templates["verification"] = [
            PromptTemplate(
                template_id="ver_v1",
                name="التحقق الأساسي",
                version="1.0",
                template="""أنت مدقق قانوني صارم. راجع الإجابة:

**السؤال:** {question}
**الإجابة:** {answer}
**المصادر:** {sources_count}

**تحقق من:**
1. دقة المعلومات القانونية
2. صحة المنطق
3. اكتمال الإجابة
4. وجود تناقضات

**أجب بـ JSON:**
{{
    "is_valid": true/false,
    "confidence": 0.0-1.0,
    "issues": [],
    "suggestions": [],
    "verdict": "مقبول/يحتاج تعديل/مرفوض"
}}""",
                variables=["question", "answer", "sources_count"],
                category="verification",
                style=PromptStyle.FORMAL
            )
        ]
    
    def get_template(
        self,
        category: str,
        version: Optional[str] = None,
        use_ab_testing: bool = True
    ) -> PromptTemplate:
        """الحصول على قالب"""
        templates = self.templates.get(category, [])
        
        if not templates:
            raise ValueError(f"No templates for category: {category}")
        
        if version:
            for t in templates:
                if t.version == version:
                    return t
        
        if use_ab_testing and len(templates) > 1:
            # اختيار عشوائي موزون حسب الأداء
            weights = [max(0.1, t.performance_score) for t in templates]
            total = sum(weights)
            probs = [w/total for w in weights]
            return np.random.choice(templates, p=probs)
        
        return templates[0]
    
    def record_performance(
        self,
        template_id: str,
        success: bool,
        quality: float,
        response_time: float
    ):
        """تسجيل أداء القالب"""
        if template_id not in self.performance:
            self.performance[template_id] = PromptPerformance(
                template_id=template_id,
                success_rate=0.0,
                avg_response_quality=0.0,
                avg_response_time=0.0,
                usage_count=0,
                last_used=datetime.now()
            )
        
        perf = self.performance[template_id]
        perf.usage_count += 1
        
        # تحديث المتوسطات
        n = perf.usage_count
        perf.success_rate = ((n-1) * perf.success_rate + (1 if success else 0)) / n
        perf.avg_response_quality = ((n-1) * perf.avg_response_quality + quality) / n
        perf.avg_response_time = ((n-1) * perf.avg_response_time + response_time) / n
        perf.last_used = datetime.now()
        
        # تحديث نتيجة الأداء في القالب
        for category_templates in self.templates.values():
            for template in category_templates:
                if template.template_id == template_id:
                    template.performance_score = perf.success_rate * 0.5 + perf.avg_response_quality * 0.5
                    template.usage_count = perf.usage_count


# ============================================================
# ADVANCED QUERY GENERATOR - مولد الاستعلامات المتقدم
# ============================================================

class AdvancedQueryGenerator:
    """مولد الاستعلامات والتحليل المتقدم"""
    
    def __init__(self):
        self.domain_detector = SemanticDomainDetector()
        self.complexity_analyzer = ComplexityAnalyzer()
        self.intent_detector = IntentDetector()
        self.entity_extractor = EntityExtractor()
        self.fuzzy_matcher = FuzzyKeywordMatcher()
        
        logger.info("🧠 AdvancedQueryGenerator initialized")
    
    def analyze(self, question: str) -> AnalyzedQuestion:
        """تحليل شامل للسؤال"""
        
        # تنظيف النص
        normalized = self._normalize_text(question)
        
        # استخراج الكلمات المفتاحية
        keywords = self._extract_keywords(normalized)
        
        # تحديد المجال
        domain_scores = self.domain_detector.detect(normalized)
        primary_domain = domain_scores[0].domain if domain_scores else LegalDomain.UNKNOWN
        secondary_domains = [ds.domain for ds in domain_scores[1:3] if ds.score > 0.5]
        
        # استخراج الكلمات القانونية
        legal_keywords = self._extract_legal_keywords(normalized, primary_domain)
        
        # تحليل التعقيد
        complexity, complexity_factors = self.complexity_analyzer.analyze(normalized)
        
        # تحديد النية
        intent = self.intent_detector.detect(normalized)
        
        # استخراج الكيانات
        entities = self.entity_extractor.extract(normalized)
        
        # توليد الأسئلة الفرعية
        sub_questions = self._generate_sub_questions(question, primary_domain, intent)
        
        # توليد استعلامات البحث
        search_queries = self._generate_search_queries(
            legal_keywords, primary_domain, intent
        )
        
        logger.info(f"📊 Analyzed: domain={primary_domain.arabic_name}, "
                   f"complexity={complexity.key}, intent={intent}")
        
        return AnalyzedQuestion(
            original=question,
            normalized=normalized,
            keywords=keywords,
            legal_keywords=legal_keywords,
            domain=primary_domain,
            domain_scores=domain_scores,
            secondary_domains=secondary_domains,
            complexity=complexity,
            complexity_factors=complexity_factors,
            sub_questions=sub_questions,
            search_queries=search_queries,
            intent=intent,
            entities=entities
        )
    
    def _normalize_text(self, text: str) -> str:
        """تنظيف وتوحيد النص"""
        # إزالة التشكيل
        text = re.sub(r'[\u064B-\u065F]', '', text)
        
        # توحيد الهمزات
        text = re.sub(r'[إأآا]', 'ا', text)
        
        # إزالة علامات الترقيم الزائدة
        text = re.sub(r'[؟?!]+', '؟', text)
        
        # إزالة المسافات الزائدة
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _extract_keywords(self, text: str) -> List[str]:
        """استخراج الكلمات المفتاحية"""
        words = re.findall(r'[\u0600-\u06FF]+', text)
        
        stop_words = {
            "في", "من", "إلى", "على", "عن", "هل", "ما", "هي", "هو",
            "أن", "كان", "التي", "الذي", "هذا", "هذه", "مع", "أو",
            "كل", "بعد", "قبل", "أي", "لم", "لا", "قد", "كيف"
        }
        
        keywords = [w for w in words if len(w) > 2 and w not in stop_words]
        
        # إزالة التكرارات مع الحفاظ على الترتيب
        seen = set()
        unique = []
        for kw in keywords:
            if kw not in seen:
                seen.add(kw)
                unique.append(kw)
        
        return unique[:15]
    
    def _extract_legal_keywords(
        self,
        text: str,
        domain: LegalDomain
    ) -> List[KeywordMatch]:
        """استخراج الكلمات القانونية"""
        keywords = self.domain_detector.domain_keywords.get(domain, [])
        
        # توسيع بالمترادفات
        expanded = self.fuzzy_matcher.expand_keywords(keywords)
        
        # البحث عن المطابقات
        matches = self.fuzzy_matcher.find_matches(text, expanded, domain)
        
        return matches
    
    def _generate_sub_questions(
        self,
        question: str,
        domain: LegalDomain,
        intent: str
    ) -> List[str]:
        """توليد أسئلة فرعية ذكية"""
        sub_questions = []
        
        # أسئلة حسب المجال
        domain_questions = {
            LegalDomain.PERSONAL_STATUS: {
                "حضانة": [
                    "ما شروط الحضانة في النظام السعودي؟",
                    "ما الحالات التي تسقط فيها الحضانة؟",
                    "كيف يتم تنظيم الزيارة؟"
                ],
                "طلاق": [
                    "ما أنواع الطلاق وشروط كل منها؟",
                    "ما حقوق المطلقة؟",
                    "ما إجراءات الطلاق القضائي؟"
                ],
                "نفقة": [
                    "كيف تُحسب النفقة؟",
                    "ما عناصر النفقة الواجبة؟",
                    "متى تسقط النفقة؟"
                ]
            },
            LegalDomain.LABOR: {
                "فصل": [
                    "ما حالات الفصل المشروع؟",
                    "ما تعويضات الفصل التعسفي؟",
                    "ما إجراءات الطعن في قرار الفصل؟"
                ],
                "راتب": [
                    "ما حقوق العامل في الأجر؟",
                    "متى يجوز الخصم من الراتب؟",
                    "كيف تُحسب المستحقات المتأخرة؟"
                ]
            },
            LegalDomain.CRIMINAL: {
                "عقوبة": [
                    "ما أنواع العقوبات في النظام الجزائي؟",
                    "ما الظروف المخففة والمشددة؟",
                    "ما إجراءات الاستئناف؟"
                ]
            }
        }
        
        # البحث عن أسئلة مناسبة
        if domain in domain_questions:
            for keyword, questions in domain_questions[domain].items():
                if keyword in question:
                    sub_questions.extend(questions[:2])
                    break
        
        # أسئلة حسب النية
        intent_questions = {
            "procedure": ["ما الوثائق المطلوبة؟", "ما المدة الزمنية المتوقعة؟"],
            "eligibility": ["ما الشروط الواجب توفرها؟", "ما الموانع؟"],
            "consequence": ["ما العقوبات المحتملة؟", "ما سبل التخفيف؟"],
            "deadline": ["ما آخر موعد؟", "ما يترتب على فوات المدة؟"]
        }
        
        if intent in intent_questions:
            sub_questions.extend(intent_questions[intent][:1])
        
        return sub_questions[:5]
    
    def _generate_search_queries(
        self,
        legal_keywords: List[KeywordMatch],
        domain: LegalDomain,
        intent: str
    ) -> List[str]:
        """توليد استعلامات بحث محسّنة"""
        queries = []
        
        # استعلام 1: الكلمات الرئيسية
        main_keywords = [m.keyword for m in legal_keywords[:3]]
        if main_keywords:
            queries.append(" ".join(main_keywords))
        
        # استعلام 2: المجال + الموضوع
        if domain != LegalDomain.UNKNOWN and main_keywords:
            queries.append(f"{domain.arabic_name} {main_keywords[0]}")
        
        # استعلام 3: مع سياق النية
        intent_prefixes = {
            "procedure": "إجراءات",
            "eligibility": "شروط",
            "consequence": "عقوبة",
            "deadline": "مدة"
        }
        
        if intent in intent_prefixes and main_keywords:
            queries.append(f"{intent_prefixes[intent]} {main_keywords[0]}")
        
        # استعلام 4: توسيع بالمترادفات
        if len(legal_keywords) > 1:
            synonyms = self.fuzzy_matcher.expand_keywords([legal_keywords[0].keyword])
            if len(synonyms) > 1:
                queries.append(" ".join(synonyms[:3]))
        
        return queries[:5]


# ============================================================
# ADVANCED PROMPT BUILDER - بنّاء البرومبت المتقدم
# ============================================================

class AdvancedPromptBuilder:
    """بنّاء البرومبت المتقدم"""
    
    def __init__(self):
        self.query_generator = AdvancedQueryGenerator()
        self.magic_words = MagicWordsManager()
        self.templates = PromptTemplateManager()
        self.few_shot = FewShotManager()
        
        logger.info("🔧 AdvancedPromptBuilder initialized")
    
    def build_analysis_prompt(self, question: str) -> str:
        """بناء برومبت التحليل"""
        template = self.templates.get_template("question_analyzer", use_ab_testing=True)
        
        magic = "\n".join(self.magic_words.get_words([
            MagicWordCategory.STEP_BY_STEP,
            MagicWordCategory.STRUCTURED_OUTPUT
        ]))
        
        return template.render(
            question=question,
            magic_words=magic
        )
    
    def build_reasoning_prompt(
        self,
        question: str,
        context: str,
        domain: Optional[LegalDomain] = None,
        complexity: Optional[QuestionComplexity] = None,
        include_examples: bool = True
    ) -> str:
        """بناء برومبت الاستدلال القانوني"""
        
        # تحليل السؤال إذا لم يُحدد المجال
        if domain is None:
            analysis = self.query_generator.analyze(question)
            domain = analysis.domain
            complexity = analysis.complexity
        
        # اختيار القالب
        template = self.templates.get_template("legal_reasoning", use_ab_testing=True)
        
        # الكلمات السحرية حسب التعقيد
        magic = "\n".join(self.magic_words.get_context_words(
            complexity or QuestionComplexity.MODERATE,
            domain
        ))
        
        # دور الخبير
        expert_role = f"أنت محامٍ سعودي خبير بخبرة 20 عاماً في {domain.arabic_name}."
        
        # الأمثلة
        examples_text = ""
        if include_examples:
            examples = self.few_shot.get_examples(domain)
            examples_text = self.few_shot.format_examples(examples)
        
        return template.render(
            expert_role=expert_role,
            magic_words=magic,
            question=question,
            context=context[:3000],
            few_shot_examples=examples_text,
            domain=domain.arabic_name
        )
    
    def build_verification_prompt(
        self,
        question: str,
        answer: str,
        sources_count: int
    ) -> str:
        """بناء برومبت التحقق"""
        template = self.templates.get_template("verification")
        
        return template.render(
            question=question,
            answer=answer[:2500],
            sources_count=sources_count
        )
    
    def build_consistency_prompt(
        self,
        question: str,
        context: str,
        perspective: str,
        focus_area: str
    ) -> str:
        """بناء برومبت التناسق"""
        magic = "\n".join(self.magic_words.get_words([
            MagicWordCategory.DEEP_THINKING,
            MagicWordCategory.VERIFICATION
        ]))
        
        return f"""أنت خبير قانوني. فكر في المسألة من منظور {perspective}.

{magic}

**السؤال:** {question}
**السياق:** {context[:1500]}

**من وجهة نظر {perspective}:**
ركز على {focus_area} وقدم تحليلك.

**التحليل:**"""
    
    def get_magic_words(
        self,
        categories: List[MagicWordCategory],
        domain: Optional[LegalDomain] = None
    ) -> List[str]:
        """الحصول على كلمات سحرية"""
        return self.magic_words.get_words(categories, domain)
    
    def record_prompt_performance(
        self,
        template_id: str,
        success: bool,
        quality: float,
        response_time: float
    ):
            self.templates.record_performance(template_id, success, quality, response_time)


# ============================================================================
# Backward Compatibility Aliases (للتوافق مع الكود القديم)
# ============================================================================

# Alias للكلاسات القديمة
IntelligentQueryGenerator = AdvancedQueryGenerator
PromptBuilder = AdvancedPromptBuilder

# إضافة method alias للتوافق
def _add_analyze_question_alias():
    """إضافة analyze_question كـalias لـanalyze"""
    AdvancedQueryGenerator.analyze_question = AdvancedQueryGenerator.analyze

_add_analyze_question_alias()

# Backward compatibility constants
MAGIC_WORDS = {
    "greeting": ["مرحبا", "السلام", "اهلا", "صباح", "مساء"],
    "thanks": ["شكرا", "متشكر"],
    "question": ["كيف", "ماذا", "هل", "متى", "أين"]
}

LEGAL_DOMAIN_KEYWORDS = {
    "أحوال شخصية": ["طلاق", "زواج", "حضانة", "نفقة"],
    "تجاري": ["شركة", "عقد", "تجارة"],
    "جنائي": ["قتل", "سرقة", "تزوير"],
    "حقوق": ["ملكية", "عقار", "تعويض"]
}

PROMPT_TEMPLATES = {
    "simple": "ابحث عن: {query}",
    "detailed": "استعلام مفصل: {query}"
}


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    # Enums
    "LegalDomain",
    "QuestionComplexity",
    "PromptStyle",
    "MagicWordCategory",
    
    # Data structures
    "AnalyzedQuestion",
    "KeywordMatch",
    "DomainScore",
    "PromptTemplate",
    "FewShotExample",
    
    # Managers
    "MagicWordsManager",
    "FuzzyKeywordMatcher",
    "SemanticDomainDetector",
    "ComplexityAnalyzer",
    "IntentDetector",
    "EntityExtractor",
    "FewShotManager",
    "PromptTemplateManager",
    
    # Main classes
    "AdvancedQueryGenerator",
    "AdvancedPromptBuilder",
    
    # Backward compatibility
    "IntelligentQueryGenerator",  # Alias
    "PromptBuilder",  # Alias
    "MAGIC_WORDS",
    "LEGAL_DOMAIN_KEYWORDS",
    "PROMPT_TEMPLATES"
]