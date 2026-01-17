-- ============================================================================
-- TEMPORARY FIX: Disable RLS for Custom Auth System
-- حل مؤقت: تعطيل RLS لنظام المصادقة المخصص
-- ============================================================================

-- Option 1: Completely disable RLS (NOT RECOMMENDED for production)
-- الخيار 1: تعطيل RLS بالكامل (غير موصى به للإنتاج)
ALTER TABLE cases DISABLE ROW LEVEL SECURITY;

-- ============================================================================
-- Option 2: Create permissive policies (RECOMMENDED for development)
-- الخيار 2: إنشاء policies مرنة (موصى به للتطوير)
-- ============================================================================

-- First, drop existing policies
DROP POLICY IF EXISTS "Lawyers can view own cases" ON cases;
DROP POLICY IF EXISTS "Lawyers can insert own cases" ON cases;
DROP POLICY IF EXISTS "Lawyers can update own cases" ON cases;
DROP POLICY IF EXISTS "Lawyers can delete own cases" ON cases;

-- Create new permissive policies for development
-- These allow all operations - you'll need to implement security at application level
CREATE POLICY "Allow all SELECT for authenticated users"
ON cases FOR SELECT
USING (true);

CREATE POLICY "Allow all INSERT for authenticated users"
ON cases FOR INSERT
WITH CHECK (true);

CREATE POLICY "Allow all UPDATE for authenticated users"
ON cases FOR UPDATE
USING (true);

CREATE POLICY "Allow all DELETE for authenticated users"
ON cases FOR DELETE
USING (true);

-- ============================================================================
-- Apply same fix to opponents table
-- ============================================================================

ALTER TABLE opponents ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow all SELECT for opponents" ON opponents;
DROP POLICY IF EXISTS "Allow all INSERT for opponents" ON opponents;
DROP POLICY IF EXISTS "Allow all UPDATE for opponents" ON opponents;
DROP POLICY IF EXISTS "Allow all DELETE for opponents" ON opponents;

CREATE POLICY "Allow all SELECT for opponents"
ON opponents FOR SELECT
USING (true);

CREATE POLICY "Allow all INSERT for opponents"
ON opponents FOR INSERT
WITH CHECK (true);

CREATE POLICY "Allow all UPDATE for opponents"
ON opponents FOR UPDATE
USING (true);

CREATE POLICY "Allow all DELETE for opponents"
ON opponents FOR DELETE
USING (true);

-- ============================================================================
-- IMPORTANT NOTES
-- ============================================================================
-- 
-- ⚠️ هذا الحل مؤقت للتطوير فقط!
-- 
-- للإنتاج، يجب عليك:
-- 1. استخدام Supabase Auth بدلاً من Custom Auth
-- 2. أو تنفيذ الأمان على مستوى التطبيق (Application Level Security)
-- 3. أو استخدام Service Role Key من الـ Backend فقط
-- 
-- الوضع الحالي:
-- - Custom FastAPI Auth ← Frontend
-- - Supabase Database (مع RLS معطل/مرن)
-- 
-- الأمان يعتمد الآن على:
-- ✅ JWT Token validation في FastAPI
-- ✅ lawyer_id في الاستعلامات
-- ❌ RLS غير فعّال حالياً
-- ============================================================================
