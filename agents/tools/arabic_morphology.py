"""
🔤 Arabic Morphology Engine
Generates legal conjugations and derivatives for Arabic legal terms
"""

from typing import List, Set
import re


class ArabicMorphology:
    """
    Arabic morphological analyzer focused on legal terminology
    """
    
    # Common legal term patterns
    LEGAL_PATTERNS = {
        # Contract-related (عقد)
        "عقد": ["عقد", "عاقد", "متعاقد", "التعاقد", "المتعاقدين", "العقد", "العاقد", "المتعاقد"],
        
        # Sale (بيع)
        "بيع": ["بيع", "بائع", "مبيع", "مشتري", "البيع", "البائع", "المبيع", "المشتري", "بيعه", "بيعها"],
        
        # Gift (هبة)
        "هبة": ["هبة", "واهب", "موهوب", "الهبة", "الواهب", "الموهوب له", "هبته", "هبتها", "وهب", "يهب"],
        
        # Ownership (ملك)
        "ملك": ["ملك", "مالك", "ملكية", "المالك", "الملكية", "ملكه", "ملكها", "تملك", "التملك"],
        
        # Lease (إيجار)
        "إيجار": ["إيجار", "مؤجر", "مستأجر", "الإيجار", "المؤجر", "المستأجر", "إيجاره", "أجر", "يؤجر"],
        
        # Loan (قرض)
        "قرض": ["قرض", "مقرض", "مقترض", "القرض", "المقرض", "المقترض", "قرضه", "اقتراض"],
        
        # Mortgage (رهن)
        "رهن": ["رهن", "راهن", "مرتهن", "الرهن", "الراهن", "المرتهن", "رهنه", "ارتهان"],
        
        # Inheritance (إرث / ميراث)
        "إرث": ["إرث", "ميراث", "وارث", "مورث", "الإرث", "الميراث", "الوارث", "المورث", "ورثة"],
        "ميراث": ["ميراث", "إرث", "وارث", "مورث", "الميراث", "الوارث", "المورث", "ورثة"],
        
        # Will (وصية)
        "وصية": ["وصية", "موصي", "موصى له", "الوصية", "الموصي", "وصيته", "أوصى"],
        
        # Partnership (شركة)
        "شركة": ["شركة", "شريك", "شركاء", "الشركة", "الشريك", "الشركاء", "شراكة", "المشاركة"],
        
        # Compensation (تعويض)
        "تعويض": ["تعويض", "تعويضات", "التعويض", "التعويضات", "عوض", "يعوض", "معوض"],
        
        # Damage (ضرر)
        "ضرر": ["ضرر", "أضرار", "متضرر", "الضرر", "الأضرار", "المتضرر", "ضرره", "إضرار"],
        
        # Obligation (التزام)
        "التزام": ["التزام", "التزامات", "ملتزم", "الالتزام", "الالتزamات", "ملزم", "إلزام"],
        
        # Right (حق)
        "حق": ["حق", "حقوق", "الحق", "الحقوق", "حقه", "حقها", "حقوقه", "صاحب الحق"],
    }
    
    @staticmethod
    def get_conjugations(term: str) -> List[str]:
        """
        Get all legal conjugations for a term
        
        Args:
            term: Arabic legal term
            
        Returns:
            List of conjugations and derivatives
        """
        # Normalize
        term_clean = term.strip().lower()
        
        # Remove "ال" if present
        if term_clean.startswith("ال"):
            term_root = term_clean[2:]
        else:
            term_root = term_clean
        
        # Check if we have predefined patterns
        if term_root in ArabicMorphology.LEGAL_PATTERNS:
            return ArabicMorphology.LEGAL_PATTERNS[term_root]
        
        # Fallback: generate basic variations
        variants = set()
        variants.add(term_clean)
        
        # Add with/without ال
        if term_clean.startswith("ال"):
            variants.add(term_clean[2:])
        else:
            variants.add("ال" + term_clean)
        
        # Add possessive forms
        for suffix in ["ه", "ها", "هم", "هما", "ك", "كم"]:
            variants.add(term_root + suffix)
        
        # ة/ه variants
        if "ة" in term_clean:
            variants.add(term_clean.replace("ة", "ه"))
        if "ه" in term_clean and not term_clean.endswith("ه"):
            variants.add(term_clean.replace("ه", "ة"))
        
        return list(variants)
    
    @staticmethod
    def expand_legal_keywords(keywords: List[str]) -> List[str]:
        """
        Expand a list of keywords with conjugations
        
        Args:
            keywords: Original keywords
            
        Returns:
            Expanded list with conjugations
        """
        expanded = set()
        
        for kw in keywords:
            # Add original
            expanded.add(kw)
            
            # Add conjugations
            conjugations = ArabicMorphology.get_conjugations(kw)
            expanded.update(conjugations)
        
        # Remove generic/academic words
        academic_words = {
            "تعريف", "معنى", "المقصود", "شرح", "توضيح", "دراسة", 
            "بحث", "تفسير", "كيفية", "ماهية", "definition", "meaning"
        }
        
        expanded = expanded - academic_words
        
        return list(expanded)


# Convenient function
def get_legal_terms(word: str) -> List[str]:
    """Get all legal variations of a word"""
    return ArabicMorphology.get_conjugations(word)


if __name__ == "__main__":
    # Test
    test_words = ["هبة", "بيع", "عقد", "ملك"]
    
    print("🔤 Arabic Morphology Engine Tests:\n")
    
    for word in test_words:
        terms = get_legal_terms(word)
        print(f"{word} →")
        print(f"   {terms}\n")
