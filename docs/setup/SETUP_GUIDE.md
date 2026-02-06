# دليل الإعداد السريع - Legal AI System
# Quick Setup Guide

## 🔑 المتطلبات الأساسية

### 1. مزود الذكاء الاصطناعي (AI Provider)

اختر أحد المزودات التالية:

#### أ) OpenAI (موصى به)
1. سجل حساب في https://platform.openai.com
2. اذهب إلى API Keys: https://platform.openai.com/api-keys
3. انقر "Create new secret key"
4. انسخ المفتاح (يبدأ بـ `sk-...`)

**التكلفة:** ~$0.002 لكل 1000 token

#### ب) Anthropic Claude
1. سجل في https://console.anthropic.com
2. اذهب إلى API Keys
3. أنشئ مفتاح جديد

#### ج) Google Gemini
1. اذهب إلى https://makersuite.google.com/app/apikey
2. انقر "Get API Key"
3. انسخ المفتاح

---

### 2. قاعدة البيانات Supabase

#### الخطوة 1: إنشاء مشروع
1. سجل حساب في https://supabase.com
2. انقر "New Project"
3. اختر اسم ومنطقة وكلمة مرور قوية

#### الخطوة 2: الحصول على المفاتيح
1. اذهب إلى **Settings** → **API**
2. ستجد:
   - **Project URL**: `https://xxxxx.supabase.co`
   - **anon/public key**: للاستخدام العام
   - **service_role key**: للاستخدام من Backend (سري)

#### الخطوة 3: إعداد قاعدة البيانات

**3.1 تفعيل pgvector:**

في SQL Editor، نفذ:
```sql
-- تفعيل pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;
```

**3.2 إنشاء الجداول:**

```sql
-- جدول مصادر القانون
CREATE TABLE legal_sources (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    title TEXT NOT NULL,
    source_type TEXT CHECK (source_type IN ('قانون', 'لائحة', 'قرار', 'سابقة', 'فتوى')),
    full_text TEXT NOT NULL,
    jurisdiction TEXT,
    issue_date DATE,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- جدول الأجزاء المفهرسة
CREATE TABLE document_chunks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    source_id UUID REFERENCES legal_sources(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    chunk_index INTEGER,
    hierarchy_path TEXT,
    ai_summary TEXT,
    legal_logic TEXT,
    embedding vector(1536),  -- لـ OpenAI embeddings
    keywords JSONB,
    fts_tokens tsvector,
    created_at TIMESTAMP DEFAULT NOW()
);

-- جدول قوالب التفكير
CREATE TABLE thought_templates (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    category TEXT,
    template_text TEXT NOT NULL,
    example_usage TEXT,
    embedding vector(1536),
    created_at TIMESTAMP DEFAULT NOW()
);

-- إنشاء الفهارس
CREATE INDEX idx_document_chunks_source_id ON document_chunks(source_id);
CREATE INDEX idx_document_chunks_fts ON document_chunks USING GIN(fts_tokens);
CREATE INDEX idx_document_chunks_embedding ON document_chunks 
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_document_chunks_keywords ON document_chunks USING GIN(keywords);
```

**3.3 إنشاء دوال البحث:**

نفذ محتوى الملف [`supabase_functions.sql`](file:///e:/law/supabase_functions.sql)

---

## ⚙️ إعداد Backend

### 1. إنشاء ملف .env

في مجلد `e:/law/`:

```bash
copy .env.example .env
```

### 2. تحرير .env

افتح `e:/law/.env` وأضف المفاتيح:

```env
# Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# AI Provider (اختر واحد)
AI_PROVIDER=openai

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4

# أو Anthropic
# ANTHROPIC_API_KEY=sk-ant-...
# ANTHROPIC_MODEL=claude-3-opus-20240229

# أو Google
# GOOGLE_API_KEY=AIza...
# GOOGLE_MODEL=gemini-pro

# Embedding
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536

# Search Configuration
KEYWORD_WEIGHT=0.5
VECTOR_WEIGHT=0.5
TOP_K_RESULTS=10

# LLM Configuration
MAX_TOKENS=2000
TEMPERATURE=0.7

# Storage
CASES_BUCKET=legal-cases
STORAGE_PATH=./cases

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=True
```

### 3. تثبيت المكتبات

```bash
cd e:/law
pip install -r requirements.txt
```

### 4. تشغيل Backend

```bash
python -m uvicorn api.main:app --reload
```

الـ API سيعمل على: http://localhost:8000

---

## 🌐 إعداد Frontend

### 1. إنشاء ملف .env

في `e:/law/frontend/`:

```bash
copy .env.example .env
```

محتوى `.env`:
```env
VITE_API_URL=http://localhost:8000
```

### 2. تثبيت المكتبات (اختياري)

```bash
cd e:/law/frontend
npm install
npm run dev
```

أو استخدم النسخة المستقلة التي لا تحتاج build:

**افتح مباشرة:** `e:/law/frontend/index-standalone.html`

---

## ✅ اختبار الاتصال

### 1. اختبار Backend

```bash
# في المتصفح أو curl
http://localhost:8000/health
```

يجب أن ترى:
```json
{
  "status": "healthy",
  "timestamp": "...",
  "version": "1.0.0"
}
```

### 2. اختبار الاتصال بـ Supabase

في Python:

```python
from agents.config.database import db

# اختبار الاتصال
try:
    result = db.legal_sources.select("id").limit(1).execute()
    print("✅ الاتصال بـ Supabase ناجح!")
except Exception as e:
    print("❌ خطأ في الاتصال:", e)
```

### 3. اختبار AI Provider

```python
from agents.knowledge.embeddings import create_embedding

try:
    embedding = create_embedding("اختبار")
    print(f"✅ AI Provider يعمل! Embedding size: {len(embedding)}")
except Exception as e:
    print("❌ خطأ في AI Provider:", e)
```

---

## 🔍 استكشاف الأخطاء

### خطأ: Supabase connection failed

**السبب:** مفاتيح خاطئة أو غير موجودة

**الحل:**
1. تحقق من `SUPABASE_URL` و `SUPABASE_SERVICE_ROLE_KEY` في `.env`
2. تأكد أن المشروع في Supabase نشط
3. تحقق من أن الـ service_role key صحيح (يبدأ بـ `eyJ...`)

### خطأ: OpenAI API Error

**الأسباب المحتملة:**
- مفتاح API غير صحيح
- نفد الرصيد في الحساب
- تجاوز الـ rate limit

**الحل:**
1. تحقق من المفتاح في https://platform.openai.com/api-keys
2. تحقق من الرصيد في https://platform.openai.com/usage
3. أضف رصيد إذا لزم الأمر

### خطأ: pgvector not found

**السبب:** Extension غير مفعل

**الحل:**
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### خطأ: Function match_document_chunks does not exist

**السبب:** لم يتم تنفيذ [`supabase_functions.sql`](file:///e:/law/supabase_functions.sql)

**الحل:**
1. افتح Supabase SQL Editor
2. انسخ محتوى `supabase_functions.sql`
3. نفذ الكود

---

## 📊 إضافة بيانات تجريبية (اختياري)

لاختبار النظام، أضف قانون تجريبي:

```sql
-- إدراج قانون تجريبي
INSERT INTO legal_sources (title, source_type, full_text, jurisdiction)
VALUES (
    'قانون العقوبات - القتل العمد',
    'قانون',
    'المادة 234: يعاقب بالإعدام كل من قتل نفساً عمداً مع سبق الإصرار والترصد...',
    'مصر'
);

-- إدراج chunk مفهرس
INSERT INTO document_chunks (source_id, content, chunk_index, keywords)
SELECT 
    id,
    'المادة 234: يعاقب بالإعدام كل من قتل نفساً عمداً...',
    0,
    '["قتل", "عمد", "إعدام", "جريمة"]'::jsonb
FROM legal_sources WHERE title LIKE '%قانون العقوبات%'
LIMIT 1;
```

---

## 🎯 الخطوات التالية

1. ✅ أنشئ حساب Supabase وأحصل على المفاتيح
2. ✅ أنشئ حساب OpenAI وأحصل على API key
3. ✅ املأ ملف `.env` في `e:/law/`
4. ✅ نفذ SQL scripts في Supabase
5. ✅ شغّل Backend: `uvicorn api.main:app --reload`
6. ✅ افتح Frontend: `index-standalone.html`
7. ✅ اختبر بإنشاء قضية أولى!

---

## 💰 التكلفة المتوقعة

### Supabase (مجاني)
- Free tier: 500MB database
- 1GB file storage
- 2GB bandwidth
- كافي للتطوير والاختبار

### OpenAI
- تكلفة تقريبية لكل قضية: $0.05 - $0.20
- يعتمد على طول القضية وعدد الوكلاء

**للبدء:** $5 - $10 رصيد كافي للاختبار

---

## 📞 المساعدة

إذا واجهت مشاكل:
1. تحقق من الـ logs في Terminal
2. راجع ملف `.env`
3. تأكد من اتصال الإنترنت
4. راجع [walkthrough.md](file:///C:/Users/LENOVO/.gemini/antigravity/brain/1787840c-e5c6-4201-a8f3-1fc2a17154aa/walkthrough.md)
