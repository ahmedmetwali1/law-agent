import re

class TextNormalizer:
    @staticmethod
    def normalize_arabic_text(text: str) -> str:
        """
        Robust text normalization for Arabic legal search and processing.
        Unifies disparate characters to ensure matching (e.g., Ahmd == Ahmed).
        """
        if not text:
            return ""
            
        # 1. Normalize Alef (أ, إ, آ -> ا)
        text = re.sub(r'[أإآ]', 'ا', text)
        
        # 2. Normalize Ya/Alef Maqsura (ى -> ي)
        # Note: In strict normalization we might map both to dotless yeh, 
        # but commonly mapping ى to ي works for search if the DB is also normalized.
        # Or better: specific context rules. For generic search, mapping ى to ي is safer.
        text = re.sub(r'ى', 'ي', text)
        
        # 3. Normalize Ta Marbuta (ة -> ه)
        # This is CRITICAL for partial matches (مكتبة vs مكتبه)
        text = re.sub(r'ة', 'ه', text)
        
        # 4. Remove Diacritics (Tashkeel)
        text = re.sub(r'[\u064B-\u065F]', '', text)
        
        # 5. Collapse multiple spaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    @staticmethod
    def context_aware_correction(text: str) -> str:
        """
        Applies heuristic fixes for common legal typing errors.
        """
        # Common typos map
        corrections = {
            r'\bمدعى\b': 'مدعي',   # Common confusion if user meant Claimant
            r'\bمستانف\b': 'مستأنف',
            r'\bمستانف ضده\b': 'مستأنف ضده',
            r'\bتوجيه\b': 'توجيه', # often typed as توجية (handled by normalizer but good for direct fixes)
        }
        
        for pattern, replacement in corrections.items():
            text = re.sub(pattern, replacement, text)
            
        return text

    @staticmethod
    def is_semantically_equal(text1: str, text2: str) -> bool:
        """
        Checks if two texts are essentially the same after normalization.
        """
        return TextNormalizer.normalize_arabic_text(text1) == TextNormalizer.normalize_arabic_text(text2)
