# دليل إعداد Open WebUI للنظام القانوني
# Open WebUI Setup Guide for Legal AI System

## 🎯 نظرة عامة

Open WebUI يوفر واجهة موحدة للوصول إلى نماذج AI مختلفة من خلال API واحد. يدعم:
- نماذج محلية (Ollama: Llama, Mistral, etc.)
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Google (Gemini)
- وغيرها...

---

## 📦 تثبيت Open WebUI

### الطريقة 1: Docker (موصى به)

```bash
docker run -d -p 11434:8080 \
  -v open-webui:/app/backend/data \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main
```

Open WebUI سيعمل على: `http://localhost:11434`

### الطريقة 2: Python

```bash
pip install open-webui
open-webui serve
```

---

## ⚙️ إعداد Open WebUI

### 1. الوصول إلى الواجهة

افتح: `http://localhost:11434`

### 2. إنشاء حساب

سجل حساب جديد (أول حساب يكون Admin)

### 3. إضافة النماذج

#### أ) نماذج محلية (Ollama)

```bash
# تثبيت Ollama
curl -fsSL https://ollama.com/install.sh | sh

# تحميل نماذج
ollama pull llama3.1
ollama pull mistral
ollama pull nomic-embed-text  # للـ embeddings
```

#### ب) نماذج خارجية (OpenAI/Claude)

في Open WebUI:
1. اذهب إلى **Settings** → **Connections**
2. أضف OpenAI API Key
3. أضف Anthropic API Key
4. احفظ

---

## 🔑 الحصول على API Key

### في Open WebUI:

1. اذهب إلى **Settings** → **Account**
2. انقر **Create API Key**
3. انسخ الـ API Key
4. احفظه في ملف `.env`:

```env
OPENWEBUI_API_KEY=your-api-key-here
```

**ملاحظة:** بعض إصدارات Open WebUI لا تحتاج API key للاستخدام المحلي.

---

## 🛠️ إعداد النظام القانوني

### 1. إنشاء ملف .env

في `e:/law/`:

```bash
copy .env.example .env
```

### 2. تحرير .env

```env
# Open WebUI Configuration
OPENWEBUI_API_URL=http://localhost:11434
OPENWEBUI_API_KEY=your-api-key-or-leave-empty

# اختر النموذج المفضل
OPENWEBUI_MODEL=llama3.1:latest
# أو: gpt-4, claude-3-opus, mistral:latest

# للـ Embeddings
EMBEDDING_PROVIDER=openwebui
OPENWEBUI_EMBEDDING_MODEL=nomic-embed-text:latest

# أو استخدم OpenAI للـ embeddings فقط
# EMBEDDING_PROVIDER=openai
# OPENAI_API_KEY=sk-...
# EMBEDDING_MODEL=text-embedding-3-small

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-key

# Storage
USE_SUPABASE_STORAGE=False
STORAGE_PATH=./cases
```

---

## 🧪 اختبار الاتصال

### 1. اختبار Open WebUI Client

```python
from agents.config.openwebui import openwebui_client

# قائمة النماذج المتاحة
models = openwebui_client.list_models()
print("Available models:", models)

# اختبار completion
response = openwebui_client.chat_completion([
    {"role": "user", "content": "مرحباً"}
])
print("Response:", response)

# اختبار embedding
embedding = openwebui_client.generate_embedding("نص تجريبي")
print(f"Embedding size: {len(embedding)}")
```

### 2. اختبار من Terminal

```bash
# تشغيل Backend
cd e:/law
python -m uvicorn api.main:app --reload
```

### 3. اختبار API

```bash
# في المتصفح
http://localhost:8000/api/config

# يجب أن ترى
{
  "llm_provider": "Open WebUI",
  "llm_model": "llama3.1:latest",
  "embedding_provider": "openwebui"
}
```

---

## 🎯 اختيار النماذج المناسبة

### للـ LLM (التحليل والتوصيات):

| النموذج | المميزات | الاستخدام |
|---------|----------|-----------|
| `llama3.1:latest` | مجاني، سريع، جيد للعربية | تطوير واختبار |
| `mistral:latest` | متوازن، أداء جيد | بديل مجاني |
| `gpt-4` | أفضل جودة، تكلفة عالية | إنتاج |
| `claude-3-opus` | ممتاز للتحليل، متوسط التكلفة | إنتاج |
| `gemini-pro` | جيد ورخيص | بديل اقتصادي |

### للـ Embeddings:

| النموذج | الحجم | الاستخدام |
|---------|-------|-----------|
| `nomic-embed-text:latest` | 768 | محلي، مجاني |
| `text-embedding-3-small` | 1536 | OpenAI، دقة عالية |
| `text-embedding-3-large` | 3072 | أعلى دقة |

---

## 💡 نصائح الأداء

### 1. استخدام Models المناسبة

```env
# للتطوير: نماذج محلية سريعة
OPENWEBUI_MODEL=llama3.1:latest

# للإنتاج: نماذج قوية
OPENWEBUI_MODEL=gpt-4
```

### 2. Caching

Open WebUI يدعم caching تلقائي للـ responses المتشابهة

### 3. Batch Processing

لمعالجة قضايا متعددة، استخدم async:

```python
import asyncio
from agents.core.general_lawyer_agent import GeneralLawyerAgent

async def process_multiple_cases(cases):
    agent = GeneralLawyerAgent()
    tasks = [agent.process_complete_case(case['facts']) 
             for case in cases]
    return await asyncio.gather(*tasks)
```

---

## 🔧 استكشاف الأخطاء

### خطأ: Connection refused

**السبب:** Open WebUI غير مشغل

**الحل:**
```bash
# تحقق من تشغيل Open WebUI
curl http://localhost:11434/health

# أو شغله
docker start open-webui
# أو
open-webui serve
```

### خطأ: Model not found

**السبب:** النموذج غير محمل

**الحل:**
```bash
# حمل النموذج
ollama pull llama3.1

# تحقق من النماذج المتاحة
ollama list
```

### خطأ: Embedding dimension mismatch

**السبب:** Embedding model مختلف عن المتوقع

**الحل:**
```env
# إذا استخدمت nomic-embed-text
EMBEDDING_DIMENSIONS=768

# إذا استخدمت OpenAI
EMBEDDING_DIMENSIONS=1536
```

---

## 📊 مقارنة التكاليف

### نماذج محلية (Ollama)
- **التكلفة:** مجانية 100%
- **المتطلبات:** 8GB+ RAM
- **السرعة:** متوسطة إلى سريعة
- **الأداء:** جيد للعربية

### OpenAI عبر Open WebUI
- **التكلفة:** ~$0.002 - $0.03 لكل 1K tokens
- **الأداء:** ممتاز
- **السرعة:** سريعة جداً

### Claude عبر Open WebUI
- **التكلفة:** ~$0.015 - $0.075 لكل 1K tokens
- **الأداء:** ممتاز للتحليل المعقد
- **السرعة:** سريعة

---

## ✅ قائمة التحقق

- [ ] تثبيت Open WebUI
- [ ] إعداد Ollama (للنماذج المحلية)
- [ ] تحميل النماذج المطلوبة
- [ ] إنشاء API Key في Open WebUI
- [ ] تحديث ملف `.env`
- [ ] اختبار الاتصال
- [ ] تشغيل Backend
- [ ] اختبار من Frontend

---

## 🎊 جاهز!

النظام الآن يستخدم Open WebUI كواجهة موحدة. يمكنك:
- التبديل بين النماذج بتغيير `OPENWEBUI_MODEL`
- استخدام نماذج محلية مجانية
- أو نماذج خارجية من خلال نفس API

**ميزة:** لا حاجة لتغيير الكود عند تغيير النموذج!
