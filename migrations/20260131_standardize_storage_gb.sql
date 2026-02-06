-- Migration: Standardize Storage Unit to GB
-- 1. Rename column extra_storage_mb -> extra_storage_gb
-- 2. Convert values (MB / 1024)

BEGIN;

-- Check if column exists before renaming
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'lawyer_subscriptions' AND column_name = 'extra_storage_mb') THEN
        ALTER TABLE public.lawyer_subscriptions RENAME COLUMN extra_storage_mb TO extra_storage_gb;
        
        -- Convert existing MB values to GB
        UPDATE public.lawyer_subscriptions 
        SET extra_storage_gb = extra_storage_gb / 1024
        WHERE extra_storage_gb >= 1; -- Avoid re-converting if already small
        
        -- Change type to float or numeric if it was integer, to support partial GBs (e.g. 0.5 GB)
        ALTER TABLE public.lawyer_subscriptions ALTER COLUMN extra_storage_gb TYPE float;
    END IF;
END $$;

-- Also check if we need to add specific 'requested_' columns if they don't exist, though typically we use extra_ fields.
-- Based on error "Could not find the 'extra_storage_gb' column", the above rename should fix it.

COMMIT;
