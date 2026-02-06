# 🗂️ خطة أرشفة الأكواد القديمة V1

## 📋 الملخص
هذا الملف يحتوي على الأوامر لأرشفة أكواد V1 القديمة بشكل آمن.

---

## ⚠️ تحديث مهم: إلغاء حذف `read_tool.py`

**السبب:** يحتوي `read_tool.py` على وظيفة **Navigation بـ sequence_number** التي لا توجد في `GetRelatedDocumentTool` حالياً.

**القرار:**
1. ✅ **إبقاء `read_tool.py`** مؤقتاً
2. ✅ **دمج** وظيفة الـ Navigation في `GetRelatedDocumentTool`
3. ✅ **بعد التأكد** من أن الوظيفة متاحة، يمكن أرشفة `read_tool.py`

---

## 🔧 الأوامر (PowerShell)

### 1. إنشاء مجلدات الأرشيف
```powershell
# إنشاء المجلدات
New-Item -ItemType Directory -Force -Path "archive"
New-Item -ItemType Directory -Force -Path "archive\v1_nodes"
New-Item -ItemType Directory -Force -Path "archive\v1_tools"
```

### 2. أرشفة الـ Nodes القديمة
```powershell
# نقل الـ V1 nodes
Move-Item -Path "agents\graph\nodes\council.py" -Destination "archive\v1_nodes\" -Force
Move-Item -Path "agents\graph\nodes\drafter.py" -Destination "archive\v1_nodes\" -Force
Move-Item -Path "agents\graph\nodes\investigator.py" -Destination "archive\v1_nodes\" -Force
Move-Item -Path "agents\graph\nodes\research.py" -Destination "archive\v1_nodes\" -Force
Move-Item -Path "agents\graph\nodes\general.py" -Destination "archive\v1_nodes\" -Force
Move-Item -Path "agents\graph\nodes\reviewer.py" -Destination "archive\v1_nodes\" -Force
Move-Item -Path "agents\graph\nodes\router.py" -Destination "archive\v1_nodes\" -Force
```

### 3. أرشفة الأدوات غير المستخدمة
```powershell
# نقل الأدوات القديمة (ما عدا read_tool.py!)
Move-Item -Path "agents\tools\semantic_tools.py" -Destination "archive\v1_tools\" -Force
Move-Item -Path "agents\tools\smart_finalizer.py" -Destination "archive\v1_tools\" -Force

# ⚠️ لا تنقل read_tool.py حتى يتم دمج الـ Navigation!
# Move-Item -Path "agents\tools\read_tool.py" -Destination "archive\v1_tools\" -Force
```

### 4. التحقق من الأرشفة
```powershell
# عرض محتويات الأرشيف
Get-ChildItem -Recurse "archive\"

# التأكد من عدم وجود استيرادات مكسورة
Select-String -Path "agents\**\*.py" -Pattern "from.*council import" -Exclude "*council_v2*"
Select-String -Path "agents\**\*.py" -Pattern "from.*drafter import" -Exclude "*drafter_v2*"
```

---

## 📝 قائمة التحقق

### الـ Nodes المُؤرشفة:
- [ ] council.py → `archive/v1_nodes/`
- [ ] drafter.py → `archive/v1_nodes/`
- [ ] investigator.py → `archive/v1_nodes/`
- [ ] research.py → `archive/v1_nodes/`
- [ ] general.py → `archive/v1_nodes/`
- [ ] reviewer.py → `archive/v1_nodes/`
- [ ] router.py → `archive/v1_nodes/`

### الأدوات المُؤرشفة:
- [ ] semantic_tools.py → `archive/v1_tools/`
- [ ] smart_finalizer.py → `archive/v1_tools/`
- [ ] ~~read_tool.py~~ → **إلغاء الأرشفة** (وظيفة مهمة)

---

## 🔄 خطة دمج `read_tool.py` في `fetch_tools.py`

### الوظائف التي يجب نقلها:

#### A. Navigation by `sequence_number`
```python
# من read_tool.py (Lines 189-194)
metadata["navigation"] = {
    "prev_page_cmd": f"read_document(source_id='{current_source}', sequence_number={current_seq - 1})",
    "next_page_cmd": f"read_document(source_id='{current_source}', sequence_number={current_seq + 1})",
    "hint": "Use source_id + sequence_number to flip pages."
}
```

**الحل:** إضافة methods جديدة في `GetRelatedDocumentTool`:
```python
def get_next_chunk(self, chunk_id: str) -> ToolResult:
    """Get the next chunk in sequence"""
    # 1. Get current sequence_number
    # 2. Fetch chunk with sequence_number + 1
    
def get_prev_chunk(self, chunk_id: str) -> ToolResult:
    """Get the previous chunk in sequence"""
    # 1. Get current sequence_number
    # 2. Fetch chunk with sequence_number - 1
```

#### B. Navigation by `source_id + sequence_number`
```python
# يمكن إضافة parameter جديد في GetRelatedDocumentTool
def run(
    self,
    chunk_id: Optional[str] = None,
    source_id: Optional[str] = None,
    sequence_number: Optional[int] = None,  # ← جديد
    include_siblings: bool = False,
    sibling_limit: int = 3
):
    """
    If sequence_number is provided with source_id,
    fetch that specific chunk directly
    """
```

---

## 🎯 الخطوات التالية

1. **تحديث `GetRelatedDocumentTool`:**
   - إضافة `sequence_number` parameter
   - إضافة `get_next_chunk()` و `get_prev_chunk()`

2. **تحديث `deep_research.py`:**
   - استخدام الـ navigation الجديدة

3. **اختبار:**
   - التأكد من أن الـ agents يمكنهم طلب القسم التالي/السابق

4. **بعد النجاح:**
   - أرشفة `read_tool.py`

---

## 📅 الجدول الزمني

| المرحلة | المدة | الحالة |
|:---|:---|:---|
| أرشفة V1 Nodes | يوم 1 | ⏸️ **معلق** (بانتظار دمج Navigation) |
| دمج Navigation | يوم 2-3 | 🔄 **التالي** |
| اختبار | يوم 4 |   |
| أرشفة `read_tool.py` | يوم 5 |   |
| حذف نهائي | بعد أسبوعين |   |

---

## 🛡️ خطة التراجع (Rollback)

إذا حدثت مشاكل:
```powershell
# استعادة ملف من الأرشيف
Copy-Item -Path "archive\v1_nodes\council.py" -Destination "agents\graph\nodes\" -Force

# أو استعادة الكل
Copy-Item -Path "archive\v1_nodes\*" -Destination "agents\graph\nodes\" -Force -Recurse
```

---

## ملاحظات

- **لا تحذف الأرشيف** قبل أسبوعين
- **راقب الـ logs** بعد الأرشفة
- **اختبر النظام** بعد كل خطوة

