-- Database Cleanup: Drop legacy tables to unify the system
-- This script removes old tables that have been replaced by 'subscription_packages' and 'lawyer_subscriptions'

BEGIN;

-- 1. Drop old 'packages' table if it exists
DROP TABLE IF EXISTS public.packages CASCADE;

-- 2. Drop old 'subscriptions' table if it exists (careful not to drop 'lawyer_subscriptions')
DROP TABLE IF EXISTS public.subscriptions CASCADE;

-- 3. Drop old 'user_subscriptions' if it exists (another potential legacy name)
DROP TABLE IF EXISTS public.user_subscriptions CASCADE;

COMMIT;
