
# Golden Dataset for Legal Search Tuning
# Format: {"query": "text", "expected_keywords": ["kw1", "kw2"], "expected_article_ref": "Article X"}

GOLDEN_DATASET = [
    # --- 1. Civil (مدني) ---
    {
        "category": "Civil",
        "query": "ما هي شروط عقد الهبة؟",
        "expected_keywords": ["هبة", "عقد", "واجب", "شرط"],
        "expected_article_ref": "368" 
    },
    {
        "category": "Civil",
        "query": "هل يجوز الرجوع في الهبة؟",
        "expected_keywords": ["رجوع", "هبة", "عذر", "موانع"],
        "expected_article_ref": "371" 
    },

    # --- 2. Criminal / Drugs (مخدرات) ---
    {
        "category": "Drugs",
        "query": "عقوبة تعاطي المخدرات لأول مرة",
        "expected_keywords": ["مخدرات", "تعاطي", "عقوبة", "حبس"],
        "expected_article_ref": "41" # Example from Narcotic Drugs Law
    },
    {
        "category": "Drugs",
        "query": "حكم الترويج للمخدرات",
        "expected_keywords": ["ترويج", "مخدرات", "إعدام", "سجن"],
        "expected_article_ref": "37" 
    },

    # --- 3. Personal Status (أحوال شخصية) ---
    {
        "category": "Personal Status",
        "query": "الفرق بين الطلاق والخلع",
        "expected_keywords": ["طلاق", "خلع", "عوض", "زوج"],
        "expected_article_ref": "None" # Conceptual
    },
    {
        "category": "Personal Status",
        "query": "شروط فسخ النكاح للعيب",
        "expected_keywords": ["فسخ", "نكاح", "عيب", "مرض"],
        "expected_article_ref": "104" # Personal Status Law
    },
    {
        "category": "Personal Status",
        "query": "نفقة الأولاد بعد الطلاق",
        "expected_keywords": ["نفقة", "أولاد", "حضامة", "أب"],
        "expected_article_ref": "None"
    },

    # --- 4. Commercial (تجاري) ---
    {
        "category": "Commercial",
        "query": "مسؤولية الشريك في شركة التضامن",
        "expected_keywords": ["شركة", "تضامن", "شريك", "مسؤولية"],
        "expected_article_ref": "18" # Companies Law
    },
    {
        "category": "Commercial",
        "query": "عقد المضاربة وشروطه",
        "expected_keywords": ["مضاربة", "عقد", "ربح", "خسارة"],
        "expected_article_ref": "None"
    },

    # --- 5. Real Estate (عقاري) ---
    {
        "category": "Real Estate",
        "query": "فسخ عقد الإيجار لعدم دفع الأجرة",
        "expected_keywords": ["إيجار", "أجرة", "فسخ", "سداد"],
        "expected_article_ref": "None" # Ejar Law / Civil Trans
    },
    {
        "category": "Real Estate",
        "query": "نظام البيع على الخارطة",
        "expected_keywords": ["بيع", "خارطة", "وافي", "تطوير"],
        "expected_article_ref": "None"
    },

    # --- 6. Liability / Medical (أخطاء طبية / تعويض) ---
    {
        "category": "Medical Liability",
        "query": "التعويض عن الخطأ الطبي في العملية الجراحية",
        "expected_keywords": ["خطأ", "طبي", "تعويض", "ضرر"],
        "expected_article_ref": "None"
    },
    {
        "category": "Compensation",
        "query": "التعويض عن الضرر المعنوي",
        "expected_keywords": ["تعويض", "ضرر", "معنوي", "نفسي"],
        "expected_article_ref": "138" # Civil Transactions
    },

    # --- 7. Legal Drafting & Procedures (صياغة وإجراءات) ---
    # Requested: Contracts, Defense Memos, Claims, Appeals, Cassation, Expert Objections
    
    # A. Contracts (العقود)
    {
        "category": "Drafting - Contracts",
        "query": "أركان عقد البيع وشروط صحته",
        "expected_keywords": ["عقد", "بيع", "أركان", "رضا", "محل", "سبب"],
        "expected_article_ref": "None" # Civil Transactions
    },
    {
        "category": "Drafting - Contracts",
        "query": "صياغة شرط التحكيم في العقود التجارية",
        "expected_keywords": ["تحكيم", "شرط", "عقد", "نظام التحكيم"],
        "expected_article_ref": "None"
    },

    # B. Litigation Documents (المذكرات والصحائف)
    {
        "category": "Drafting - Litigation",
        "query": "البيانات الإلزامية في صحيفة الدعوى",
        "expected_keywords": ["صحيفة", "دعوى", "بيانات", "مدعي", "مدعى عليه"],
        "expected_article_ref": "41" # Civil Procedure Law (approx)
    },
    {
        "category": "Drafting - Litigation",
        "query": "آلية كتابة مذكرة دفاع في قضية جنائية",
        "expected_keywords": ["مذكرة", "دفاع", "جنائية", "رد", "دفوع"],
        "expected_article_ref": "None"
    },
    {
        "category": "Drafting - Litigation",
        "query": "مذكرة شارحة لأسباب الاستئناف",
        "expected_keywords": ["استئناف", "مذكرة", "أسباب", "حكم"],
        "expected_article_ref": "None"
    },

    # C. Appeals & Cassation (الطعون)
    {
        "category": "Procedures - Appeals",
        "query": "مهلة تقديم الاستئناف في القضايا التجارية",
        "expected_keywords": ["مهلة", "استئناف", "تجاري", "يوم"],
        "expected_article_ref": "None"
    },
    {
        "category": "Procedures - Cassation",
        "query": "حالات النقض في النظام السعودي",
        "expected_keywords": ["نقض", "محكمة عليا", "أسباب", "مخالفة"],
        "expected_article_ref": "None"
    },

    # D. Expert Reports (الخبرة)
    {
        "category": "Procedures - Experts",
        "query": "طريقة الاعتراض على تقرير الخبير الهندسي",
        "expected_keywords": ["اعتراض", "تقرير", "خبير", "مناقشة"],
        "expected_article_ref": "None" # Law of Evidence / Procedures
    }
]
