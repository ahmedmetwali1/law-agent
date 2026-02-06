-- Add outcome and next_hearing_date to hearings table
ALTER TABLE hearings ADD COLUMN IF NOT EXISTS outcome TEXT;
ALTER TABLE hearings ADD COLUMN IF NOT EXISTS next_hearing_date DATE;

-- Add comment for documentation
COMMENT ON COLUMN hearings.outcome IS 'The result or outcome of the hearing';
COMMENT ON COLUMN hearings.next_hearing_date IS 'Scheduled date for the following hearing';
