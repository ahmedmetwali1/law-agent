-- ============================================================================
-- Add lawyer_id to hearings table
-- إضافة lawyer_id لجدول الجلسات
-- ============================================================================

-- 1. Add lawyer_id column (nullable first)
ALTER TABLE hearings 
ADD COLUMN IF NOT EXISTS lawyer_id UUID;

-- 2. Populate lawyer_id from case's lawyer_id
UPDATE hearings 
SET lawyer_id = cases.lawyer_id
FROM cases
WHERE hearings.case_id = cases.id
AND hearings.lawyer_id IS NULL;

-- 3. Delete orphaned hearings (without valid case or lawyer)
DELETE FROM hearings 
WHERE lawyer_id IS NULL 
   OR case_id IS NULL
   OR NOT EXISTS (SELECT 1 FROM cases WHERE cases.id = hearings.case_id);

-- 4. Add foreign key constraint
ALTER TABLE hearings 
ADD CONSTRAINT hearings_lawyer_id_fkey 
FOREIGN KEY (lawyer_id) 
REFERENCES users(id) 
ON DELETE CASCADE;

-- 5. Make lawyer_id required
ALTER TABLE hearings 
ALTER COLUMN lawyer_id SET NOT NULL;

-- 6. Add indexes
CREATE INDEX IF NOT EXISTS idx_hearings_lawyer_id ON hearings(lawyer_id);
CREATE INDEX IF NOT EXISTS idx_hearings_case_id ON hearings(case_id);
CREATE INDEX IF NOT EXISTS idx_hearings_date ON hearings(hearing_date);

-- ============================================================================
-- FIX RLS POLICIES FOR HEARINGS
-- ============================================================================

ALTER TABLE hearings ENABLE ROW LEVEL SECURITY;

-- Drop old policies
DROP POLICY IF EXISTS "Allow all SELECT for hearings" ON hearings;
DROP POLICY IF EXISTS "Allow all INSERT for hearings" ON hearings;
DROP POLICY IF EXISTS "Allow all UPDATE for hearings" ON hearings;
DROP POLICY IF EXISTS "Allow all DELETE for hearings" ON hearings;

-- Create permissive policies for custom auth
CREATE POLICY "Allow all SELECT for hearings"
ON hearings FOR SELECT
USING (true);

CREATE POLICY "Allow all INSERT for hearings"
ON hearings FOR INSERT
WITH CHECK (true);

CREATE POLICY "Allow all UPDATE for hearings"
ON hearings FOR UPDATE
USING (true);

CREATE POLICY "Allow all DELETE for hearings"
ON hearings FOR DELETE
USING (true);

-- ============================================================================
-- ✅ MIGRATION COMPLETE
-- 
-- التغييرات:
-- ✅ إضافة lawyer_id لجدول hearings
-- ✅ ملء البيانات الحالية
-- ✅ إضافة Foreign Key Constraints
-- ✅ RLS Policies محدّثة
-- ✅ Indexes للأداء
-- ============================================================================
