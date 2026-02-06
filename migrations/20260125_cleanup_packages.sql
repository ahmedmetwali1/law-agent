-- Clean up legacy subscription data and packages
TRUNCATE TABLE lawyer_subscriptions CASCADE;
DELETE FROM subscription_packages WHERE is_flexible = FALSE;

-- Ensure a single "Flexible" package exists if not already there
INSERT INTO subscription_packages (
    id, name, name_ar, description, description_ar, 
    is_flexible, is_active, sort_order, features,
    color, icon
) 
SELECT 
    gen_random_uuid(), 'Flexible', 'باقة مرنة', 
    'صمم باقتك بنفسك حسب احتياجاتك', 'Design your own package',
    TRUE, TRUE, 1, 
    '["custom_assistants", "custom_storage", "custom_ai"]',
    '#D4AF37', 'Settings'
WHERE NOT EXISTS (SELECT 1 FROM subscription_packages WHERE is_flexible = TRUE);

-- Update lawyer_subscriptions to support expiration logic (30 days)
-- (Existing table should already have end_date, but we'll ensure logic is clear)
-- We might need a status for 'pending_activation' if not exists
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'subscription_status') THEN
        -- Skip if using varchar or existing enum
    END IF;
END $$;
