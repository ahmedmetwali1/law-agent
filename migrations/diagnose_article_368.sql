-- =========================================================
-- 🕵️‍♂️ DIAGNOSTIC: How is Article 368 actually written?
-- =========================================================

-- 1. Search for Partial Text Matches (to catch "الثامنة" vs "ثمانية")
SELECT 
  'Text Partial Match' as search_type,
  id, 
  source_title, 
  substring(content from 1 for 100) as content_preview
FROM document_chunks
WHERE 
  normalize_arabic(content) LIKE '%الثامنه%' 
  AND normalize_arabic(content) LIKE '%الستون%'
LIMIT 5;

-- 2. Search for Digit Matches (to see if it's stored as "368")
SELECT 
  'Digit Match' as search_type,
  id, 
  source_title, 
  substring(content from 1 for 100) as content_preview
FROM document_chunks
WHERE content LIKE '%368%'
LIMIT 5;
