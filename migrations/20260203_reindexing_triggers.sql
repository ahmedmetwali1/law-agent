-- Add needs_reindexing column and triggers for stale embeddings

-- 1. Add Column
ALTER TABLE legal_sources 
ADD COLUMN IF NOT EXISTS needs_reindexing BOOLEAN DEFAULT FALSE;

-- 2. Create Trigger Function
CREATE OR REPLACE FUNCTION mark_source_for_reindexing()
RETURNS TRIGGER 
LANGUAGE plpgsql
AS $$
BEGIN
    -- Check if content changed
    IF NEW.full_content_md IS DISTINCT FROM OLD.full_content_md THEN
        NEW.needs_reindexing := TRUE;
        -- Optional: Mark existing chunks as outdated immediately?
        -- UPDATE document_chunks SET status = 'outdated' WHERE source_id = NEW.id;
    END IF;
    RETURN NEW;
END;
$$;

-- 3. Create Trigger
DROP TRIGGER IF EXISTS trg_check_source_content ON legal_sources;
CREATE TRIGGER trg_check_source_content
BEFORE UPDATE ON legal_sources
FOR EACH ROW
EXECUTE FUNCTION mark_source_for_reindexing();
