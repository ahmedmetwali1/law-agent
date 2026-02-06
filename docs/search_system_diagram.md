# مخططات توضيحية لنظام البحث القانوني

## 1. مسار البحث الهجين (Hybrid Search Flow)

```mermaid
flowchart TB
    Start([استعلام المستخدم]) --> Judge{Judge Node}
    
    Judge -->|LEGAL_SIMPLE| DR[Deep Research]
    Judge -->|LEGAL_COMPLEX| DR
    Judge -->|ADMIN_QUERY| Admin[Admin Operations]
    
    DR --> Scout[🔍 Scout Phase]
    
    Scout --> VS1[Vector Search<br/>Top 12]
    Scout --> EE[استخراج الكيانات<br/>Articles, Laws]
    Scout --> LLM1[LLM Analysis<br/>Keyword Expansion]
    Scout --> QT[تصنيف نوع الاستعلام<br/>ENUMERATION/DEFINITION/etc.]
    
    VS1 --> Sniper[🎯 Sniper Phase]
    EE --> Sniper
    LLM1 --> Sniper
    QT --> Sniper
    
    Sniper --> VS2[Vector Search<br/>Top 40]
    Sniper --> KS[Keyword Search<br/>Top 40]
    
    VS2 --> Merge[دمج وإزالة التكرار]
    KS --> Merge
    
    Merge --> Score[تسجيل الصلة<br/>Relevance Scoring]
    
    Score --> Rank[ترتيب حسب النقاط]
    
    Rank --> Diversity[فلتر التنوع<br/>Diversity Filter]
    
    Diversity --> Expand[توسيع السياق<br/>Fetch Siblings]
    
    Expand --> Results([نتائج البحث النهائية])
    
    Results --> Simple{استعلام بسيط?}
    Simple -->|نعم| DirectAnswer[إجابة مباشرة]
    Simple -->|لا| Council[Council Node]
    
    Council --> JudgeV[Judge Verdict]
    JudgeV --> DirectAnswer
    
    DirectAnswer --> End([إجابة المستخدم])
    
    style Scout fill:#e1f5ff
    style Sniper fill:#ffe1e1
    style DirectAnswer fill:#d4edda
```

## 2. هندسة قاعدة المعرفة الطبقية

```mermaid
graph TD
    subgraph "المستوى 3: المبادئ القانونية"
        TT[thought_templates<br/>المبادئ العامة]
    end
    
    subgraph "المستوى 2: الشرائح"
        DC1[Chunk #1<br/>sequence: 1]
        DC2[Chunk #2<br/>sequence: 2<br/>المادة 77]
        DC3[Chunk #3<br/>sequence: 3]
        DC4[Chunk #4<br/>sequence: 4]
    end
    
    subgraph "المستوى 1: المصادر"
        LS[legal_sources<br/>القانون المدني<br/>full_content_md]
    end
    
    LS -->|تقسيم| DC1
    LS -->|تقسيم| DC2
    LS -->|تقسيم| DC3
    LS -->|تقسيم| DC4
    
    DC1 -.->|السياق السابق| DC2
    DC3 -.->|السياق اللاحق| DC2
    
    TT -.->|يطبق على| DC2
    
    style LS fill:#f9f9f9
    style DC2 fill:#fff3cd
    style TT fill:#d1ecf1
```

## 3. نموذج التسجيل (Scoring Model)

```mermaid
pie title توزيع نقاط الصلة (Relevance Score)
    "Base Similarity" : 30
    "Entity Matching" : 20
    "Keyword Density" : 20
    "Query Type Bonus" : 30
```

## 4. تدفق استرجاع السياق (Context Retrieval)

```mermaid
sequenceDiagram
    participant User
    participant HybridSearch
    participant VectorDB
    participant GetDocument
    participant Response
    
    User->>HybridSearch: "ما هي المادة 77؟"
    HybridSearch->>VectorDB: Vector Search
    VectorDB-->>HybridSearch: Chunk #5 (contains "المادة 77")
    
    HybridSearch->>GetDocument: Fetch Siblings (chunk_id=5, limit=2)
    GetDocument->>VectorDB: WHERE sequence IN (3,4,5,6,7)
    VectorDB-->>GetDocument: [Chunk#3, 4, 5, 6, 7]
    
    GetDocument-->>HybridSearch: Merged Context
    HybridSearch->>Response: Full Context Response
    Response-->>User: "المادة 77 تنص على...<br/>(سياق: المادة 76 تعرّف...)"
```

## 5. أنماط الاستعلام ومعالجتها

```mermaid
mindmap
  root((أنماط الاستعلام))
    ARTICLE_ENUMERATION
      "ما المواد الخاصة بـ..."
      البحث عن الفهارس
      توسيع النطاق
    DEFINITION
      "ما تعريف..."
      التركيز على النص التعريفي
      البحث عن كلمة "تعريف"
    PROCEDURE
      "كيف..."
      البحث عن الخطوات
      الإجراءات القانونية
    CONDITION
      "شروط..."
      البحث عن القوائم
      المتطلبات
    GENERAL
      استعلامات عامة
      بحث شامل
```

## 6. معمارية النظام الشاملة

```mermaid
graph LR
    subgraph "الواجهة الأمامية"
        UI[React Frontend]
    end
    
    subgraph "الخادم الخلفي"
        API[FastAPI Backend]
        Graph[LangGraph Multi-Agent]
    end
    
    subgraph "قاعدة البيانات"
        Supabase[(Supabase PostgreSQL)]
        Vector[(pgvector Extension)]
    end
    
    subgraph "الخدمات الخارجية"
        OpenAI[OpenAI API<br/>GPT-4 + Embeddings]
    end
    
    UI -->|HTTP/WebSocket| API
    API -->|Invoke| Graph
    
    Graph -->|Query| Supabase
    Graph -->|Vector Search| Vector
    Graph -->|LLM Calls| OpenAI
    
    Supabase --> Vector
    
    style Graph fill:#e3f2fd
    style Supabase fill:#f3e5f5
    style OpenAI fill:#fff3e0
```

## 7. دورة حياة الاستعلام (Query Lifecycle)

```mermaid
stateDiagram-v2
    [*] --> Received: User Query
    Received --> Classified: Judge Node
    
    Classified --> SimpleRoute: LEGAL_SIMPLE
    Classified --> ComplexRoute: LEGAL_COMPLEX
    Classified --> AdminRoute: ADMIN_QUERY
    
    SimpleRoute --> Investigator: Check Facts
    ComplexRoute --> Investigator
    
    Investigator --> FactsComplete: Facts OK
    Investigator --> NeedClarification: Missing Info
    
    NeedClarification --> [*]: Ask User
    
    FactsComplete --> Research: Deep Research
    
    Research --> NoResults: 0 Results
    Research --> HasResults: Found Data
    
    NoResults --> [*]: Apologize
    
    HasResults --> DirectAnswer: Simple Intent
    HasResults --> Council: Complex Intent
    
    Council --> Judge: Multi-Agent Review
    Judge --> DirectAnswer: Final Verdict
    
    DirectAnswer --> [*]: Response to User
    AdminRoute --> [*]: Admin Operation
```

## 8. تفصيل Scout Phase

```mermaid
flowchart LR
    subgraph "Scout Phase - المرحلة الاستكشافية"
        direction TB
        
        A[Query Input] --> B{Embedding Available?}
        B -->|Yes| C[Vector Search<br/>match_count=12]
        B -->|No| D[Keyword Fallback]
        
        C --> E[Extract Entities<br/>from Results]
        D --> E
        
        E --> F[Articles:<br/>77, 78, 79]
        E --> G[Laws:<br/>القانون رقم 12]
        
        F --> H[LLM Analysis]
        G --> H
        
        H --> I[Query Type<br/>Detection]
        
        I --> J{Query Type?}
        J -->|ENUMERATION| K[Add Index Keywords<br/>فهرس, جدول المحتويات]
        J -->|DEFINITION| L[Add Definition Keywords<br/>تعريف, معنى]
        J -->|OTHER| M[Standard Keywords]
        
        K --> N[Expanded Keywords<br/>40 terms max]
        L --> N
        M --> N
    end
    
    style A fill:#e8f5e9
    style N fill:#ffebee
```

## 9. نموذج البيانات (Data Model)

```mermaid
erDiagram
    COUNTRIES ||--o{ LEGAL_SOURCES : "belongs_to"
    LEGAL_SOURCES ||--o{ DOCUMENT_CHUNKS : "contains"
    DOCUMENT_CHUNKS ||--o{ THOUGHT_TEMPLATES : "generates"
    
    COUNTRIES {
        uuid id PK
        string name_ar
        string name_en
        string code
    }
    
    LEGAL_SOURCES {
        uuid id PK
        uuid country_id FK
        string title
        text full_content_md
        int total_word_count
    }
    
    DOCUMENT_CHUNKS {
        uuid id PK
        uuid source_id FK
        text content
        vector embedding
        int sequence_number
        jsonb keywords
    }
    
    THOUGHT_TEMPLATES {
        uuid id PK
        text template_text
        vector template_embedding
        float confidence_score
    }
```

---

**تم إنشاؤه:** 2026-02-05  
**الغرض:** توضيح معماري لنظام البحث القانوني
