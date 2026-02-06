# 🔧 تقرير التشخيص: مشكلة HybridSearchTool

**التاريخ:** 2026-02-05  
**الحالة:** 🔴 مشكلة حرجة مُكتشفة  
**الأولوية:** عالية جداً

---

## 📊 نتائج الاختبار

### ✅ **ما يعمل:**

| الأداة | الحالة | النتائج |
|--------|--------|---------|
| SQL Direct Search | ✅ | 8 شرائح تحتوي على "الهبة" |
| FlexibleSearchTool | ✅ | 5 نتائج صحيحة |
| VectorSearchTool | ⚠️ | 5 نتائج (Similarity منخفض: 0.31) |
| HybridSearchTool | ❌ | 5 نتائج **خاطئة تماماً** |

### ❌ **المشكلة:**

**الاستعلام:** `"ما هي الهبة"`

**النتائج المتوقعة:**
- مواد من القانون المدني عن الهبة
- تعريفات قانونية للهبة
- شروط عقد الهبة

**النتائج الفعلية من HybridSearchTool:**
1. نظام الإحصاء (Score: 0.4317) ❌
2. نظام وحدات الإخصاب والأجنة (Score: 0.4183) ❌
3. ضوابط شراء المركبات (Score: 0.3883) ❌

---

## 🔍 تحليل السبب الجذري

### 1. **Scout Phase يعمل بشكل صحيح**

```json
{
  "scout_keywords": ["الهبة", "gift", "تعريف", "definition", "معنى"],
  "articles_found": []  // ⚠️ لم يجد أرقام مواد!
}
```

**الملاحظات:**
- ✅ Keywords صحيحة
- ⚠️ لم يُستخرج أي `article_numbers` (لأن الاستعلام لم يذكر مادة معينة)
- ✅ Query Type غالباً `DEFINITION` (بسبب "ما هي")

### 2. **Sniper Phase - المشكلة الرئيسية**

**الكود المُشتبه فيه:**
```python
# File: hybrid_search_tool.py:645-684
def _build_sniper_query(
    query_type: str,
    expanded_keywords: List[str],
    query_entities: Dict
):
    query_parts = []
    
    # Base keywords
    query_parts.extend(expanded_keywords[:15])  # ✅ يأخذ أول 15 كلمة
    
    # Type-specific additions
    if query_type == 'DEFINITION':
        query_parts.extend([
            "تعريف", "معنى", "المقصود",
            "definition", "meaning", "defined"
        ])
    
    return ' '.join(query_parts)  // ⚠️ يُحوّل لنص واحد
```

**النص المُرسَل للبحث:**
```
"الهبة gift تعريف definition معنى تعريف معنى المقصود definition meaning defined"
```

**المشكلة المحتملة:**
1. **Vector Search** يبحث عن هذا النص الطويل
2. **النتائج تتطابق مع كلمات عامة** مثل "تعريف" و "معنى"
3. **أي نظام يبدأ بـ "تعريف" يحصل على نقاط عالية!**

### 3. **Scoring System - مشكلة ثانوية**

```python
# File: hybrid_search_tool.py:686-786
final_score = (
    base_similarity * 0.30 +      # ⚠️ Similarity منخفض لكن يُحسب
    norm_entity_score * 0.20 +    # ⚠️ صفر (لا توجد مواد مُستخرجة)
    norm_keyword_score * 0.20 +   # ⚠️ يتطابق مع "تعريف" فقط!
    type_bonus * 0.30             # ⚠️ DEFINITION bonus خاطئ
)
```

**تحليل النقاط:**

| المستند | Base Sim | Entity | Keyword | Type Bonus | **Final** |
|---------|----------|--------|---------|------------|-----------|
| نظام الإحصاء | 0.15 | 0.0 | **0.80** | **0.70** | **0.43** |
| الهبة الحقيقية | 0.30 | 0.0 | **0.20** | 0.30 | **0.26** |

**السبب:**
- نظام الإحصاء يحتوي على كلمات "تعريف، معنى، المقصود" كثيراً (Keyword Score عالي)
- Type Bonus يُعطي نقاط لأي مستند يحتوي على "تعريف"
- المستند الحقيقي عن "الهبة" يحصل على نقاط أقل!

---

## 🐛 الأخطاء المُكتشفة

### Error #1: Query Dilution (تخفيف الاستعلام)

**المشكلة:**
```python
# ❌ الكود الحالي
query = "الهبة gift تعريف definition معنى تعريف معنى المقصود"
```

**الحل المقترح:**
```python
# ✅ الكود المُقترح
query = "الهبة"  # Main term ONLY for vector search
keywords = ["gift", "تعريف", "معنى"]  # Use for keyword search separately
```

### Error #2: Generic Keyword Bonus (مكافأة الكلمات العامة)

**المشكلة:**
```python
# ❌ يُعطي نقاط لأي مستند يحتوي على "تعريف"
if query_type == 'DEFINITION':
    type_bonus += 0.5  # إذا وجد "تعريف" في المستند
```

**الحل المقترح:**
```python
# ✅ يُعطي نقاط فقط إذا كان "تعريف الهبة" معاً
if query_type == 'DEFINITION':
    if "تعريف" in content and "الهبة" in content:  # Proximity check
        type_bonus += 0.5
```

### Error #3: Missing Keyword Filtering (عدم تصفية الكلمات)

**المشكلة:**
- Scout يُنتج: `["الهبة", "gift", "تعريف", "definition", "معنى"]`
- Sniper يستخدم **كل الكلمات** مما يُضعف الدقة

**الحل المقترح:**
```python
# Separate core terms from context terms
core_terms = ["الهبة", "gift"]         # Must appear
context_terms = ["تعريف", "معنى"]      # Optional boosters

# Build query with priority
vector_query = " ".join(core_terms)  # For semantic search
keyword_query = core_terms + context_terms  # For SQL ILIKE
```

---

## 🔧 الحلول المقترحة

### الحل السريع (Quick Fix) - 30 دقيقة

**1. تعديل `_build_sniper_query`:**

```python
def _build_sniper_query(
    query_type: str,
    expanded_keywords: List[str],
    query_entities: Dict
) -> str:
    # ✅ FIX: Separate core terms from modifiers
    core_terms = []
    modifiers = []
    
    generic_terms = {"تعريف", "معنى", "definition", "meaning", "شروط", "إجراءات"}
    
    for kw in expanded_keywords[:15]:
        if kw.lower() in generic_terms:
            modifiers.append(kw)
        else:
            core_terms.append(kw)
    
    # ✅ Prioritize core terms
    if core_terms:
        query_parts = core_terms[:5]  # Max 5 core terms
    else:
        query_parts = expanded_keywords[:3]  # Fallback
    
    # Add modifiers only if relevant
    if query_type == 'DEFINITION' and modifiers:
        query_parts.extend(modifiers[:2])  # Max 2 modifiers
    
    return ' '.join(query_parts)
```

**2. تعديل `_calculate_legal_relevance_score`:**

```python
# ✅ FIX: Keyword matching with proximity
keyword_score = 0.0
core_keywords = [kw for kw in expanded_keywords[:5] 
                 if kw.lower() not in {"تعريف", "معنى", "definition"}]

for kw in core_keywords:
    normalized_kw = self._normalize_arabic(kw.lower())
    if normalized_kw in normalized_content.lower():
        keyword_score += 2.0  # Double weight for core terms
    
# Bonus for proximity (e.g., "تعريف الهبة" together)
if query_type == 'DEFINITION':
    for core in core_keywords:
        pattern = f"تعريف.*{core}|{core}.*تعريف"
        if re.search(pattern, content, re.IGNORECASE):
            keyword_score += 1.0

norm_keyword_score = min(keyword_score / 15.0, 1.0)
```

### الحل المتوسط (Medium Fix) - 2 ساعات

**إعادة هيكلة Sniper Phase:**

```python
async def _precision_sniper_phase(...):
    # 1. Dual-track search
    core_query = self._extract_core_terms(expanded_keywords)
    
    # Vector Search with CORE TERMS ONLY
    v_res = await vector_search(core_query)
    
    # Keyword Search with ALL TERMS (but weighted)
    k_res = await keyword_search(expanded_keywords)
    
    # 2. Merge with weighted deduplication
    candidates = self._merge_results(v_res, k_res, weights={
        'vector': 0.6,  # Prioritize semantic
        'keyword': 0.4
    })
    
    # 3. Re-rank with proximity scoring
    ranked = self._rerank_with_proximity(
        candidates, 
        core_terms=core_query,
        context_terms=expanded_keywords
    )
    
    return ranked[:limit]
```

### الحل الطويل الأمد (Long-term Fix) - 1 أسبوع

**1. Query Understanding Layer:**
- إضافة Named Entity Recognition (NER) للقانون
- استخراج المصطلحات القانونية تلقائياً
- بناء قاموس مرادفات قانوني

**2. Re-ranking Model:**
- استخدام Cross-Encoder للـ Re-ranking
- تدريب Model على استعلامات قانونية حقيقية
- Fine-tuning على البيانات السعودية

**3. Query Expansion Intelligence:**
- استخدام LLM لتوليد variations ذكية
- مثال: "الهبة" → ["عقد الهبة", "الواهب", "الموهوب له", "التبرع"]

---

## 🧪 خطة الاختبار

### Test Case #1: الهبة
```python
query = "ما هي الهبة"
expected_keywords = ["الهبة", "عقد الهبة", "الواهب"]
expected_articles = [488, 489, 490]  # المواد المتعلقة بالهبة
```

### Test Case #2: الطلاق
```python
query = "شروط الطلاق"
expected_keywords = ["الطلاق", "شروط", "الزوج", "الزوجة"]
expected_articles = [...]
```

### Test Case #3: البيع
```python
query = "عقد البيع"
expected_keywords = ["البيع", "البائع", "المشتري", "الثمن"]
expected_articles = [...]
```

---

## 📋 Action Items (مهام التنفيذ)

### ⚡ عاجل (اليوم)
- [ ] تطبيق Quick Fix على `_build_sniper_query`
- [ ] تطبيق Quick Fix على `_calculate_legal_relevance_score`
- [ ] إعادة اختبار "الهبة"
- [ ] اختبار 3 استعلامات إضافية

### 🔄 قصير المدى (هذا الأسبوع)
- [ ] إعادة هيكلة Sniper Phase (Medium Fix)
- [ ] إضافة Proximity Scoring
- [ ] بناء Test Suite شامل (20+ استعلام)
- [ ] قياس Precision@5 و Recall@10

### 🚀 متوسط المدى (هذا الشهر)
- [ ] بناء قاموس مرادفات قانوني
- [ ] إضافة NER للمصطلحات القانونية
- [ ] Fine-tuning Embedding Model
- [ ] تطبيق Cross-Encoder للـ Re-ranking

---

## 📈 المؤشرات المستهدفة

| المؤشر | الحالي | المستهدف |
|--------|--------|----------|
| **Precision@5** | ~20% | >80% |
| **Recall@10** | غير معروف | >70% |
| **Response Time** | 3-7s | 2-5s |
| **Relevance Score** | 0.43 (خطأ) | >0.70 (صحيح) |

---

**آخر تحديث:** 2026-02-05 21:05  
**المسؤول:** فريق تطوير Marid AI - Search Engine Team  
**الحالة:** 🔴 يتطلب تدخل فوري
