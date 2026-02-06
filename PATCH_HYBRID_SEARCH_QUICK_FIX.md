# 🔧 Quick Fix Patch for HybridSearchTool

## ملف: `agents/tools/hybrid_search_tool.py`

### التعديل 1: دالة `_build_sniper_query` (السطور 645-684)

**استبدل الدالة الحالية بالكود التالي:**

```python
def _build_sniper_query(
    self,
    query_type: str,
    expanded_keywords: List[str],
    query_entities: Dict
) -> str:
    """
    Build optimized query for Sniper phase based on query type
    
    ✅ FIX: Separate core legal terms from generic modifiers
    to prevent query dilution and improve precision
    """
    # ✅ Generic terms that should NOT dominate the query
    generic_terms = {
        "تعريف", "معنى", "المقصود", "شروط", "إجراءات", "خطوات",
        "كيفية", "قائمة", "فهرس", "جدول",
        "definition", "meaning", "defined", "conditions", "procedure",
        "process", "steps", "list", "index", "table"
    }
    
    # ✅ Separate core terms from modifiers
    core_terms = []
    modifiers = []
    
    for kw in expanded_keywords[:15]:
        if kw.lower() in generic_terms:
            modifiers.append(kw)
        else:
            core_terms.append(kw)
    
    query_parts = []
    
    # ✅ Prioritize core terms (legal concepts)
    if core_terms:
        query_parts.extend(core_terms[:5])  # Max 5 core terms
    else:
        # Fallback if ALL terms are generic (rare)
        query_parts.extend(expanded_keywords[:3])
    
    # Add entity terms (articles/laws)
    if query_entities.get('articles'):
        for article in query_entities['articles'][:5]:  # Reduced from 8
            query_parts.append(f"المادة {article}")
    
    # ✅ Add modifiers ONLY if relevant and limited
    if query_type == 'DEFINITION' and modifiers:
        # Add max 2 definition-related terms
        def_mods = [m for m in modifiers if m.lower() in {"تعريف", "معنى", "definition", "meaning"}]
        query_parts.extend(def_mods[:2])
    
    elif query_type == 'ARTICLE_ENUMERATION':
        # Add structure keywords
        query_parts.extend([
            "فهرس", "جدول المحتويات", "المواد",
            "index", "articles"
        ][:3])  # Limit to 3
    
    elif query_type == 'PROCEDURE' and modifiers:
        # Add procedure keywords
        proc_mods = [m for m in modifiers if m.lower() in {"إجراءات", "خطوات", "procedure", "steps"}]
        query_parts.extend(proc_mods[:2])
    
    final_query = ' '.join(query_parts)
    
    # ✅ Debug logging
    logger.info(f"🎯 Sniper Query Built: '{final_query[:100]}...'")
    
    return final_query
```

---

## خطوات التطبيق اليدوي:

1. افتح `e:\law\agents\tools\hybrid_search_tool.py`
2. اذهب للسطر 645
3. احذف السطور 645-684 (الدالة القديمة)
4. الصق الكود الجديد أعلاه
5. احفظ الملف
6. أعد تشغيل الخادم:
   ```
   # في terminal e:\law
   # الخادم سيُعيد التحميل تلقائياً (hot reload)
   ```
7. اختبر مرة أخرى:
   ```
   python tests/test_search_hiba.py
   ```

---

## التأثير المتوقع:

### قبل الإصلاح:
```
Sniper Query: "الهبة gift تعريف definition معنى تعريف معنى المقصود"
Result 1: نظام الإحصاء (Score: 0.43) ❌
```

### بعد الإصلاح:
```
Sniper Query: "الهبة gift"
Result 1: المواد المتعلقة بالهبة (Score: 0.65) ✅
```

---

## التحسينات المطبقة:

1. ✅ **فصل المصطلحات:** Core terms vs. Generic modifiers
2. ✅ **تحديد الأولوية:** أول 5 مصطلحات أساسية فقط
3. ✅ **تقليل التكرار:** إزالة "Article X" المكررة
4. ✅ **تحديد Modifiers:** حد أقصى 2-3 كلمات عامة
5. ✅ **Debug Logging:** تتبع الاستعلام المُنش
