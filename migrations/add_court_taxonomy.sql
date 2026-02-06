-- ========================================
-- Multi-Country Support - Phase 1
-- Court Taxonomy Table + Egyptian & Saudi Data
-- ========================================

-- 1. Create court_taxonomy table
CREATE TABLE IF NOT EXISTS court_taxonomy (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    country_id UUID NOT NULL REFERENCES countries(id) ON DELETE CASCADE,
    court_level TEXT NOT NULL CHECK (court_level IN ('supreme', 'appeal', 'first_instance', 'execution', 'specialized')),
    court_name_ar TEXT NOT NULL,
    court_name_en TEXT,
    regex_patterns TEXT[] NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(country_id, court_level, court_name_ar)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_court_taxonomy_country ON court_taxonomy(country_id);
CREATE INDEX IF NOT EXISTS idx_court_taxonomy_level ON court_taxonomy(court_level);
CREATE INDEX IF NOT EXISTS idx_court_taxonomy_active ON court_taxonomy(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_court_taxonomy_country_active ON court_taxonomy(country_id, is_active) WHERE is_active = true;

-- Updated_at trigger
CREATE OR REPLACE FUNCTION update_court_taxonomy_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER court_taxonomy_updated_at
    BEFORE UPDATE ON court_taxonomy
    FOR EACH ROW
    EXECUTE FUNCTION update_court_taxonomy_updated_at();

-- ========================================
-- 2. Insert Egyptian Courts Data 🇪🇬
-- ========================================

DO $$
DECLARE
    egypt_id UUID := '3216b40a-9c9b-4c0a-adde-9b680f6b9481';
BEGIN
    -- محكمة النقض (Supreme Court)
    INSERT INTO court_taxonomy (country_id, court_level, court_name_ar, court_name_en, regex_patterns, sort_order, metadata) VALUES
    (egypt_id, 'supreme', 'محكمة النقض', 'Court of Cassation', ARRAY[
        'محكمة النقض',
        'نقض',
        'المحكمة النقض',
        'النقض المصرية',
        'محكمه النقض'
    ], 1, '{"jurisdiction": "national", "established": "1931"}'::jsonb);
    
    -- محكمة الاستئناف (Appeal Courts)
    INSERT INTO court_taxonomy (country_id, court_level, court_name_ar, court_name_en, regex_patterns, sort_order, metadata) VALUES
    (egypt_id, 'appeal', 'محكمة الاستئناف', 'Court of Appeal', ARRAY[
        'محكمة الاستئناف',
        'استئناف',
        'محكمة استئناف',
        'استئناف القاهرة',
        'استئناف الإسكندرية',
        'استئناف طنطا',
        'استئناف أسيوط',
        'استئناف المنصورة',
        'محكمه الاستئناف'
    ], 2, '{"degree": "second_instance"}'::jsonb);
    
    -- محكمة ابتدائية كلية (Full First Instance)
    INSERT INTO court_taxonomy (country_id, court_level, court_name_ar, court_name_en, regex_patterns, sort_order, metadata) VALUES
    (egypt_id, 'first_instance', 'محكمة ابتدائية كلية', 'Full Court of First Instance', ARRAY[
        'محكمة ابتدائية',
        'ابتدائية',
        'محكمة كلية',
        'كلية',
        'ابتدائيه'
    ], 3, '{"type": "civil_criminal", "jurisdiction": "regional"}'::jsonb);
    
    -- محكمة جزئية (Partial Court)
    INSERT INTO court_taxonomy (country_id, court_level, court_name_ar, court_name_en, regex_patterns, sort_order, metadata) VALUES
    (egypt_id, 'first_instance', 'محكمة جزئية', 'Partial Court', ARRAY[
        'محكمة جزئية',
        'جزئية',
        'محكمه جزئية'
    ], 4, '{"type": "minor_cases", "max_value": "100000 EGP"}'::jsonb);
    
    -- محكمة الأسرة (Family Court)
    INSERT INTO court_taxonomy (country_id, court_level, court_name_ar, court_name_en, regex_patterns, sort_order, metadata) VALUES
    (egypt_id, 'specialized', 'محكمة الأسرة', 'Family Court', ARRAY[
        'محكمة الأسرة',
        'أسرة',
        'محكمة أحوال شخصية',
        'أحوال شخصية',
        'محكمه الأسرة'
    ], 5, '{"specialization": "family_law", "established": "2004"}'::jsonb);
    
    -- محكمة اقتصادية (Economic Court)
    INSERT INTO court_taxonomy (country_id, court_level, court_name_ar, court_name_en, regex_patterns, sort_order, metadata) VALUES
    (egypt_id, 'specialized', 'محكمة اقتصادية', 'Economic Court', ARRAY[
        'محكمة اقتصادية',
        'اقتصادية',
        'المحكمة الاقتصادية',
        'محكمه اقتصادية'
    ], 6, '{"specialization": "economic_disputes", "established": "2008"}'::jsonb);
    
    RAISE NOTICE '✅ Inserted Egyptian court patterns';
END $$;

-- ========================================
-- 3. Insert Saudi Courts Data 🇸🇦
-- ========================================

DO $$
DECLARE
    saudi_id UUID := '61a2dd4b-cf18-4d88-b210-4d3687701b01';
BEGIN
    -- المحكمة العليا (Supreme Court)
    INSERT INTO court_taxonomy (country_id, court_level, court_name_ar, court_name_en, regex_patterns, sort_order, metadata) VALUES
    (saudi_id, 'supreme', 'المحكمة العليا', 'Supreme Court', ARRAY[
        'المحكمة العليا',
        'محكمة العليا',
        'العليا',
        'محكمه العليا'
    ], 1, '{"jurisdiction": "national", "established": "2009"}'::jsonb);
    
    -- محكمة الاستئناف
    INSERT INTO court_taxonomy (country_id, court_level, court_name_ar, court_name_en, regex_patterns, sort_order, metadata) VALUES
    (saudi_id, 'appeal', 'محكمة الاستئناف', 'Court of Appeal', ARRAY[
        'محكمة الاستئناف',
        'استئناف',
        'درجة ثانية',
        'المحكمة الاستئناف',
        'محكمه الاستئناف'
    ], 2, '{"degree": "second_instance"}'::jsonb);
    
    -- محكمة عامة (General Court)
    INSERT INTO court_taxonomy (country_id, court_level, court_name_ar, court_name_en, regex_patterns, sort_order, metadata) VALUES
    (saudi_id, 'first_instance', 'محكمة عامة', 'General Court', ARRAY[
        'محكمة عامة',
        'عامة',
        'درجة أولى',
        'محكمه عامة'
    ], 3, '{"type": "general_jurisdiction"}'::jsonb);
    
    -- محكمة أحوال شخصية
    INSERT INTO court_taxonomy (country_id, court_level, court_name_ar, court_name_en, regex_patterns, sort_order, metadata) VALUES
    (saudi_id, 'specialized', 'محكمة أحوال شخصية', 'Personal Status Court', ARRAY[
        'محكمة أحوال شخصية',
        'أحوال شخصية',
        'الأحوال الشخصية',
        'محكمه أحوال شخصية'
    ], 4, '{"specialization": "personal_status"}'::jsonb);
    
    -- محكمة تجارية
    INSERT INTO court_taxonomy (country_id, court_level, court_name_ar, court_name_en, regex_patterns, sort_order, metadata) VALUES
    (saudi_id, 'specialized', 'محكمة تجارية', 'Commercial Court', ARRAY[
        'محكمة تجارية',
        'تجارية',
        'المحكمة التجارية',
        'محكمه تجارية'
    ], 5, '{"specialization": "commercial_disputes"}'::jsonb);
    
    -- محكمة عمالية
    INSERT INTO court_taxonomy (country_id, court_level, court_name_ar, court_name_en, regex_patterns, sort_order, metadata) VALUES
    (saudi_id, 'specialized', 'محكمة عمالية', 'Labor Court', ARRAY[
        'محكمة عمالية',
        'عمالية',
        'المحكمة العمالية',
        'محكمه عمالية'
    ], 6, '{"specialization": "labor_disputes"}'::jsonb);
    
    -- محكمة جزائية
    INSERT INTO court_taxonomy (country_id, court_level, court_name_ar, court_name_en, regex_patterns, sort_order, metadata) VALUES
    (saudi_id, 'specialized', 'محكمة جزائية', 'Criminal Court', ARRAY[
        'محكمة جزائية',
        'جزائية',
        'المحكمة الجزائية',
        'محكمه جزائية'
    ], 7, '{"specialization": "criminal_law"}'::jsonb);
    
    -- محكمة التنفيذ
    INSERT INTO court_taxonomy (country_id, court_level, court_name_ar, court_name_en, regex_patterns, sort_order, metadata) VALUES
    (saudi_id, 'execution', 'محكمة التنفيذ', 'Execution Court', ARRAY[
        'محكمة التنفيذ',
        'تنفيذ',
        'المحكمة التنفيذ',
        'محكمه التنفيذ'
    ], 8, '{"function": "execution_of_judgments"}'::jsonb);
    
    RAISE NOTICE '✅ Inserted Saudi court patterns';
END $$;

-- ========================================
-- 4. Verification Query
-- ========================================

DO $$
DECLARE
    egypt_count INTEGER;
    saudi_count INTEGER;
    total_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO egypt_count FROM court_taxonomy WHERE country_id = '3216b40a-9c9b-4c0a-adde-9b680f6b9481';
    SELECT COUNT(*) INTO saudi_count FROM court_taxonomy WHERE country_id = '61a2dd4b-cf18-4d88-b210-4d3687701b01';
    SELECT COUNT(*) INTO total_count FROM court_taxonomy;
    
    RAISE NOTICE '========================================';
    RAISE NOTICE '✅ Migration Complete!';
    RAISE NOTICE 'Egyptian courts: %', egypt_count;
    RAISE NOTICE 'Saudi courts: %', saudi_count;
    RAISE NOTICE 'Total courts: %', total_count;
    RAISE NOTICE '========================================';
END $$;

-- Sample query to verify
SELECT 
    c.name_ar AS country,
    ct.court_level,
    ct.court_name_ar,
    array_length(ct.regex_patterns, 1) AS pattern_count
FROM court_taxonomy ct
JOIN countries c ON c.id = ct.country_id
ORDER BY c.name_ar, ct.sort_order;
