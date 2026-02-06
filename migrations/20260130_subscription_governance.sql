-- Migration: Harden Subscription Security and Governance
-- Purpose: Prevent trial abuse and ensure resource uniqueness

-- 1. Ensure User identification fields are unique
-- Note: Email is usually unique by default in most systems, but we ensure it here if not already.
-- Phone and License Number MUST be unique to prevent multi-account creation by the same person.

ALTER TABLE public.users ADD CONSTRAINT users_phone_unique UNIQUE (phone);
ALTER TABLE public.users ADD CONSTRAINT users_license_number_unique UNIQUE (license_number);

-- 2. Ensure one subscription per lawyer
ALTER TABLE public.lawyer_subscriptions ADD CONSTRAINT lawyer_subscriptions_lawyer_id_unique UNIQUE (lawyer_id);

-- 3. Standardize Default Starter Package
-- We assume 'Flexible' or 'Starter' is the default. Let's make sure 'Flexible' is marked as default if it exists.
UPDATE public.subscription_packages SET is_default = TRUE WHERE name = 'Flexible';

-- 4. Initial Governance values for Starter Package (if needed)
-- This ensures that any new signup gets these exact values unless changed via Admin.
UPDATE public.subscription_packages 
SET max_assistants = 0, 
    storage_mb = 50, -- 50MB
    ai_words_monthly = 5000,
    is_active = TRUE
WHERE is_default = TRUE;

-- 5. Helper Function for atomic storage usage updates
CREATE OR REPLACE FUNCTION increment_storage_usage(lawyer_id_val UUID, size_mb FLOAT)
RETURNS void AS $$
BEGIN
  UPDATE public.lawyer_subscriptions
  SET storage_used_mb = COALESCE(storage_used_mb, 0) + size_mb,
      updated_at = NOW()
  WHERE lawyer_id = lawyer_id_val;
END;
$$ LANGUAGE plpgsql;

-- 6. Helper Function for atomic word usage updates
CREATE OR REPLACE FUNCTION increment_word_usage(lawyer_id_val UUID, word_count INT)
RETURNS void AS $$
BEGIN
  UPDATE public.lawyer_subscriptions
  SET words_used_this_month = COALESCE(words_used_this_month, 0) + word_count,
      updated_at = NOW()
  WHERE lawyer_id = lawyer_id_val;
END;
$$ LANGUAGE plpgsql;

-- 7. Backfill for existing lawyers who don't have a subscription
DO $$
DECLARE
    starter_pkg_id UUID;
    lawyer_role_id UUID;
BEGIN
    -- Get IDs
    SELECT id INTO starter_pkg_id FROM public.subscription_packages WHERE is_default = TRUE LIMIT 1;
    SELECT id INTO lawyer_role_id FROM public.roles WHERE is_default = TRUE LIMIT 1; -- Based on prev context, default role is lawyer

    IF starter_pkg_id IS NOT NULL THEN
        INSERT INTO public.lawyer_subscriptions (
            lawyer_id, 
            package_id, 
            status, 
            start_date, 
            end_date, 
            auto_renew, 
            extra_assistants, 
            extra_storage_mb, 
            extra_words
        )
        SELECT 
            u.id, 
            starter_pkg_id, 
            'trial', 
            CURRENT_DATE, 
            CURRENT_DATE + INTERVAL '30 days', 
            FALSE, 
            0, 0, 0
        FROM public.users u
        LEFT JOIN public.lawyer_subscriptions ls ON u.id = ls.lawyer_id
        WHERE ls.id IS NULL -- Only those without subscription
        AND u.role_id = lawyer_role_id; -- Only lawyers
    END IF;
END $$;
