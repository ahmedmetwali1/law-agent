"""
Arabic Text Utilities
أدوات معالجة النصوص العربية

Handles Arabic character variations and fuzzy matching
"""

import re
from typing import List, Tuple
from difflib import SequenceMatcher


def normalize_arabic(text: str) -> str:
    """
    Normalize Arabic text for flexible matching
    
    Handles:
    - Hamza variations: أ، إ، آ → ا
    - Taa Marbuta: ة → ه
    - Alef Maksura: ى → ي
    - Remove diacritics (tashkeel)
    
    Args:
        text: Arabic text to normalize
        
    Returns:
        Normalized text
        
    Examples:
        "أحمد" → "احمد"
        "فاطمة" → "فاطمه"
        "مصطفى" → "مصطفي"
    """
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Normalize Hamza variations
    text = re.sub(r'[أإآ]', 'ا', text)
    
    # Normalize Taa Marbuta
    text = re.sub(r'ة', 'ه', text)
    
    # Normalize Alef Maksura
    text = re.sub(r'ى', 'ي', text)
    
    # Remove Arabic diacritics (tashkeel)
    arabic_diacritics = re.compile(r'[\u064B-\u0652\u0640]')
    text = arabic_diacritics.sub('', text)
    
    # Remove extra spaces
    text = ' '.join(text.split())
    
    return text


def similarity_score(text1: str, text2: str) -> float:
    """
    Calculate similarity between two Arabic texts
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        Similarity score (0.0 to 1.0)
    """
    # Normalize both texts
    norm1 = normalize_arabic(text1)
    norm2 = normalize_arabic(text2)
    
    # Calculate similarity
    return SequenceMatcher(None, norm1, norm2).ratio()


def find_similar_matches(
    query: str, 
    candidates: List[str], 
    threshold: float = 0.6
) -> List[Tuple[str, float]]:
    """
    Find similar matches from candidates
    
    Args:
        query: Search query
        candidates: List of candidate strings
        threshold: Minimum similarity score (0.0 to 1.0)
        
    Returns:
        List of (candidate, score) tuples, sorted by score
        
    Example:
        query = "احمد متولي"
        candidates = ["أحمد متولى", "احمد محمد", "فاطمة"]
        → [("أحمد متولى", 0.95), ("احمد محمد", 0.65)]
    """
    matches = []
    
    for candidate in candidates:
        score = similarity_score(query, candidate)
        if score >= threshold:
            matches.append((candidate, score))
    
    # Sort by score (descending)
    matches.sort(key=lambda x: x[1], reverse=True)
    
    return matches


def contains_flexible(text: str, query: str) -> bool:
    """
    Flexible contains check (handles Arabic variations)
    
    Args:
        text: Text to search in
        query: Query to search for
        
    Returns:
        True if query found in text (normalized)
        
    Example:
        contains_flexible("أحمد متولى", "احمد") → True
        contains_flexible("فاطمة", "فاطمه") → True
    """
    return normalize_arabic(query) in normalize_arabic(text)


def create_flexible_pattern(query: str) -> str:
    """
    Create SQL LIKE pattern for flexible Arabic search
    
    Args:
        query: Search query
        
    Returns:
        SQL LIKE pattern with variations
        
    Example:
        "أحمد" → Pattern matching: أحمد, احمد, إحمد, آحمد
    """
    normalized = normalize_arabic(query)
    
    # Build pattern with variations
    # This returns the normalized version which will match
    # variations when both sides are normalized
    return f"%{normalized}%"


__all__ = [
    'normalize_arabic',
    'similarity_score',
    'find_similar_matches',
    'contains_flexible',
    'create_flexible_pattern'
]
