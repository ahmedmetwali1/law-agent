-- Fix for match_documents RPC
-- The previous version referenced 'd.title' which does not exist in document_chunks.
-- This version removes that reference and adds strict country filtering.

create or replace function match_documents_v2 (
  query_embedding vector(1536),
  match_threshold float,
  match_count int,
  filter jsonb default '{}'
)
returns table (
  id uuid,
  content text,
  similarity float,
  metadata jsonb
)
language plpgsql
as $$
begin
  return query
  select
    document_chunks.id,
    document_chunks.content,
    1 - (document_chunks.embedding <=> query_embedding) as similarity,
    jsonb_build_object(
      'source_id', document_chunks.source_id,
      'country_id', document_chunks.country_id,
      'sequence_number', document_chunks.sequence_number,
      'ai_summary', document_chunks.ai_summary
    ) as metadata
  from document_chunks
  where 1 - (document_chunks.embedding <=> query_embedding) > match_threshold
  and (
    filter is null 
    or (
      -- JSONB contained check for generic metadata filters
      -- This is a simplification; for strict country_id we might want a direct column check if passed
      (filter ->> 'country_id' is null or document_chunks.country_id = (filter ->> 'country_id')::uuid)
    )
  )
  order by document_chunks.embedding <=> query_embedding
  limit match_count;
end;
$$;
