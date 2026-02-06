-- Clean up subscription tables
TRUNCATE TABLE lawyer_subscriptions CASCADE;
TRUNCATE TABLE subscription_packages CASCADE;
TRUNCATE TABLE country_pricing CASCADE;
TRUNCATE TABLE subscription_pricing CASCADE;

-- Default Subscription Pricing (Global)
INSERT INTO subscription_pricing (
    id, base_platform_fee, price_per_assistant, 
    price_per_gb_monthly, price_per_1000_words, 
    yearly_discount_percent, currency, currency_symbol, is_active
) VALUES (
    gen_random_uuid(),
    50.00,  -- Base Fees (Manual System)
    20.00,  -- Per Assistant
    1.00,   -- Per GB
    0.50,   -- Per 1000 words
    15.00,  -- 15% discount for yearly
    'USD', '$', TRUE
);

-- Flexible Package (The Only Package)
INSERT INTO subscription_packages (
    id, name, name_ar, description, description_ar, 
    is_flexible, is_active, sort_order, features,
    color, icon
) VALUES (
    gen_random_uuid(),
    'Flexible', 'باقة مرنة', 
    'صمم باقتك بنفسك حسب احتياجاتك', 'Design your own package',
    TRUE, TRUE, 1, 
    '["custom_assistants", "custom_storage", "custom_ai"]',
    'from-gold-500 to-amber-600', 'Settings'
);

