-- Optimization: Enforce strict number matching & CTE-based Score Filtering
-- Generated: 2026-02-06
-- Description:
-- 1. Extracts 'Sacred Numbers' from query/semantic args.
-- 2. Uses CTE to calculate scores first.
-- 3. Filters by TOTAL score (Base + Bonuses) to eliminate boilerplate noise.

-- 🧹 CLEANUP
-- 🧹 NUCLEAR CLEANUP: Dynamically drop ALL variations of this function to stop "is not unique" errors.
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN SELECT oid FROM pg_proc WHERE proname = 'check_text_existence'
    LOOP
        EXECUTE 'DROP FUNCTION ' || r.oid::regprocedure || ' CASCADE';
    END LOOP;
END$$;

CREATE OR REPLACE FUNCTION normalize_arabic(input_text TEXT)
RETURNS TEXT AS $$
BEGIN
  -- 1. Remove Tashkeel (Diacritics) & Tatweel
  -- 2. Normalize Alef/Taa/Yaa
  -- 3. Collapse multiple whitespace/newlines into single space (CRITICAL for multi-line headers)
  RETURN regexp_replace(
    translate(
      regexp_replace(input_text, '[\u064B-\u065F\u0640]', '', 'g'),
      'أإآةى',
      'اااهي'
    ),
    '\s+', ' ', 'g'
  );
END;
$$ LANGUAGE plpgsql IMMUTABLE;

CREATE OR REPLACE FUNCTION check_text_existence(
  query_text TEXT,
  match_threshold FLOAT DEFAULT 0.6,
  filter_country_id UUID DEFAULT NULL,
  semantic_query TEXT DEFAULT NULL,
  min_return_score FLOAT DEFAULT 0.75 -- ✅ NEW: Quality Gate
)
RETURNS TABLE (
  id UUID,
  content TEXT,
  similarity_score FLOAT,
  source_id UUID,
  source_title TEXT,
  keywords JSONB,
  hierarchy_path TEXT,
  debug_info JSONB -- ✅ Added for transparency
)
LANGUAGE plpgsql
AS $$
DECLARE
  captured_number TEXT;
  norm_query TEXT;
BEGIN
  -- 1. Extract 'Sacred Number' Analysis
  captured_number := substring(query_text FROM '[0-9]+');
  IF captured_number IS NULL AND semantic_query IS NOT NULL THEN
    captured_number := substring(semantic_query FROM '[0-9]+');
  END IF;

  -- 2. Normalize Query Once
  norm_query := normalize_arabic(query_text);

  RETURN QUERY
  WITH ScoredResults AS (
    SELECT
      document_chunks.id,
      document_chunks.content,

      -- Calculate components separately for debugging
      COALESCE(similarity(document_chunks.content, query_text), 0)::FLOAT as val_sim,
      (CASE
        -- Header Priority REMOVED: User confirms definition can be in the middle.
        -- Robust Exact Match (+3.0): Search ANYWHERE in normalized content.
        -- Matches "المادة" with "الماده" and ignores diacritics.
        WHEN length(norm_query) > 4 AND position(norm_query in normalize_arabic(document_chunks.content)) > 0
        THEN 3.0
        ELSE 0.0
      END)::FLOAT as val_exact,
      (CASE
          WHEN semantic_query IS NOT NULL
               AND to_tsvector('arabic', document_chunks.content) @@ to_tsquery('arabic', semantic_query)
          THEN 0.8
          ELSE 0.0
      END)::FLOAT as val_sem,
      (CASE 
          -- Use strict boundaries \m \M to avoid partial matches inside years/money
          WHEN captured_number IS NOT NULL AND document_chunks.content ~ ('\m' || captured_number || '\M')
          THEN 1.5 
          ELSE 0.0 
      END)::FLOAT as val_num,
      
      document_chunks.source_id,
      document_chunks.source_title,
      document_chunks.keywords,
      document_chunks.hierarchy_path,
      document_chunks.country_id
      
    FROM document_chunks
    WHERE 
      -- A. Country Filter
      (filter_country_id IS NULL OR document_chunks.country_id = filter_country_id)
      
      -- B. Baseline Relevance Check (Must meet at least one criteria to even be scored)
      AND (
        (length(query_text) > 4 AND position(query_text in document_chunks.content) > 0)
        OR similarity(document_chunks.content, query_text) > match_threshold
        OR (semantic_query IS NOT NULL AND to_tsvector('arabic', document_chunks.content) @@ to_tsquery('arabic', semantic_query))
        -- Include Number Match as a valid entry criteria, but NOT exclusive
        OR (captured_number IS NOT NULL AND document_chunks.content ~ captured_number)
      )
  )
  -- Final Selection & Filtering
  SELECT 
    sr.id, 
    sr.content, 
    (sr.val_sim + sr.val_exact + sr.val_sem + sr.val_num) as similarity_score,
    sr.source_id, 
    sr.source_title, 
    sr.keywords, 
    sr.hierarchy_path,
    jsonb_build_object(
      'sim', sr.val_sim,
      'exact', sr.val_exact,
      'sem', sr.val_sem,
      'num', sr.val_num,
      'cap_num', captured_number,
      'seen_query', query_text -- ✅ Reveal the invisible
    ) as debug_info
  FROM ScoredResults sr
  WHERE (sr.val_sim + sr.val_exact + sr.val_sem + sr.val_num) >= min_return_score -- ✅ Quality Gate: Drops high-similarity noise
  ORDER BY similarity_score DESC
  LIMIT 20;
END;
$$;
