-- Supabase RPC Functions for Vector Search
-- هذه الدوال يجب تنفيذها في Supabase SQL Editor

-- ==========================================
-- Function: match_document_chunks
-- البحث في document_chunks باستخدام التشابه الدلالي
-- ==========================================

CREATE OR REPLACE FUNCTION match_document_chunks(
  query_embedding vector(1536),
  match_threshold float DEFAULT 0.5,
  match_count int DEFAULT 10
)
RETURNS TABLE (
  id uuid,
  source_id uuid,
  content text,
  hierarchy_path text,
  ai_summary text,
  legal_logic text,
  keywords jsonb,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    document_chunks.id,
    document_chunks.source_id,
    document_chunks.content,
    document_chunks.hierarchy_path,
    document_chunks.ai_summary,
    document_chunks.legal_logic,
    document_chunks.keywords,
    1 - (document_chunks.embedding <=> query_embedding) AS similarity
  FROM document_chunks
  WHERE 1 - (document_chunks.embedding <=> query_embedding) > match_threshold
  ORDER BY document_chunks.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- ==========================================
-- Function: hybrid_search_documents
-- البحث الهجين (keyword + vector)
-- ==========================================

CREATE OR REPLACE FUNCTION hybrid_search_documents(
  search_query text,
  query_embedding vector(1536),
  keyword_weight float DEFAULT 0.5,
  vector_weight float DEFAULT 0.5,
  match_count int DEFAULT 10
)
RETURNS TABLE (
  id uuid,
  source_id uuid,
  content text,
  hierarchy_path text,
  ai_summary text,
  legal_logic text,
  keywords jsonb,
  hybrid_score float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  WITH keyword_results AS (
    SELECT
      document_chunks.id,
      1.0 AS keyword_score
    FROM document_chunks
    WHERE fts_tokens @@ to_tsquery('arabic', search_query)
  ),
  vector_results AS (
    SELECT
      document_chunks.id,
      1 - (document_chunks.embedding <=> query_embedding) AS vector_score
    FROM document_chunks
    ORDER BY document_chunks.embedding <=> query_embedding
    LIMIT match_count * 2
  )
  SELECT
    dc.id,
    dc.source_id,
    dc.content,
    dc.hierarchy_path,
    dc.ai_summary,
    dc.legal_logic,
    dc.keywords,
    (COALESCE(kr.keyword_score, 0) * keyword_weight + 
     COALESCE(vr.vector_score, 0) * vector_weight) AS hybrid_score
  FROM document_chunks dc
  LEFT JOIN keyword_results kr ON dc.id = kr.id
  LEFT JOIN vector_results vr ON dc.id = vr.id
  WHERE kr.id IS NOT NULL OR vr.id IS NOT NULL
  ORDER BY hybrid_score DESC
  LIMIT match_count;
END;
$$;

-- ==========================================
-- Indexes for Performance
-- فهارس لتحسين الأداء
-- ==========================================

-- Index on fts_tokens for faster keyword search
CREATE INDEX IF NOT EXISTS idx_document_chunks_fts 
ON document_chunks USING GIN(fts_tokens);

-- Index on embedding for faster vector search
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding 
ON document_chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Index on source_id for joins
CREATE INDEX IF NOT EXISTS idx_document_chunks_source_id 
ON document_chunks(source_id);

-- Index on keywords for JSONB queries
CREATE INDEX IF NOT EXISTS idx_document_chunks_keywords 
ON document_chunks USING GIN(keywords);

-- ==========================================
-- Notes / ملاحظات
-- ==========================================

-- 1. Make sure pgvector extension is enabled:
--    CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Adjust the vector dimension (1536) if using a different embedding model

-- 3. The ivfflat index parameter 'lists' should be tuned based on data size:
--    - Small dataset (< 100K rows): lists = 100
--    - Medium dataset (100K - 1M rows): lists = sqrt(rows)
--    - Large dataset (> 1M rows): lists = sqrt(rows) to rows/1000

-- 4. For Arabic text search, ensure the 'arabic' text search configuration exists:
--    SELECT * FROM pg_ts_config WHERE cfgname = 'arabic';
