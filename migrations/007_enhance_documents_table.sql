-- ============================================================================
-- Update documents table for OCR and AI features
-- تحديث جدول المستندات لدعم OCR والتلخيص
-- ============================================================================

-- 1. Add lawyer_id and client_id for relationships
ALTER TABLE documents 
ADD COLUMN IF NOT EXISTS lawyer_id UUID REFERENCES users(id) ON DELETE CASCADE,
ADD COLUMN IF NOT EXISTS client_id UUID REFERENCES clients(id) ON DELETE CASCADE;

-- 2. Add OCR tracking fields
ALTER TABLE documents
ADD COLUMN IF NOT EXISTS ocr_enabled BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS ocr_status VARCHAR(50) DEFAULT 'pending',
ADD COLUMN IF NOT EXISTS extraction_error TEXT;

-- 3. Add AI summary tracking fields
ALTER TABLE documents
ADD COLUMN IF NOT EXISTS summary_status VARCHAR(50) DEFAULT 'pending',
ADD COLUMN IF NOT EXISTS word_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS chunk_number INTEGER DEFAULT 1,
ADD COLUMN IF NOT EXISTS total_chunks INTEGER DEFAULT 1,
ADD COLUMN IF NOT EXISTS is_complete BOOLEAN DEFAULT false;

-- 4. Add file metadata
ALTER TABLE documents
ADD COLUMN IF NOT EXISTS file_size INTEGER,
ADD COLUMN IF NOT EXISTS uploaded_by UUID REFERENCES users(id);

-- 5. Populate lawyer_id from case
UPDATE documents 
SET lawyer_id = cases.lawyer_id,
    client_id = cases.client_id
FROM cases
WHERE documents.case_id = cases.id
AND documents.lawyer_id IS NULL;

-- 6. Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_documents_lawyer_id ON documents(lawyer_id);
CREATE INDEX IF NOT EXISTS idx_documents_client_id ON documents(client_id);
CREATE INDEX IF NOT EXISTS idx_documents_case_id ON documents(case_id);
CREATE INDEX IF NOT EXISTS idx_documents_ocr_status ON documents(ocr_status);
CREATE INDEX IF NOT EXISTS idx_documents_summary_status ON documents(summary_status);

-- 7. Enable RLS
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- Drop old policies
DROP POLICY IF EXISTS "Allow all SELECT for documents" ON documents;
DROP POLICY IF EXISTS "Allow all INSERT for documents" ON documents;
DROP POLICY IF EXISTS "Allow all UPDATE for documents" ON documents;
DROP POLICY IF EXISTS "Allow all DELETE for documents" ON documents;

-- Create permissive policies for custom auth
CREATE POLICY "Allow all SELECT for documents"
ON documents FOR SELECT
USING (true);

CREATE POLICY "Allow all INSERT for documents"
ON documents FOR INSERT
WITH CHECK (true);

CREATE POLICY "Allow all UPDATE for documents"
ON documents FOR UPDATE
USING (true);

CREATE POLICY "Allow all DELETE for documents"
ON documents FOR DELETE
USING (true);

-- ============================================================================
-- ✅ MIGRATION COMPLETE
-- 
-- الإضافات:
-- ✅ lawyer_id و client_id للعلاقات
-- ✅ حقول OCR (ocr_enabled, ocr_status, extraction_error)
-- ✅ حقول AI Summary (summary_status, word_count, chunks)
-- ✅ Metadata (file_size, uploaded_by)
-- ✅ Indexes للأداء
-- ✅ RLS Policies
-- 
-- الحقول الموجودة مسبقاً:
-- ✅ raw_text (للنص المستخرج)
-- ✅ ai_summary (للملخص)
-- ✅ is_analyzed (للحالة)
-- ============================================================================
