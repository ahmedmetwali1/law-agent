-- Add is_flexible to subscription_packages
-- Date: 2026-01-26

DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='subscription_packages' AND column_name='is_flexible') THEN
        ALTER TABLE subscription_packages ADD COLUMN is_flexible BOOLEAN DEFAULT FALSE;
    END IF;
END $$;

-- Update the Flexible package to be marked correctly
UPDATE subscription_packages SET is_flexible = TRUE WHERE name = 'Flexible' OR name_ar = 'باقة مرنة';
