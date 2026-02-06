import logging
import asyncio
import time
import re
from typing import List, Dict, Any, Optional, Tuple
from langchain_core.messages import SystemMessage
from collections import defaultdict

from .base_tool import BaseTool, ToolResult
from .fetch_tools import FlexibleSearchTool
from .vector_tools import VectorSearchTool
from agents.core.llm_factory import get_llm, get_embeddings
from agents.config.database import db  # For country validation

logger = logging.getLogger(__name__)

class HybridSearchTool(BaseTool):
    """
    ⚖️ Legal Hybrid Search Engine v3.0 (LHSE-Pro)
    
    Architecture: "The Scout, The Analyst & The Sniper"
    
    Enhancements v3.0:
    - Universal legal system support (not country-specific)
    - Query type detection (Article Enumeration, Definition, Procedure, etc.)
    - Enhanced article extraction (Arabic & Latin numerals, ranges)
    - Adaptive scoring based on query type
    - Multi-language legal entity patterns
    """
    
    # ==================== LEGAL PATTERNS ====================
    
    # Article Patterns (Arabic, English, with ranges support)
    ARTICLE_PATTERNS = [
        # Arabic patterns
        r'المادة\s*[\(]?\s*([\d\u0660-\u0669]+)\s*[\)]?',           # المادة 77, المادة (77), المادة ٧٧
        r'المواد\s*[\(]?\s*([\d\u0660-\u0669]+)\s*[\)]?',          # المواد 77
        r'مادة\s*[\(]?\s*([\d\u0660-\u0669]+)\s*[\)]?',            # مادة 77
        r'م\s*[\.\:\-]?\s*([\d\u0660-\u0669]+)',                   # م.77, م:77, م-77
        
        # English patterns
        r'Article\s*[\(]?\s*(\d+)\s*[\)]?',                        # Article 77, Article (77)
        r'Art\s*\.?\s*[\(]?\s*(\d+)\s*[\)]?',                     # Art. 77, Art 77
        r'Section\s*[\(]?\s*(\d+)\s*[\)]?',                       # Section 77
        r'Sec\s*\.?\s*[\(]?\s*(\d+)\s*[\)]?',                     # Sec. 77
        
        # French patterns
        r'Article\s*[\(]?\s*(\d+)\s*[\)]?',                       # Article 77
        r'Art\s*\.?\s*[\(]?\s*(\d+)\s*[\)]?',                     # Art. 77
    ]
    
    # Range Patterns (المواد من X إلى Y)
    RANGE_PATTERNS = [
        r'المواد\s*من\s*([\d\u0660-\u0669]+)\s*(?:إلى|حتى|الى|-|–|—)\s*([\d\u0660-\u0669]+)',  # المواد من 77 إلى 90
        r'المواد\s*[\(]?\s*([\d\u0660-\u0669]+)\s*(?:-|–|—)\s*([\d\u0660-\u0669]+)\s*[\)]?',    # المواد (77-90)
        r'Articles\s*(\d+)\s*(?:to|through|-|–|—)\s*(\d+)',                                      # Articles 77 to 90
        r'Articles\s*[\(]?\s*(\d+)\s*(?:-|–|—)\s*(\d+)\s*[\)]?',                                # Articles (77-90)
    ]
    
    # Law/Regulation Patterns
    LAW_PATTERNS = [
        # Arabic
        r'القانون\s+رقم\s+([\d\u0660-\u0669]+)\s+لسنة\s+([\d\u0660-\u0669]+)',  # القانون رقم 12 لسنة 2023
        r'قانون\s+([\d\u0660-\u0669]+)\s*/\s*([\d\u0660-\u0669]+)',              # قانون 12/2023
        r'النظام\s+رقم\s+([\d\u0660-\u0669]+)',                                  # النظام رقم 12
        r'نظام\s+([\w\s]+)',                                                      # نظام المعاملات المدنية
        
        # English
        r'Law\s+No\s*\.?\s*(\d+)\s+of\s+(\d+)',                                  # Law No. 12 of 2023
        r'Act\s+No\s*\.?\s*(\d+)\s+of\s+(\d+)',                                  # Act No. 12 of 2023
        r'Regulation\s+No\s*\.?\s*(\d+)',                                        # Regulation No. 12
    ]
    
    # Arabic Normalization Map
    ARABIC_NORMALIZE = {
        'أ': 'ا', 'إ': 'ا', 'آ': 'ا', 'ٱ': 'ا',
        'ة': 'ه', 'ـ': '',
        'ى': 'ي',
        'ؤ': 'و', 'ئ': 'ي',
    }
    
    # Stop Words (Multi-language)
    STOP_WORDS = {
        # Arabic
        "ما", "هي", "في", "عن", "من", "إلى", "على", "هذا", "ذلك", "هذه", "تلك",
        "التى", "التي", "الذي", "الذى", "تتكلم", "يتكلم", "تتحدث", "يتحدث",
        "أن", "أي", "كل", "بعض", "هل", "لماذا", "كيف", "متى", "أين",
        "الى", "لـ", "بـ", "كـ", "و", "أو", "ثم", "لكن", "لكن",
        
        # English
        "what", "is", "are", "in", "on", "at", "the", "a", "an",
        "about", "which", "that", "this", "these", "those",
        "how", "why", "when", "where", "who", "whom",
        "and", "or", "but", "if", "then",
    }
    
    # Query Type Indicators
    QUERY_TYPE_PATTERNS = {
        'ARTICLE_ENUMERATION': [
            r'ما هي المواد',
            r'أرقام المواد',
            r'المواد التي',
            r'المواد التى',
            r'المواد الخاصة',
            r'أي المواد',
            r'which articles',
            r'what articles',
            r'list.*articles',
            r'articles.*related',
        ],
        'DEFINITION': [
            r'ما هو',
            r'ما هي',
            r'عرف',
            r'تعريف',
            r'معنى',
            r'المقصود',
            r'what is',
            r'define',
            r'definition',
            r'meaning',
        ],
        'PROCEDURE': [
            r'كيف',
            r'ما هي الإجراءات',
            r'الخطوات',
            r'الطريقة',
            r'how to',
            r'procedure',
            r'process',
            r'steps',
        ],
        'CONDITION': [
            r'شروط',
            r'متى',
            r'في أي حال',
            r'conditions',
            r'requirements',
            r'when',
        ],
        'COMPARISON': [
            r'الفرق بين',
            r'مقارنة',
            r'difference',
            r'compare',
            r'versus',
            r'vs',
        ],
    }
    
    def __init__(self):
        super().__init__(
            name="universal_legal_hybrid_search",
            description="محرك بحث قانوني هجين عالمي - Universal Legal Search Engine"
        )
        self.vector_tool = VectorSearchTool()
        self.keyword_tool = FlexibleSearchTool()
        
        # Import LawIdentifierTool for law filtering
        from .law_identifier_tool import LawIdentifierTool
        self.law_identifier = LawIdentifierTool()
        
    # ==================== UTILITY METHODS ====================
    
    def _normalize_arabic(self, text: str) -> str:
        """Normalize Arabic text for better matching"""
        if not text:
            return ""
        for old, new in self.ARABIC_NORMALIZE.items():
            text = text.replace(old, new)
        return text
    
    def _generate_arabic_variants(self, text: str) -> List[str]:
        """
        ✅ FIX: Generate all Arabic variant forms of a word + NUMBER CONVERSION
        
        Example: "الهبة" → ["الهبة", "الهبه", "هبة", "هبه"]
                 "المادة 368" → ["المادة 368", "المادة الثامنة وستون بعد الثلاثمائة", ...]
        This solves the problem where "الهبة" ≠ "الهبه" in search
        """
        if not text:
            return [text]
        
        variants = set()
        variants.add(text)  # Original
        
        # ===== ARTICLE NUMBER CONVERSION =====
        # Check if text contains article numbers (e.g., "المادة 368")
        from .arabic_numbers import number_to_arabic_text
        
        # Pattern: المادة [number]
        article_pattern = r'(المادة|مادة|الماده)\s+(\d+)'
        matches = re.findall(article_pattern, text)
        
        for prefix, num_str in matches:
            try:
                num = int(num_str)
                arabic_text = number_to_arabic_text(num)
                
                if arabic_text and not arabic_text.isdigit():
                    # Add variant with Arabic text
                    # e.g., "المادة الثامنة وستون بعد الثلاثمائة"
                    variant_with_text = text.replace(f"{prefix} {num_str}", f"{prefix} {arabic_text}")
                    variants.add(variant_with_text)
                    
                    # Also add without "ال" prefix on المادة
                    variant_no_al = variant_with_text.replace("المادة", "مادة")
                    variants.add(variant_no_al)
            except:
                pass  # Ignore conversion errors
        
        # ===== EXISTING VARIANTS (Hamza, Ta Marbuta, etc.) =====
        # Remove "ال" article
        if text.startswith('ال'):
            variants.add(text[2:])
        
        # Swap: ة ↔ ه
        if 'ة' in text:
            variants.add(text.replace('ة', 'ه'))
        if 'ه' in text:
            variants.add(text.replace('ه', 'ة'))
        
        # Swap hamzas: أ، إ، آ → ا
        for old, new in [('أ', 'ا'), ('إ', 'ا'), ('آ', 'ا')]:
            if old in text:
                variants.add(text.replace(old, new))
        
        # Swap alif maqsura: ى → ي
        if 'ى' in text:
            variants.add(text.replace('ى', 'ي'))
        if 'ي' in text:
            variants.add(text.replace('ي', 'ى'))
        
        # تنوين normalization
        for tanween in ['ً', 'ٌ', 'ٍ']:
            if tanween in text:
                variants.add(text.replace(tanween, ''))
        
        return list(variants)
    
    def _convert_arabic_numerals(self, text: str) -> str:
        """Convert Arabic-Indic numerals to Western numerals"""
        arabic_to_western = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')
        return text.translate(arabic_to_western)
    
    def _detect_query_type(self, query: str) -> str:
        """
        🎯 Detect the type of legal query to optimize search strategy
        
        Returns: ARTICLE_ENUMERATION, DEFINITION, PROCEDURE, CONDITION, COMPARISON, or GENERAL
        """
        query_lower = query.lower()
        
        for query_type, patterns in self.QUERY_TYPE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    logger.info(f"🎯 Query Type Detected: {query_type}")
                    return query_type
        
        return 'GENERAL'
    
    def _extract_legal_entities(self, text: str) -> Dict[str, List]:
        """
        Extract legal entities from text:
        - Article numbers (with ranges)
        - Law references
        - Case numbers
        """
        if not text:
            return {'articles': [], 'laws': [], 'ranges': []}
        
        # Convert Arabic numerals first
        text = self._convert_arabic_numerals(text)
        
        entities = {
            'articles': [],
            'laws': [],
            'ranges': []
        }
        
        # Extract Article Ranges
        for pattern in self.RANGE_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple) and len(match) >= 2:
                    start = int(match[0])
                    end = int(match[1])
                    if start < end and (end - start) < 100:  # Reasonable range
                        entities['ranges'].append((start, end))
                        # Expand range
                        entities['articles'].extend(range(start, end + 1))
        
        # Extract Individual Articles
        for pattern in self.ARTICLE_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    article_num = int(match)
                    if 1 <= article_num <= 9999:  # Valid article range
                        entities['articles'].append(article_num)
                except ValueError:
                    continue
        
        # Extract Laws
        for pattern in self.LAW_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities['laws'].extend(matches)
        
        # Deduplicate
        entities['articles'] = sorted(list(set(entities['articles'])))
        entities['laws'] = list(set([str(law) for law in entities['laws']]))
        
        return entities
    
    def _extract_legal_nouns_from_query(self, query: str) -> List[str]:
        """
        Fallback: Extract legal nouns directly from query
        Filters out stop words and short words
        """
        if not query:
            return []
        
        words = re.findall(r'[\w\u0600-\u06FF]+', query)
        legal_nouns = []
        
        for word in words:
            word_clean = word.strip()
            word_lower = word_clean.lower()
            
            # Filter conditions
            if (len(word_clean) > 2 and 
                word_lower not in self.STOP_WORDS and
                not word_clean.isdigit()):
                legal_nouns.append(word_clean)
        
        return legal_nouns
    
    # ==================== SCOUT PHASE ====================
    
    async def _adaptive_scout_phase(
        self, 
        query: str,
        query_type: str,
        country_id: Optional[str]
    ) -> Tuple[List[str], Dict, bool]:
        """
        🔍 Enhanced Scout Phase v3.0 (Multi-Stage)
        
        Stage 1: Initial Vector Search (broader)
        Stage 2: Entity Extraction from results
        Stage 3: LLM Analysis with Query-Type awareness
        Stage 4: Keyword Expansion with context
        
        Returns: (keywords, legal_entities, found_matches)
        """
        embeddings = get_embeddings()
        query_vector = None
        
        try:
            # Embedding with timeout
            query_vector = await asyncio.wait_for(
                embeddings.aembed_query(query), 
                timeout=3.0
            )
        except asyncio.TimeoutError:
            logger.warning("⚠️ Embedding Service Timeout (Scout Phase) - using fallback")
        except Exception as e:
            logger.warning(f"⚠️ Embedding Service Failed (Scout Phase): {e}")
        
        initial_docs = []
        found_matches = False

        # Stage 1: Vector Search
        if query_vector:
            try:
                initial_res = self.vector_tool.run(
                    query_vector=query_vector,
                    match_count=12,  # Increased for better coverage
                    filter={"country_id": country_id} if country_id else {}
                )
                
                if initial_res.success and initial_res.data:
                    found_matches = True
                    initial_docs = initial_res.data
            except Exception as e:
                logger.warning(f"⚠️ Vector Search Failed (Scout Phase): {e}")
        
        # Fallback: Keyword Search if vector failed
        if not initial_docs:
            logger.info("ℹ️ Vector Search yielded no results. Engaging Keyword Fallback...")
            try:
                keyword_res = self.keyword_tool.run(
                    query=query, 
                    limit=12, 
                    country_id=country_id
                )
                if keyword_res.success and keyword_res.data:
                    initial_docs = keyword_res.data
                    found_matches = True
            except Exception as e:
                logger.warning(f"⚠️ Keyword Fallback Failed (Scout Phase): {e}")
        
        if not initial_docs:
            logger.warning("⚠️ No documents found in Scout Phase")
            return [], {}, False
        
        # Stage 2: Extract Entities from Results
        combined_entities = defaultdict(list)
        context_chunks = []
        
        for doc in initial_docs[:6]:  # Top 6 for context
            content = doc.get('content', '')
            entities = self._extract_legal_entities(content)
            
            for key, values in entities.items():
                if key != 'ranges':  # Don't add ranges to combined
                    combined_entities[key].extend(values)
            
            # Build context preview
            context_chunks.append(content[:800])
        
        # Deduplicate entities
        combined_entities['articles'] = sorted(list(set(combined_entities['articles'])))
        combined_entities['laws'] = list(set(combined_entities['laws']))
        
        context_preview = "\n---\n".join(context_chunks)
        
        # Stage 3: Enhanced LLM Analysis with Query Type Awareness
        llm = get_llm(temperature=0.0)
        
        entities_str = ""
        if combined_entities.get('articles'):
            articles_preview = combined_entities['articles'][:20]  # First 20
            entities_str += f"\n- Article Numbers Found: {articles_preview}"
            if len(combined_entities['articles']) > 20:
                entities_str += f" (+ {len(combined_entities['articles']) - 20} more)"
        
        if combined_entities.get('laws'):
            entities_str += f"\n- Laws/Regulations Found: {combined_entities['laws'][:5]}"
        
        # ✅ CRITICAL: Query-Type-Aware Prompt
        prompt = self._build_scout_prompt(
            query=query,
            query_type=query_type,
            context_preview=context_preview[:1500],
            entities_str=entities_str
        )
        
        try:
            response = await llm.ainvoke([SystemMessage(content=prompt)])
            analysis_text = response.content.strip()
            
            # Extract keywords from LLM analysis
            detected_keywords = []
            for line in analysis_text.split('\n'):
                if ',' in line:
                    parts = [p.strip() for p in line.split(',')]
                    detected_keywords.extend([p for p in parts if p and len(p) > 2])
            
            # If no keywords from LLM, use fallback
            if not detected_keywords:
                detected_keywords = self._extract_legal_nouns_from_query(query)
            
            # ✅ NEW: Expand keywords with Arabic morphology
            from .arabic_morphology import ArabicMorphology
            
            # Extract main legal terms (not articles, not generic words)
            core_legal_terms = []
            for kw in detected_keywords[:5]:  # Top 5 keywords
                # Skip if it's an article reference or generic
                if not any(x in kw for x in ["المادة", "Article", "تعريف", "معنى"]):
                    core_legal_terms.append(kw)
            
            # Expand with conjugations
            expanded_keywords = list(detected_keywords)  # Keep originals
            for term in core_legal_terms[:3]:  # Top 3 legal terms only
                conjugations = ArabicMorphology.get_conjugations(term)
                expanded_keywords.extend(conjugations[:5])  # Add top 5 conjugations
            
            # Remove duplicates while preserving order
            seen = set()
            final_keywords = []
            for kw in expanded_keywords:
                if kw not in seen:
                    seen.add(kw)
                    final_keywords.append(kw)
            
            # Add article-specific keywords if present in entities
            if combined_entities.get('articles'):
                for article in combined_entities['articles'][:3]:
                    final_keywords.append(f"المادة {article}")
                    final_keywords.append(f"Article {article}")
            
            # Limit to reasonable size
            final_keywords = final_keywords[:40]
            
            return final_keywords, dict(combined_entities), found_matches
            
        except Exception as e:
            logger.warning(f"Scout LLM Analysis Failed: {e}")
            # Fallback to direct extraction
            fallback_keywords = self._extract_legal_nouns_from_query(query)
            return fallback_keywords, dict(combined_entities), found_matches
    
    def _build_scout_prompt(
        self, 
        query: str, 
        query_type: str, 
        context_preview: str, 
        entities_str: str
    ) -> str:
        """
        Build query-type-aware prompt for Scout phase
        """
        base_prompt = f"""
🎯 **You are a LEGAL PRACTITIONER, not an academic researcher.**

Your role: Extract **practical legal keywords** that a lawyer would use to find relevant provisions.

**Original Query:** {query}

**Query Type Detected:** {query_type}

**Context from Database:**
{context_preview}

**Entities Found:**
{entities_str}

**Technical Context:**
- Database: Supabase PostgreSQL
- Search uses: ILIKE (case-insensitive pattern matching)
- Keywords will be used in SQL queries

⚠️ **CRITICAL RULES - Legal Practitioner Mindset:**

1. **NO ACADEMIC WORDS:**
   - ❌ Avoid: "تعريف", "معنى", "المقصود", "شرح", "توضيح", "دراسة"
   - ✅ Use: Actual legal terms, conjugations, related concepts

2. **THINK LIKE A LAWYER:**
   - Focus on **legal provisions**, not definitions
   - Use **specific legal terminology**
   - Include **conjugations** of legal terms
   
3. **CONJUGATION EXAMPLES:**
   - "هبة" → ["هبة", "واهب", "موهوب له", "الموهوب", "هبته"]
   - "بيع" → ["بيع", "بائع", "مشتري", "المبيع", "البائع"]
   - "عقد" → ["عقد", "عاقد", "متعاقد", "التعاقد", "المتعاقدين"]

4. **PRACTICAL FOCUS:**
   - Look for: procedures, rights, obligations, penalties
   - Not: theoretical explanations, academic analysis
"""
        
        # ✅ Query-Type-Specific Instructions
        if query_type == 'ARTICLE_ENUMERATION':
            base_prompt += """
**⚠️ CRITICAL - Article Enumeration Query Detected:**

This query asks "WHICH ARTICLES" or "WHAT ARTICLES" deal with a topic.

**Your Goal:** Help find documents that:
1. Contain LISTS of article numbers
2. Have table of contents or indexes
3. Show article ranges (e.g., "Articles 488-514 on Gifts")

**Required Keywords:**
1. Core legal term (e.g., "gift", "الهبة")
2. Related terms (e.g., "donor", "الواهب", "donee", "الموهوب له")
3. Structure keywords: "فهرس", "جدول المحتويات", "index", "table of contents"
4. ANY article numbers found in context

**Example Output:**
الهبة, الواهب, الموهوب له, عقد الهبة, المادة 488, المادة 490, فهرس, جدول المحتويات

"""
        
        elif query_type == 'DEFINITION':
            base_prompt += """
**Definition Query Detected:**

Focus on:
1. The exact term to define
2. Related terminology
3. Keywords like "تعريف", "definition", "معنى", "meaning"

"""
        
        elif query_type == 'PROCEDURE':
            base_prompt += """
**Procedure Query Detected:**

Focus on:
1. Action verbs and procedural terms
2. Keywords like "إجراءات", "خطوات", "procedure", "steps"
3. Temporal indicators

"""
        
        else:  # GENERAL or other types
            base_prompt += """
**General Legal Query:**

Focus on:
1. Core legal concepts
2. Relevant legal entities (parties, objects)
3. Action terms if applicable

"""
        
        # Common rules for all types
        base_prompt += """
**⚠️ STRICT RULES (Apply to ALL query types):**

1. **NOUNS ONLY** - Extract legal nouns, not verbs/prepositions
   ✅ Allowed: "الهبة", "gift", "contract", "عقد"
   ❌ Forbidden: "ما", "what", "في", "in", "عن", "about"

2. **NO STOP WORDS** - Filter out common words

3. **MULTILINGUAL** - Include terms in original language + English if relevant

4. **ARTICLE NUMBERS** - If any article numbers appear in context, INCLUDE them as keywords

5. **FORMAT** - Use English commas (,) as separators, NO other punctuation

**Output Format (exact, comma-separated):**
keyword1, keyword2, keyword3, المادة X, Article Y, ...

Provide ONLY the comma-separated keywords, nothing else.
"""
        
        return base_prompt
    
    def _process_llm_keywords(self, text_resp: str) -> List[str]:
        """
        Process LLM response to extract clean keywords
        """
        keywords = []
        
        # Split by commas
        parts = text_resp.split(',')
        
        for part in parts:
            keyword = part.strip()
            
            # Clean various quotation marks
            keyword = keyword.strip('"\'""''«»')
            
            # Filter
            if (keyword and 
                len(keyword) > 2 and 
                keyword.lower() not in self.STOP_WORDS and
                not keyword.isdigit()):
                keywords.append(keyword)
        
        return keywords
    
    # ==================== SNIPER PHASE ====================
    
    async def _precision_sniper_phase(
        self,
        original_query: str,
        query_type: str,
        expanded_keywords: List[str],
        query_entities: Dict[str, List],
        country_id: Optional[str],
        limit: int,
        source_id_filter: Optional[str] = None  # NEW: Law filter
    ) -> List[Dict]:
        """
        🎯 COMPLETELY REWRITTEN: Direct SQL Search with Variants
        
        OLD Approach: Vector + Keyword → query dilution ❌
        NEW Approach: SQL ILIKE with Arabic variants → precise ✅
        """
        from agents.config.database import db
        
        # Extract core legal term (first non-generic keyword)
        generic_terms = {
            "تعريف", "معنى", "المقصود", "شروط", "إجراءات", "خطوات",
            "كيفية", "قائمة", "فهرس", "جدول", "ما", "هي", "هو",
            "definition", "meaning", "defined", "conditions", "procedure",
            "process", "steps", "list", "index", "table", "what", "is"
        }
        
        core_term = None
        for kw in expanded_keywords:
            if kw.lower() not in generic_terms and len(kw) > 2:
                core_term = kw
                break
        
        if not core_term:
            # Fallback: use original query
            core_term = original_query.split()[0] if original_query else "قانون"
        
        logger.info(f"🎯 Core Term: '{core_term}'")
        
        # Generate Arabic variants
        variants = self._generate_arabic_variants(core_term)
        logger.info(f"🔎 Searching for variants: {variants}")
        
        # Build SQL OR conditions
        try:
            # Method 1: Try OR query
            or_conditions = ','.join([f"content.ilike.%{v}%" for v in variants])
            
            query_builder = db.client.table('document_chunks') \
                .select('id, content, source_id, sequence_number, hierarchy_path, keywords')
            
            # Apply filters
            if country_id:
                query_builder = query_builder.eq('country_id', country_id)
            
            # ✅ NEW: Apply law filter (source_id)
            if source_id_filter:
                query_builder = query_builder.eq('source_id', source_id_filter)
                logger.info(f"📊 Applied law filter: source_id = {source_id_filter}")
            
            result = query_builder \
                .or_(or_conditions) \
                .limit(50) \
                .execute()
            
            candidates = result.data if result.data else []
            
            logger.info(f"✅ SQL Search: {len(candidates)} candidates found")
            
        except Exception as e:
            logger.error(f"❌ SQL Search Failed: {e}")
            candidates = []
        
        if not candidates:
            return []
        
        # Score and rank
        scored_docs = []
        
        for doc in candidates:
            content = doc.get('content', '')
            content_lower = content.lower()
            
            # Simple rule-based scoring
            score = 0.0
            
            # Rule 1: Term appears in first 300 chars (+3 points)
            if any(v.lower() in content[:300].lower() for v in variants):
                score += 3.0
            
            # Rule 2: Term appears in hierarchy (+5 points)
            hierarchy = doc.get('hierarchy_path', '')
            if hierarchy and any(v.lower() in hierarchy.lower() for v in variants):
                score += 5.0
            
            #Rule 3: Term frequency (count occurrences)
            total_count = sum(content_lower.count(v.lower()) for v in variants)
            if total_count >= 2:
                score += 2.0
            if total_count >= 3:
                score += 2.0
            if total_count >= 5:
                score += 1.0
            
            # Rule 4: Legal context keywords
            legal_keywords = ['المادة', 'الباب', 'الفصل', 'النظام', 'القانون', 'أحكام', 'شروط']
            if any(kw in content[:500] for kw in legal_keywords):
                score += 1.0
            
            # Rule 5: Article numbers present
            doc_entities = self._extract_legal_entities(content)
            if doc_entities.get('articles'):
                score += 1.0
            
            # Store
            doc['relevance_score'] = score
            doc['search_method'] = 'SQL_ILIKE'
            
            if score > 0:  # Only keep docs with positive score
                scored_docs.append(doc)
        
        # Sort by score
        scored_docs.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        logger.info(f"📊 Scored {len(scored_docs)} documents")
        
        # Return top results
        return scored_docs[:limit * 2]  # Return 2x limit for diversity filter,
    
    def _build_sniper_query(
        self,
        query_type: str,
        expanded_keywords: List[str],
        query_entities: Dict
    ) -> str:
        """
        ✅ FIXED: Build optimized query WITHOUT dilution
        
        OLD Problem: "الهبة" + "تعريف" + "معنى" → finds ANY doc with "تعريف"  ❌
        NEW Solution: Core terms ONLY, minimal modifiers ✅
        """
        # Separate core legal terms from generic modifiers
        generic_terms = {
            "تعريف", "معنى", "المقصود", "شروط", "إجراءات", "خطوات",
            "كيفية", "قائمة", "فهرس", "جدول",
            "definition", "meaning", "defined", "conditions", "procedure",
            "process", "steps", "list", "index", "table"
        }
        
        core_terms = []
        modifiers = []
        
        for kw in expanded_keywords[:15]:
            if kw.lower() in generic_terms:
                modifiers.append(kw)
            else:
                core_terms.append(kw)
        
        query_parts = []
        
        # ✅ Priority 1: Core legal terms (MAX 5)
        if core_terms:
            query_parts.extend(core_terms[:5])
        else:
            # Fallback: use expanded_keywords as-is
            query_parts.extend(expanded_keywords[:3])
        
        # ✅ Priority 2: Entity terms (articles)
        if query_entities.get('articles'):
            for article in query_entities['articles'][:3]:  # Reduced from 8!
                query_parts.append(f"المادة {article}")
        
        # ✅ Priority 3: Add modifiers ONLY if relevant (MAX 2)
        if query_type == 'DEFINITION' and modifiers:
            def_mods = [m for m in modifiers if m.lower() in {"تعريف", "معنى", "definition", "meaning"}]
            query_parts.extend(def_mods[:2])
        elif query_type == 'PROCEDURE' and modifiers:
            proc_mods = [m for m in modifiers if m.lower() in {"إجراءات", "خطوات", "procedure", "steps"}]
            query_parts.extend(proc_mods[:2])
        
        final_query = ' '.join(query_parts)
        logger.info(f"🎯 Sniper Query: '{final_query[:100]}...'")
        
        return final_query
    
    def _calculate_legal_relevance_score(
        self,
        doc: Dict,
        query: str,
        query_type: str,
        expanded_keywords: List[str],
        query_entities: Dict
    ) -> float:
        """
        🎯 Advanced Legal Relevance Scoring v3.0
        
        Base Components (70%):
        1. Base Similarity/Density (30%)
        2. Legal Entity Matching (20%)
        3. Keyword Enrichment (20%)
        
        Type-Specific Bonus (30%):
        4. Query Type Bonus (30%)
        """
        content = doc.get('content', '')
        if not content:
            return 0.0
        
        normalized_content = self._normalize_arabic(content)
        normalized_query = self._normalize_arabic(query)
        
        # --- Component 1: Base Similarity (30%) ---
        if 'similarity' in doc:
            base_score = min(doc['similarity'], 1.0)
        else:
            # Term matching with normalization
            query_terms = set(normalized_query.split())
            content_words = set(normalized_content.split())
            
            if not query_terms:
                overlap_ratio = 0
            else:
                exact_matches = len(query_terms & content_words)
                partial_matches = sum(
                    1 for term in query_terms 
                    if any(term in word for word in content_words)
                )
                
                overlap_ratio = min(
                    (exact_matches * 1.0 + partial_matches * 0.5) / len(query_terms),
                    1.0
                )
            
            base_score = overlap_ratio * 0.85
        
        # --- Component 2: Entity Matching (20%) ---
        # ✅ FIX: Extract entities from ORIGINAL QUERY, not from analyst results
        # Old bug: Scout was using analyst-extracted keywords which could be wrong
        scout_entities = self._extract_legal_entities(query)
        
        # Consolidate keywords from both sources
        # Note: 'expanded_keywords' here refers to the keywords passed into this function,
        # which might be from an earlier analysis step.
        # We're adding the original query terms and scouted articles to this list for enrichment.
        detected_keywords = expanded_keywords # Rename for clarity if needed, or just use expanded_keywords
        
        expanded_keywords = list(set(
            detected_keywords[:20] +  # From analyst (or previous expansion)
            [query]  # Include original query
        ))
        
        # ✅ NEW: If query contains article numbers, prioritize them
        if scout_entities.get('articles'):
            logger.info(f"🎯 Detected articles in original query: {scout_entities['articles']}")
            # Add article-specific keywords
            for article_num in scout_entities['articles'][:5]:
                expanded_keywords.append(f"المادة {article_num}")
                expanded_keywords.append(f"مادة {article_num}")
        
        entity_score = 0.0
        doc_entities = self._extract_legal_entities(content)
        
        # Article matching
        # Use scout_entities for query articles, as per the fix
        if scout_entities.get('articles'):
            query_articles = set(scout_entities['articles'])
            doc_articles = set(doc_entities['articles'])
            
            intersection = query_articles & doc_articles
            if intersection:
                # Exact article match = high value
                entity_score += min(len(intersection) * 0.15, 0.5)
        
        # General article presence bonus
        if doc_entities.get('articles') and len(doc_entities['articles']) >= 3:
            entity_score += 0.1
        
        # Law reference matching
        if query_entities.get('laws') and doc_entities.get('laws'):
            entity_score += 0.15
        
        norm_entity_score = min(entity_score, 1.0)
        
        # --- Component 3: Keyword Enrichment (20%) ---
        keyword_score = 0.0
        
        for kw in expanded_keywords[:20]:
            normalized_kw = self._normalize_arabic(kw.lower())
            if normalized_kw in normalized_content.lower():
                keyword_score += 1.0
        
        norm_keyword_score = min(keyword_score / 15.0, 1.0)
        
        # --- Component 4: Query Type Bonus (30%) ---
        type_bonus = self._calculate_type_specific_bonus(
            query_type=query_type,
            doc=doc,
            content=content,
            doc_entities=doc_entities
        )
        
        # --- Final Weighted Score ---
        final_score = (
            base_score * 0.30 +
            norm_entity_score * 0.20 +
            norm_keyword_score * 0.20 +
            type_bonus * 0.30
        )
        
        return final_score
    
    def _calculate_type_specific_bonus(
        self,
        query_type: str,
        doc: Dict,
        content: str,
        doc_entities: Dict
    ) -> float:
        """
        Calculate query-type-specific bonus score
        """
        bonus = 0.0
        content_lower = content.lower()
        
        if query_type == 'ARTICLE_ENUMERATION':
            # ✅ CRITICAL: Bonus for documents with many articles
            article_count = len(doc_entities.get('articles', []))
            
            if article_count >= 15:
                bonus += 0.8  # Excellent - comprehensive list
            elif article_count >= 10:
                bonus += 0.6
            elif article_count >= 5:
                bonus += 0.4
            elif article_count >= 2:
                bonus += 0.2
            
            # Bonus for structure indicators
            structure_patterns = [
                r'(فهرس|جدول المحتويات|قائمة المواد)',
                r'(index|table of contents|list of articles)',
                r'(الباب|الفصل|القسم|Chapter|Section)',
            ]
            
            for pattern in structure_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    bonus += 0.15
                    break
            
            # Bonus for range indicators
            if re.search(r'(من.*إلى|المواد.*\d+.*\d+)', content):
                bonus += 0.1
        
        elif query_type == 'DEFINITION':
            # Bonus for definition indicators
            definition_patterns = [
                r'(يقصد بـ|المقصود|يعرف|تعريف)',
                r'(means|defined as|refers to|definition)',
            ]
            
            for pattern in definition_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    bonus += 0.4
                    break
            
            # Bonus for being concise (definitions are usually short)
            if 200 <= len(content) <= 1500:
                bonus += 0.2
        
        elif query_type == 'PROCEDURE':
            # Bonus for procedural language
            procedure_patterns = [
                r'(يجب|ينبغي|يتعين|الخطوات|الإجراءات)',
                r'(must|shall|should|steps|procedure)',
                r'(أولا|ثانيا|ثالثا)',
                r'(first|second|third|then|next)',
            ]
            
            matches = 0
            for pattern in procedure_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    matches += 1
            
            bonus += min(matches * 0.15, 0.6)
        
        elif query_type == 'CONDITION':
            # Bonus for conditional language
            condition_patterns = [
                r'(إذا|في حالة|بشرط|يشترط)',
                r'(if|when|provided|subject to|condition)',
            ]
            
            for pattern in condition_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    bonus += 0.3
                    break
        
        else:  # GENERAL or COMPARISON
            # General quality signals
            content_length = len(content)
            if 500 < content_length < 3000:
                bonus += 0.3
            elif 3000 <= content_length < 8000:
                bonus += 0.2
            
            # Structure bonus
            if re.search(r'(الفصل|الباب|القسم|Chapter)', content):
                bonus += 0.2
        
        return min(bonus, 1.0)
    
    def _apply_diversity_filter(
        self,
        ranked_results: List[Dict],
        limit: int,
        query_type: str
    ) -> List[Dict]:
        """
        Apply diversity filter to avoid too similar results
        More lenient for ARTICLE_ENUMERATION queries
        """
        final_results = []
        seen_content_hashes = set()
        
        # Adjust hash length based on query type
        hash_length = 300 if query_type == 'ARTICLE_ENUMERATION' else 200
        
        for doc in ranked_results:
            content = doc.get('content', '')
            
            # Hash based on content
            content_hash = hash(content[:hash_length])
            
            if content_hash not in seen_content_hashes:
                seen_content_hashes.add(content_hash)
                final_results.append(doc)
            
            if len(final_results) >= limit:
                break
        
        return final_results
    
    # ==================== MAIN EXECUTION ====================
    
    async def run(
        self,
        query: str,
        limit: int = 5,
        filter: Optional[Dict] = None,
        country_id: Optional[str] = None,
        law_filter: Optional[str] = None  # NEW: Filter by law name
    ) -> ToolResult:
        """
        Main execution flow with enhanced logging and safeguards
        
        Args:
            query: Search query
            limit: Max results
            filter: Additional filters
            country_id: Filter by country
            law_filter: Filter by law name (e.g., "المعاملات المدنية")
                       If provided, search will be restricted to this law only
        """
        self._track_usage()
        start = time.time()
        
        try:
            # ============ NEW: COUNTRY VALIDATION LAYER ============
            # Protect against queries for non-existent or non-Arabic countries
            if country_id:
                logger.info(f"🌍 Validating country: {country_id[:8]}...")
                
                # Check if country exists and is active
                try:
                    country_check = db.client.from_("countries")\
                        .select("id, code, name_ar, name_en, is_active")\
                        .eq("id", country_id)\
                        .eq("is_active", True)\
                        .execute()
                    
                    if not country_check.data or len(country_check.data) == 0:
                        # Country not found or not active
                        logger.warning(f"⚠️  Country {country_id[:8]} not found or inactive")
                        return ToolResult(
                            success=False,
                            error=f"لا تتوفر معلومات قانونية لهذه الدولة في قاعدة البيانات.",
                            message="الدولة المطلوبة غير مدعومة أو غير نشطة حالياً."
                        )
                    
                    country_name = country_check.data[0].get("name_ar", "Unknown")
                    country_code = country_check.data[0].get("code", "")
                    
                    logger.info(f"✅ Country validated: {country_name} ({country_code})")
                    
                except Exception as e:
                    logger.error(f"❌ Country validation error: {e}")
                    return ToolResult(
                        success=False,
                        error=f"لا تتوفر معلومات قانونية لهذه الدولة في قاعدة البيانات.",
                        message="حدث خطأ أثناء التحقق من الدولة."
                    )
            
            # ============ EXISTING: LAW FILTERING LOGIC ============
            # ============ NEW: LAW FILTERING LOGIC ============
            source_id_filter = None
            
            if law_filter:
                logger.info(f"🔍 Law Filter: Resolving '{law_filter}'...")
                
                # Use LawIdentifierTool to resolve law name → source_id
                law_result = self.law_identifier.run(
                    law_query=law_filter,
                    country_id=country_id,
                    min_confidence=0.6
                )
                
                if law_result.success:
                    source_id_filter = law_result.data["best_match"]["source_id"]
                    law_title = law_result.data["best_match"]["official_title"]
                    confidence = law_result.data["best_match"]["confidence"]
                    
                    logger.info(f"✅ Law Resolved: {law_title} (confidence: {confidence:.2%})")
                    logger.info(f"📊 Filtering search to source_id: {source_id_filter}")
                else:
                    # Law not found - return error
                    return ToolResult(
                        success=False,
                        error=f"لم أتمكن من العثور على النظام: {law_filter}\n{law_result.error}"
                    )
            # ============ END LAW FILTERING LOGIC ============
            
            # Detect query type
            query_type = self._detect_query_type(query)
            
            # Extract entities from query
            query_entities = self._extract_legal_entities(query)
            logger.info(f"Query Entities: {query_entities}")
            
            # Phase 1: Enhanced Scout
            logger.info(f"🕵️‍♂️ Enhanced Scout Phase (Query Type: {query_type})...")
            keywords, scout_entities, found_matches = await self._adaptive_scout_phase(
                query=query,
                query_type=query_type,
                country_id=country_id
            )
            
            # Merge entities
            all_entities = {
                'articles': sorted(list(set(
                    query_entities.get('articles', []) + 
                    scout_entities.get('articles', [])
                ))),
                'laws': list(set(
                    query_entities.get('laws', []) + 
                    scout_entities.get('laws', [])
                ))
            }
            
            logger.info(f"Scout Results: Keywords={keywords[:10]}..., Entities={all_entities}")
            
            # Enhanced Kill Switch (more lenient for article enumeration)
            if query_type == 'ARTICLE_ENUMERATION':
                # For article enumeration, proceed even with weak signals
                if not found_matches and not keywords and not all_entities.get('articles'):
                    logger.warning("⛔ Kill Switch: No signal detected (Article Enumeration)")
                    return ToolResult(success=True, data=[])
            else:
                # Standard kill switch for other types
                if not found_matches and not keywords:
                    logger.warning("⛔ Kill Switch: No signal detected")
                    return ToolResult(success=True, data=[])
            
            # Phase 2: Precision Sniper
            logger.info("🎯 Precision Sniper Phase...")
            final_results = await self._precision_sniper_phase(
                original_query=query,
                query_type=query_type,
                expanded_keywords=keywords,
                query_entities=all_entities,
                country_id=country_id,
                limit=limit,
                source_id_filter=source_id_filter  # NEW: Pass law filter
            )
            
            # ✅ FIX: Apply diversity filter
            if final_results:
                final_results = self._apply_diversity_filter(
                    ranked_results=final_results,
                    limit=limit,
                    query_type=query_type
                )
            
            # ⚠️ DISABLED: Quality Guardrail (was blocking valid results)
            # The simple rule-based scoring is accurate enough
            
            # Log results
            execution_time = time.time() - start
            logger.info(f"✅ Search Complete: {len(final_results)} results in {execution_time:.2f}s")
            
            return ToolResult(
                success=True,
                data=final_results,
                metadata={
                    "execution_time": execution_time,
                    "query_type": query_type,
                    "scout_keywords": keywords[:15],
                    "extracted_entities": all_entities,
                    "total_candidates": len(final_results),
                },
                execution_time_ms=int(execution_time * 1000)
            )
            
        except Exception as e:
            logger.error(f"LHSE-Pro v3.0 Failed: {e}", exc_info=True)
            return ToolResult(success=False, error=str(e))