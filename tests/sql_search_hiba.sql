-- 🔍 SQL Queries للبحث عن "الهبة" في Supabase

-- ==========================================
-- Query 1: بحث في محتوى المستندات (document_chunks)
-- ==========================================

SELECT 
    id,
    content,
    ai_summary,
    sequence_number,
    source_id
FROM document_chunks
WHERE 
    country_id = '61a2dd4b-cf18-4d88-b210-4d3687701b01' -- السعودية
    AND (
        content ILIKE '%الهبة%' 
        OR content ILIKE '%الهبه%'
        OR ai_summary ILIKE '%الهبة%'
        OR ai_summary ILIKE '%الهبه%'
    )
ORDER BY sequence_number
LIMIT 20;

-- ==========================================
-- Query 2: بحث في عناوين المصادر (legal_sources)
-- ==========================================

SELECT 
    id,
    title,
    doc_type,
    metadata
FROM legal_sources
WHERE 
    country_id = '61a2dd4b-cf18-4d88-b210-4d3687701b01'
    AND (
        title ILIKE '%الهبة%'
        OR title ILIKE '%الهبه%'
        OR full_content_md ILIKE '%الهبة%'
    )
LIMIT 10;

-- ==========================================
-- Query 3: إحصائيات - كم مرة ظهرت كلمة "الهبة"
-- ==========================================

SELECT 
    COUNT(*) as total_chunks_with_hiba,
    COUNT(DISTINCT source_id) as total_sources_with_hiba
FROM document_chunks
WHERE 
    country_id = '61a2dd4b-cf18-4d88-b210-4d3687701b01'
    AND (
        content ILIKE '%الهبة%' 
        OR content ILIKE '%الهبه%'
    );

-- ==========================================
-- Query 4: البحث مع تفاصيل المصدر (JOIN)
-- ==========================================

SELECT 
    dc.id as chunk_id,
    dc.content,
    dc.sequence_number,
    ls.title as source_title,
    ls.doc_type
FROM document_chunks dc
INNER JOIN legal_sources ls ON dc.source_id = ls.id
WHERE 
    dc.country_id = '61a2dd4b-cf18-4d88-b210-4d3687701b01'
    AND (
        dc.content ILIKE '%الهبة%' 
        OR dc.content ILIKE '%الهبه%'
    )
ORDER BY ls.title, dc.sequence_number
LIMIT 30;

-- ==========================================
-- Query 5: بحث في نظام محدد (نظام المعاملات المدنية)
-- ==========================================

SELECT 
    dc.id,
    dc.content,
    dc.sequence_number,
    ls.title
FROM document_chunks dc
INNER JOIN legal_sources ls ON dc.source_id = ls.id
WHERE 
    dc.country_id = '61a2dd4b-cf18-4d88-b210-4d3687701b01'
    AND ls.title ILIKE '%المعاملات المدنية%'
    AND (
        dc.content ILIKE '%الهبة%' 
        OR dc.content ILIKE '%الهبه%'
    )
ORDER BY dc.sequence_number
LIMIT 50;

-- ==========================================
-- Query 6: استخراج أرقام المواد عن الهبة
-- ==========================================

SELECT 
    dc.content,
    dc.sequence_number,
    ls.title
FROM document_chunks dc
INNER JOIN legal_sources ls ON dc.source_id = ls.id
WHERE 
    dc.country_id = '61a2dd4b-cf18-4d88-b210-4d3687701b01'
    AND dc.content ILIKE '%الهبة%'
    AND dc.content ~* 'المادة\s*[0-9٠-٩]+'  -- Regex للمواد
ORDER BY dc.sequence_number
LIMIT 30;

-- ==========================================
-- Query 7: بحث Full-Text (أسرع للبيانات الكبيرة)
-- ==========================================
-- Note: يتطلب Full-Text Search Index

SELECT 
    id,
    content,
    ts_rank(to_tsvector('arabic', content), to_tsquery('arabic', 'الهبة')) as rank
FROM document_chunks
WHERE 
    country_id = '61a2dd4b-cf18-4d88-b210-4d3687701b01'
    AND to_tsvector('arabic', content) @@ to_tsquery('arabic', 'الهبة')
ORDER BY rank DESC
LIMIT 20;

-- ==========================================
-- ✅ الأسهل للاستخدام (Quick Check)
-- ==========================================

-- فقط تحقق من الوجود:
SELECT EXISTS (
    SELECT 1 
    FROM document_chunks 
    WHERE content ILIKE '%الهبة%'
) as هل_الهبة_موجودة;

-- عد النتائج:
SELECT 
    COUNT(*) as عدد_النتائج
FROM document_chunks
WHERE 
    country_id = '61a2dd4b-cf18-4d88-b210-4d3687701b01'
    AND content ILIKE '%الهبة%';
