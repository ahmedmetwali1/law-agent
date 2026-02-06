-- 🔍 Simple SQL Test للتحقق من البيانات

-- 1. عد جميع legal_sources (بدون أي filter)
SELECT COUNT(*) as total_sources
FROM legal_sources;

-- 2. عرض أول 10 sources
SELECT id, title
FROM legal_sources
LIMIT 10;

-- 3.search عن "المعاملات"
SELECT id, title
FROM legal_sources
WHERE title ILIKE '%المعاملات%'
LIMIT 5;

-- 4. عد document_chunks
SELECT COUNT(*) as total_chunks
FROM document_chunks;

-- 5. بحث عن "الهبة" مباشرة
SELECT id, LEFT(content, 100) as preview
FROM document_chunks
WHERE content ILIKE '%الهبة%'
LIMIT 5;
