# 🗺️ المسار القانوني: كيف يعمل النظام؟

## البنية العامة

```
User Query: "ما هي الهبة؟"
    ↓
[Judge Node] → تحديد النية (LEGAL_SIMPLE/COMPLEX/ADMIN)
    ↓
[Deep Research Node] → البحث + جمع المعلومات
    ↓
[Council Node] → مناقشة متعددة الخبراء (للاستعلامات المعقدة)
    ↓
[Judge Node] → صياغة الإجابة النهائية
```

---

## الأدوات المستخدمة في `agents/tools/`

### ✅ الأدوات الحالية:

| الملف | الوظيفة | الحالة | الاستخدام |
|-------|---------|--------|-----------|
| `hybrid_search_tool.py` | البحث الهجين (Vector + Keyword) | 🔴 **معطوب!** | `deep_research.py:19` |
| `simple_legal_search.py` | بحث بسيط بقواعد واضحة | 🟢 **يعمل!** | غير مُدمج بعد |
| `fetch_tools.py` | `FlexibleSearchTool`, `GetRelatedDocumentTool` | 🟢 يعمل | البحث العام + السياق |
| `vector_tools.py` | `VectorSearchTool` | 🟡 يعمل لكن embeddings ضعيفة | البحث الدلالي |
| `semantic_tools.py` | أدوات دلالية إضافية | 🟢 يعمل | - |
| `legal_blackboard_tool.py` | إدارة الذاكرة/الحالة | 🟢 يعمل | حفظ السياق |
| `lookup_tools.py` | بحث سريع | 🟢 يعمل | - |
| `read_tool.py` | قراءة البيانات | 🟢 يعمل | - |
| `db_tool_factory.py` | عمليات قاعدة البيانات | 🟢 يعمل | للـ Admin Agent |
| `smart_finalizer.py` | تنقيح الإجابات | 🟢 يعمل | - |

---

## المشكلة الرئيسية: Deep Research يستخدم `HybridSearchTool`

### الكود الحالي (`deep_research.py:19`):

```python
# Initialize tools
hybrid_search = HybridSearchTool()  # ← المشكلة!
blackboard = LegalBlackboardTool()
doc_tool = GetRelatedDocumentTool()
principle_search = FlexibleSearchTool()
```

### الاستخدام (تقريباً السطر 120-150):

```python
# في دالة _execute_search_logic:
queries = plan.get("queries", [query])

for q in queries[:5]:
    result = await hybrid_search.run(
        query=q,
        limit=10,
        country_id=plan.get("country_id")
    )
    # ← هنا يستدعي HybridSearchTool المعطوب!
```

---

## الحل: استبدال `HybridSearchTool` بـ `SimpleLegalSearchTool`

### التغييرات المطلوبة:

#### 1. تعديل `deep_research.py`:

```python
# السطر 7: استبدال
# from ...tools.hybrid_search_tool import HybridSearchTool
from ...tools.simple_legal_search import SimpleLegalSearchTool

# السطر 19: استبدال
# hybrid_search = HybridSearchTool()
search_tool = SimpleLegalSearchTool()

# السطر ~140: تعديل الاستدعاء
result = await search_tool.search(
    query=q,
    max_results=10,
    country_id=plan.get("country_id")
)
# Note: SimpleLegalSearchTool تُرجع List بدلاً من Tool result
# نحتاج تعديل الكود لاستخدام النتائج مباشرة
```

---

## التدفق التفصيلي

### المسار الحالي (المُعطل):

```python
1. User Input: "ما هي الهبة؟"
2. Judge → intent = "LEGAL_SIMPLE"
3. Deep Research (Investigator Mode):
   - يتخطى Investigator للاستعلامات البسيطة ✅
4. Deep Research (Researcher Mode):
   - يستدعي HybridSearchTool ❌
   - HybridSearchTool:
     a. Scout Phase → Vector search (similarity ~0.31)
     b. LLM keywords: ["الهبة", "gift", "تعريف", "معنى"]
     c. Sniper Phase → query dilution!
     d. Returns: "نظام الإحصاء" ❌❌❌
5. Circuit Breaker (للاستعلامات البسيطة):
   - يُجيب مباشرة بناءً على النتائج الخاطئة ❌
```

### المسار المُحسّن (بعد الإصلاح):

```python
1. User Input: "ما هي الهبة؟"
2. Judge → intent = "LEGAL_SIMPLE"
3. Deep Research (Researcher Mode):
   - يستدعي SimpleLegalSearchTool ✅
   - SimpleLegalSearchTool:
     a. Generate variants: ["الهبة", "الهبه", "هبة", "هبه"]
     b. DB search (ILIKE OR) → 15 results ✅
     c. Rule-based filter → 8 results ✅
     d. Context expansion (±2 chunks) ✅
     e. Returns: "نظام المعاملات المدنية - الهبة" ✅✅✅
4. Circuit Breaker:
   - يُجيب بناءً على النتائج الصحيحة ✅
```

---

## الأدوات الأخرى (Reference):

### `FlexibleSearchTool` (من `fetch_tools.py`):
```python
# بحث مرن - يُستخدم للمبادئ القانونية
result = await principle_search.run(
    query="مبادئ الهبة",
    table="thought_templates"  # البحث في الأفكار العامة
)
```

### `GetRelatedDocumentTool`:
```python
# جلب السياق (±N chunks)
siblings = await doc_tool.run(
    source_id="uuid...",
    sequence_number=5,
    radius=2  # ±2 chunks
)
```

### `VectorSearchTool`:
```python
# بحث دلالي بسيط
results = await vector_search.run(
    query="الهبة",
    limit=10
)
# Problem: Embeddings ضعيفة للعربية القانونية
```

---

## الخلاصة

### المشكلة:
- `deep_research.py` يستخدم `HybridSearchTool` (السطر 19)
- `HybridSearchTool` معطوب (query dilution + embeddings ضعيفة)
- النتيجة: إجابات خاطئة تماماً

### الحل:
1. استبدال `HybridSearchTool` بـ `SimpleLegalSearchTool`
2. تعديل `deep_research.py` (3 أسطر فقط!)
3. اختبار

### الملفات التي تحتاج تعديل:
- `e:\law\agents\graph\nodes\deep_research.py` (فقط!)

---

**التوصية:** نُصلح `deep_research.py` الآن لاستخدام الأداة الجديدة؟
