-- Fix Missing Flexible Package Flag
-- 1. Ensure 'is_flexible' column exists (it should, but safety first)
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'subscription_packages' AND column_name = 'is_flexible') THEN
        ALTER TABLE public.subscription_packages ADD COLUMN is_flexible BOOLEAN DEFAULT FALSE;
    END IF;
END $$;

-- 2. Mark existing 'Flexible' package as flexible
UPDATE public.subscription_packages 
SET is_flexible = TRUE 
WHERE name ILIKE '%Flexible%' OR name ILIKE '%Starter%';

-- 3. If no package was updated, create one default flexible package
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM public.subscription_packages WHERE is_flexible = TRUE) THEN
        INSERT INTO public.subscription_packages (
            name, name_ar, is_default, is_flexible, is_active, 
            price_monthly, price_yearly, sort_order, 
            max_assistants, storage_mb, ai_words_monthly, features
        ) VALUES (
            'Flexible', 'الباقة المرنة', TRUE, TRUE, TRUE, 
            0, 0, 1, 
            0, 50, 5000, ARRAY['دفع حسب الاستخدام']
        );
    END IF;
END $$;
