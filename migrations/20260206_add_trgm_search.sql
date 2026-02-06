-- 1. Enable pg_trgm extension for fuzzy matching
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 2. Create index for faster fuzzy search on content
CREATE INDEX IF NOT EXISTS idx_document_chunks_content_trgm 
ON document_chunks 
USING GIN (content gin_trgm_ops);

-- 3. Create index for Arabic Full Text Search
CREATE INDEX IF NOT EXISTS idx_document_chunks_content_fts 
ON document_chunks 
USING GIN (to_tsvector('arabic', content));

-- 4. RPC Function for Advanced Text Existence Check
-- Usage: supabase.rpc('check_text_existence', { query_text: '...', match_threshold: 0.6, filter_country_id: '...', semantic_query: '...' })
CREATE OR REPLACE FUNCTION check_text_existence(
  query_text TEXT,
  match_threshold FLOAT DEFAULT 0.6,
  filter_country_id UUID DEFAULT NULL,
  semantic_query TEXT DEFAULT NULL
)
RETURNS TABLE (
  id UUID,
  content TEXT,
  similarity_score FLOAT,
  source_id UUID,
  source_title TEXT,      -- ✅ Correct column
  keywords JSONB,         -- ✅ Correct column
  hierarchy_path TEXT     -- ✅ Correct column
) 
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT 
    document_chunks.id,
    document_chunks.content,
    GREATEST(
      -- 1. Similarity Score (Trigram)
      similarity(document_chunks.content, query_text),
      
      -- 2. Exact Match Bonus (1.0)
      CASE WHEN document_chunks.content ILIKE '%' || query_text || '%' THEN 1.0 ELSE 0.0 END,
      
      -- 3. Semantic Match Bonus (0.7)
      CASE 
        WHEN semantic_query IS NOT NULL 
             AND to_tsvector('arabic', document_chunks.content) @@ to_tsquery('arabic', semantic_query) 
        THEN 0.7 
        ELSE 0.0 
      END
    )::FLOAT AS similarity_score,
    
    document_chunks.source_id,
    document_chunks.source_title,
    document_chunks.keywords,
    document_chunks.hierarchy_path
    
  FROM document_chunks
  WHERE 
    -- Filter by Country
    (filter_country_id IS NULL OR document_chunks.country_id = filter_country_id)
    
    AND (
      -- 1. Exact or Partial Match (Original Input)
      document_chunks.content ILIKE '%' || query_text || '%'
      
      OR
      
      -- 2. Trigram Similarity (Fuzzy Match for Typos)
      similarity(document_chunks.content, query_text) > match_threshold

      OR

      -- 3. ✅ POWERFUL: Semantic Full Text Search (Matches ANY variant)
      -- Finds "واهب" or "موهوب" even if user searched "هبة"
      (
        semantic_query IS NOT NULL 
        AND 
        to_tsvector('arabic', document_chunks.content) @@ to_tsquery('arabic', semantic_query)
      )
    )
    
  ORDER BY similarity_score DESC
  LIMIT 20;
END;
$$;
