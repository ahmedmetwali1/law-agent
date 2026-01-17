import re
from typing import Optional

class ArabicTextNormalizer:
    """تنظيف وتطبيع النص العربي من STT"""
    
    # كلمات الحشو الشائعة
    FILLER_WORDS = [
        'إممم', 'أممم', 'اممم', 'إمم', 'أمم', 'امم',
        'أه', 'آه', 'اه', 'أهه', 'آهه',
        'يعني', 'طيب', 'أوكي', 'اوكي', 'تمام',
        'بس', 'والله', 'يا', 'لا والله'
    ]
    
    @staticmethod
    def normalize(text: str) -> str:
        """Pipeline كامل للتنظيف"""
        if not text or not isinstance(text, str):
            return ""
        
        # تطبيق جميع خطوات التنظيف
        text = ArabicTextNormalizer.remove_filler_words(text)
        text = ArabicTextNormalizer.normalize_arabic_chars(text)
        text = ArabicTextNormalizer.fix_punctuation(text)
        text = ArabicTextNormalizer.remove_extra_whitespace(text)
        text = ArabicTextNormalizer.capitalize_first_letter(text)
        
        return text.strip()
    
    @staticmethod
    def remove_filler_words(text: str) -> str:
        """إزالة كلمات الحشو الشائعة"""
        pattern = r'\b(' + '|'.join(ArabicTextNormalizer.FILLER_WORDS) + r')\b'
        return re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    @staticmethod
    def normalize_arabic_chars(text: str) -> str:
        """توحيد الأحرف العربية المختلفة"""
        # توحيد الألف
        text = re.sub('[إأآٱ]', 'ا', text)
        
        # توحيد الياء
        text = re.sub('ى', 'ي', text)
        
        # توحيد الهاء
        text = re.sub('ة', 'ه', text)  # اختياري - حسب الحاجة
        
        # إزالة التشكيل الكامل
        text = re.sub('[\u064B-\u0652\u0617-\u061A\u0640]', '', text)
        
        return text
    
    @staticmethod
    def fix_punctuation(text: str) -> str:
        """إصلاح علامات الترقيم"""
        # إزالة علامات ترقيم متكررة
        text = re.sub(r'([.!?،؟])\1+', r'\1', text)
        
        # إضافة مسافة بعد علامات الترقيم إذا لم توجد
        text = re.sub(r'([.!?،؟])([^\s])', r'\1 \2', text)
        
        # إزالة المسافة قبل علامات الترقيم
        text = re.sub(r'\s+([.!?،؟])', r'\1', text)
        
        return text
    
    @staticmethod
    def remove_extra_whitespace(text: str) -> str:
        """إزالة المسافات الزائدة"""
        # استبدال أي تسلسل من المسافات البيضاء بمسافة واحدة
        text = re.sub(r'\s+', ' ', text)
        
        # إزالة المسافات من البداية والنهاية
        return text.strip()
    
    @staticmethod
    def capitalize_first_letter(text: str) -> str:
        """جعل أول حرف كبير (للغة الإنجليزية المختلطة)"""
        if not text:
            return text
        
        # البحث عن أول حرف (عربي أو إنجليزي)
        for i, char in enumerate(text):
            if char.isalpha():
                return text[:i] + char.upper() + text[i+1:]
        
        return text
    
    @staticmethod
    def validate_and_clean(text: str, min_length: int = 1, max_length: int = 1000) -> Optional[str]:
        """التحقق من صحة النص وتنظيفه"""
        if not text:
            return None
        
        # تنظيف النص
        cleaned = ArabicTextNormalizer.normalize(text)
        
        # التحقق من الطول - أكثر تساهلاً الآن
        if len(cleaned) < min_length:
            return None
        
        if len(cleaned) > max_length:
            cleaned = cleaned[:max_length]
        
        # التحقق من وجود محتوى فعلي (ليس مسافات فقط)
        if not cleaned or cleaned.isspace():
            return None
        
        return cleaned


# دالة مساعدة للاستخدام السريع
def clean_stt_text(text: str) -> str:
    """تنظيف سريع للنص من STT"""
    return ArabicTextNormalizer.normalize(text)
