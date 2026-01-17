-- ============================================================================
-- Add lawyer_id to cases table for security (FIXED VERSION)
-- إضافة lawyer_id لجدول القضايا لتحسين الأمان (نسخة مُصلحة)
-- ============================================================================

-- 1. Add lawyer_id column (nullable first)
ALTER TABLE cases 
ADD COLUMN IF NOT EXISTS lawyer_id UUID;

-- 2. Populate lawyer_id from client's lawyer_id (for existing data)
UPDATE cases 
SET lawyer_id = clients.lawyer_id
FROM clients
WHERE cases.client_id = clients.id
AND cases.lawyer_id IS NULL;

-- 3. Delete orphaned cases (cases without valid client or lawyer)
-- ⚠️ IMPORTANT: This removes invalid data!
DELETE FROM cases 
WHERE lawyer_id IS NULL 
   OR client_id IS NULL
   OR NOT EXISTS (SELECT 1 FROM clients WHERE clients.id = cases.client_id)
   OR NOT EXISTS (SELECT 1 FROM users WHERE users.id = cases.lawyer_id);

-- 4. Now add the foreign key constraint
ALTER TABLE cases 
ADD CONSTRAINT cases_lawyer_id_fkey 
FOREIGN KEY (lawyer_id) 
REFERENCES users(id) 
ON DELETE CASCADE;

-- 5. Make lawyer_id required (NOT NULL)
ALTER TABLE cases 
ALTER COLUMN lawyer_id SET NOT NULL;

-- 6. Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_cases_lawyer_id ON cases(lawyer_id);
CREATE INDEX IF NOT EXISTS idx_cases_lawyer_client ON cases(lawyer_id, client_id);

-- ============================================================================
-- ROW LEVEL SECURITY (RLS) - الأمان على مستوى الصفوف
-- ============================================================================

-- Enable RLS on cases table
ALTER TABLE cases ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if any (to avoid conflicts)
DROP POLICY IF EXISTS "Lawyers can view own cases" ON cases;
DROP POLICY IF EXISTS "Lawyers can insert own cases" ON cases;
DROP POLICY IF EXISTS "Lawyers can update own cases" ON cases;
DROP POLICY IF EXISTS "Lawyers can delete own cases" ON cases;

-- Policy: Lawyers can only view their own cases
CREATE POLICY "Lawyers can view own cases"
ON cases FOR SELECT
USING (auth.uid() = lawyer_id);

-- Policy: Lawyers can only insert cases for their own clients
CREATE POLICY "Lawyers can insert own cases"
ON cases FOR INSERT
WITH CHECK (
    auth.uid() = lawyer_id 
    AND EXISTS (
        SELECT 1 FROM clients 
        WHERE clients.id = cases.client_id 
        AND clients.lawyer_id = auth.uid()
    )
);

-- Policy: Lawyers can only update their own cases
CREATE POLICY "Lawyers can update own cases"
ON cases FOR UPDATE
USING (auth.uid() = lawyer_id);

-- Policy: Lawyers can only delete their own cases
CREATE POLICY "Lawyers can delete own cases"
ON cases FOR DELETE
USING (auth.uid() = lawyer_id);

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Check if lawyer_id was added successfully
-- SELECT column_name, data_type, is_nullable 
-- FROM information_schema.columns 
-- WHERE table_name = 'cases' AND column_name = 'lawyer_id';

-- Check for any remaining orphaned records
-- SELECT COUNT(*) FROM cases WHERE lawyer_id IS NULL;

-- Verify foreign key constraint
-- SELECT constraint_name, constraint_type 
-- FROM information_schema.table_constraints 
-- WHERE table_name = 'cases' AND constraint_name = 'cases_lawyer_id_fkey';

-- ============================================================================
-- ✅ MIGRATION COMPLETE
-- 
-- التغييرات المُطبقة:
-- ✅ إضافة lawyer_id لجدول cases
-- ✅ تنظيف البيانات غير الصالحة
-- ✅ إضافة Foreign Key Constraint
-- ✅ إضافة RLS Policies (أمان كامل)
-- ✅ إضافة Indexes (أداء محسّن)
-- 
-- الأمان: ✅ محكم - لا يمكن الوصول لقضايا المحامين الآخرين
-- ============================================================================
