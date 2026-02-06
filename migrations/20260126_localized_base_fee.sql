-- Add base_platform_fee to both pricing tables
-- Date: 2026-01-26

-- 1. Add to global subscription_pricing if not exists
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='subscription_pricing' AND column_name='base_platform_fee') THEN
        ALTER TABLE subscription_pricing ADD COLUMN base_platform_fee DECIMAL(10, 2) DEFAULT 0.00;
    END IF;
END $$;

-- 2. Add to country_pricing
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='country_pricing' AND column_name='base_platform_fee') THEN
        ALTER TABLE country_pricing ADD COLUMN base_platform_fee DECIMAL(10, 2) DEFAULT 0.00;
    END IF;
END $$;

-- 3. Update global default to 50 if it was 0
UPDATE subscription_pricing SET base_platform_fee = 50.00 WHERE base_platform_fee = 0;

-- 4. Copy values from global pricing to existing countries as a starting point
UPDATE country_pricing cp
SET base_platform_fee = sp.base_platform_fee
FROM subscription_pricing sp
WHERE cp.base_platform_fee = 0;
