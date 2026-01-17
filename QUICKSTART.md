# 🎯 Legal AI Multi-Agent System - Quick Start

## نظرة سريعة على المشروع

تم بناء نظام كامل متعدد الوكلاء للاستشارات القانونية!

## ✅ ما تم إنجازه

### 1. البنية التحتية الأساسية
- ⚙️ نظام إعدادات شامل مع دعم multiple AI providers
- 🗄️ اتصال Supabase مع singleton pattern
- 📊 توثيق كامل لقاعدة البيانات

### 2. نظام المعرفة
- 🧠 توليد Embeddings (OpenAI/Google)
- 🔍 محرك بحث هجين (Keyword + Vector)
- 📚 تكامل مع جداول Supabase الثلاثة

### 3. نظام الوكلاء
- 🤖 Base Agent مع LLM integration
- 👨‍⚖️ General Lawyer Agent (الوكيل الرئيسي)
- 📝 Case Planner (مخطط القضية)
- 🔨 Agent Builder (بناء الوكلاء ديناميكياً)
- 💾 Case Storage (حفظ JSON)

### 4. API
- 🚀 FastAPI application كاملة
- 📡 Endpoints لجميع العمليات
- 📝 OpenAPI documentation

## 🏗️ هيكل المشروع

```
law/
├── agents/
│   ├── config/          ✅ settings.py, database.py
│   ├── core/            ✅ base_agent, general_lawyer, planner, builder
│   ├── knowledge/       ✅ embeddings, hybrid_search
│   └── storage/         ✅ case_storage
├── api/                 ✅ main.py (FastAPI)
├── .env.example         ✅
├── requirements.txt     ✅
└── README.md            ✅
```

## 🚀 خطوات التشغيل السريعة

### 1. التثبيت

```bash
# إنشاء بيئة افتراضية
python -m venv venv
venv\Scripts\activate

# تثبيت المكتبات
pip install -r requirements.txt
```

### 2. الإعدادات

```bash
# نسخ ملف الإعدادات
copy .env.example .env

# تحرير .env وإضافة:
# - SUPABASE_URL
# - SUPABASE_SERVICE_ROLE_KEY
# - OPENAI_API_KEY
```

### 3. إعداد Supabase

في Supabase SQL Editor، قم بتنفيذ:
```bash
supabase_functions.sql
```

### 4. تشغيل السيرفر

```bash
cd e:/law
uvicorn api.main:app --reload
```

السيرفر يعمل على: `http://localhost:8000`
API Docs: `http://localhost:8000/docs`

## 📡 استخدام الـ API

### إنشاء قضية جديدة
```bash
POST http://localhost:8000/api/cases/new
Content-Type: application/json

{
  "facts": "وقائع القضية...",
  "client_name": "أحمد محمد",
  "case_type": "جنائي"
}
```

### معالجة قضية كاملة
```bash
POST http://localhost:8000/api/cases/{case_id}/process
```

### الحصول على تقرير
```bash
GET http://localhost:8000/api/cases/{case_id}
```

## 🎯 سير العمل

1. **المستخدم** يرسل وقائع القضية → `POST /api/cases/new`
2. **General Lawyer Agent** يستقبل ويحلل
3. **Case Planner** يحدد الوكلاء المطلوبين
4. **Agent Builder** ينشئ الوكلاء المتخصصين
5. **Specialist Agents** يبحثون في قاعدة المعرفة
6. **General Agent** يجمع التقارير ويصدر التوصية
7. **النتيجة** تحفظ في JSON

## 🔧 الخطوات التالية

### ضروري:
- [ ] تعبئة ملف `.env` بالمفاتيح الحقيقية
- [ ] تنفيذ `supabase_functions.sql` في Supabase
- [ ] اختبار الاتصال بقاعدة البيانات

### اختياري:
- [ ] إضافة Specialist Agents محددة (criminal_law_agent.py, etc.)
- [ ] تحسين prompts الوكلاء
- [ ] إضافة unit tests
- [ ] إضافة واجهة مستخدم (React/Vue)

## 📚 الوثائق

- [README.md](../README.md) - دليل كامل
- [database_schema.md](../../../brain/1787840c-e5c6-4201-a8f3-1fc2a17154aa/database_schema.md) - مخطط قاعدة البيانات
- [implementation_plan.md](../../../brain/1787840c-e5c6-4201-a8f3-1fc2a17154aa/implementation_plan.md) - خطة التنفيذ
- API Docs: `http://localhost:8000/docs` (بعد تشغيل السيرفر)

## ⚠️ ملاحظات مهمة

1. **Storage**: حالياً يستخدم local storage. لاستخدام Supabase Storage:
   ```python
   storage = CaseStorage(use_supabase=True)
   ```

2. **AI Provider**: بشكل افتراضي يستخدم OpenAI. للتغيير:
   ```env
   AI_PROVIDER=anthropic  # أو google
   ```

3. **RPC Functions**: دوال Supabase RPC ضرورية للـ vector search الكامل

## 🎊 النظام جاهز!

النظام الأساسي مكتمل وجاهز للاختبار. ابدأ بـ:
1. تعبئة `.env`
2. تشغيل السيرفر
3. إرسال أول قضية!
