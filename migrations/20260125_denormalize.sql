-- 1. Add client_name to cases
ALTER TABLE cases ADD COLUMN IF NOT EXISTS client_name TEXT;

-- 2. Add denormalized columns to hearings
ALTER TABLE hearings ADD COLUMN IF NOT EXISTS client_name TEXT;
ALTER TABLE hearings ADD COLUMN IF NOT EXISTS case_number TEXT;
ALTER TABLE hearings ADD COLUMN IF NOT EXISTS case_year TEXT;
ALTER TABLE hearings ADD COLUMN IF NOT EXISTS court_name TEXT;

-- 3. Backfill cases.client_name
UPDATE cases c
SET client_name = cl.full_name
FROM clients cl
WHERE c.client_id = cl.id
AND c.client_name IS NULL;

-- 4. Backfill hearings data
-- Join hearings -> cases -> clients
UPDATE hearings h
SET 
    case_number = c.case_number,
    case_year = c.case_year,
    court_name = c.court_name,
    client_name = cl.full_name
FROM cases c
JOIN clients cl ON c.client_id = cl.id
WHERE h.case_id = c.id
AND (
    h.case_number IS NULL OR 
    h.client_name IS NULL
);
