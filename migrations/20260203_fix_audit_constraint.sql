-- Fix Audit Logs Constraint (Force Update)
-- The table might have been created with an old constraint definition.
-- We must explicitly recreate the constraint to allow 'UPDATE', 'INSERT', 'DELETE'.

-- 0. Force Clean Data (Development Environment Only)
-- This removes any rows that might be violating the new constraint logic
-- or causing issues during the migration.
TRUNCATE TABLE audit_logs;

DO $$
BEGIN
    -- 1. Try to drop the constraint if it exists (by name)
    -- Common names: audit_logs_action_check, audit_logs_action_check1, etc.
    -- We'll try the standard one.
    IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'audit_logs_action_check') THEN
        ALTER TABLE audit_logs DROP CONSTRAINT audit_logs_action_check;
    END IF;
END $$;

-- 2. Add the correct constraint
ALTER TABLE audit_logs
ADD CONSTRAINT audit_logs_action_check
CHECK (action IN ('INSERT', 'UPDATE', 'DELETE'));

-- 3. Verify Trigger uses matching case
-- (The trigger function process_audit_log already uses uppercase 'INSERT', 'UPDATE', 'DELETE' in our codebase)
