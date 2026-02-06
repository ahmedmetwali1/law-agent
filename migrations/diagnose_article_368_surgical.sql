-- =========================================================
-- 🕵️‍♂️ SURGICAL STRIKE: Finding Article 368 by Body Text
-- =========================================================
-- Since headers are failing, we search for the unique legal rule:
-- "فلا تنعقد هبته إلا بتوثيقها"
-- This will reveal the TRUE header spelling. 
-- =========================================================

SELECT 
  id, 
  source_title, 
  -- Show the first 100 chars (Header) to spot the spelling difference
  substring(content from 1 for 100) as header_preview,
  -- Check if our normalization would verify it
  normalize_arabic(substring(content from 1 for 100)) as normalized_header
FROM document_chunks
WHERE 
  -- Search for unique body substring provided by user
  content LIKE '%فلا تنعقد هبته إلا بتوثيقها%'
LIMIT 1;
