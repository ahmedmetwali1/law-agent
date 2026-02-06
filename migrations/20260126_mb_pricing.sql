-- Migrate storage units from GB to MB
-- Date: 2026-01-26

-- 1. Update subscription_pricing (Global Defaults)
ALTER TABLE subscription_pricing RENAME COLUMN price_per_gb_monthly TO price_per_mb_monthly;
ALTER TABLE subscription_pricing RENAME COLUMN free_storage_gb TO free_storage_mb;
UPDATE subscription_pricing SET 
    price_per_mb_monthly = price_per_mb_monthly / 1024.0,
    free_storage_mb = free_storage_mb * 1024.0;

-- 2. Update country_pricing (Country Specific)
ALTER TABLE country_pricing RENAME COLUMN price_per_gb_monthly TO price_per_mb_monthly;
ALTER TABLE country_pricing RENAME COLUMN free_storage_gb TO free_storage_mb;
UPDATE country_pricing SET 
    price_per_mb_monthly = price_per_mb_monthly / 1024.0,
    free_storage_mb = free_storage_mb * 1024.0;

-- 3. Update subscription_packages
ALTER TABLE subscription_packages RENAME COLUMN storage_gb TO storage_mb;
UPDATE subscription_packages SET storage_mb = storage_mb * 1024.0;

-- 4. Update lawyer_subscriptions
ALTER TABLE lawyer_subscriptions RENAME COLUMN extra_storage_gb TO extra_storage_mb;
UPDATE lawyer_subscriptions SET extra_storage_mb = extra_storage_mb * 1024.0;

-- Optional: Update base rates to be more readable in MB if they were zero/tiny
-- $1/GB = $0.000976/MB. Let's keep the math precise.
