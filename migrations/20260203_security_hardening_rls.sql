-- Security Hardening: Enable RLS on Operational Tables
-- Date: 2026-02-03
-- Author: Security Auditor Agent

-- ==============================================================================
-- 1. Helper Macro for Common Policies
--    We define policies for: SELECT, INSERT, UPDATE, DELETE
--    Rule: Users can only operate on records where lawyer_id == auth.uid()
-- ==============================================================================

-- CASES
ALTER TABLE cases ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Lawyers can view their own cases" ON cases;
CREATE POLICY "Lawyers can view their own cases" ON cases
    FOR SELECT USING (auth.uid() = lawyer_id);

DROP POLICY IF EXISTS "Lawyers can insert their own cases" ON cases;
CREATE POLICY "Lawyers can insert their own cases" ON cases
    FOR INSERT WITH CHECK (auth.uid() = lawyer_id);

DROP POLICY IF EXISTS "Lawyers can update their own cases" ON cases;
CREATE POLICY "Lawyers can update their own cases" ON cases
    FOR UPDATE USING (auth.uid() = lawyer_id);

DROP POLICY IF EXISTS "Lawyers can delete their own cases" ON cases;
CREATE POLICY "Lawyers can delete their own cases" ON cases
    FOR DELETE USING (auth.uid() = lawyer_id);


-- HEARINGS (Depends on case_id usually, but has lawyer_id column for speed/security)
ALTER TABLE hearings ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Lawyers can view their own hearings" ON hearings;
CREATE POLICY "Lawyers can view their own hearings" ON hearings
    FOR SELECT USING (auth.uid() = lawyer_id);

DROP POLICY IF EXISTS "Lawyers can insert their own hearings" ON hearings;
CREATE POLICY "Lawyers can insert their own hearings" ON hearings
    FOR INSERT WITH CHECK (auth.uid() = lawyer_id);

DROP POLICY IF EXISTS "Lawyers can update their own hearings" ON hearings;
CREATE POLICY "Lawyers can update their own hearings" ON hearings
    FOR UPDATE USING (auth.uid() = lawyer_id);

DROP POLICY IF EXISTS "Lawyers can delete their own hearings" ON hearings;
CREATE POLICY "Lawyers can delete their own hearings" ON hearings
    FOR DELETE USING (auth.uid() = lawyer_id);


-- TASKS
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Lawyers can view their own tasks" ON tasks;
CREATE POLICY "Lawyers can view their own tasks" ON tasks
    FOR SELECT USING (auth.uid() = lawyer_id);

DROP POLICY IF EXISTS "Lawyers can insert their own tasks" ON tasks;
CREATE POLICY "Lawyers can insert their own tasks" ON tasks
    FOR INSERT WITH CHECK (auth.uid() = lawyer_id);

DROP POLICY IF EXISTS "Lawyers can update their own tasks" ON tasks;
CREATE POLICY "Lawyers can update their own tasks" ON tasks
    FOR UPDATE USING (auth.uid() = lawyer_id);

DROP POLICY IF EXISTS "Lawyers can delete their own tasks" ON tasks;
CREATE POLICY "Lawyers can delete their own tasks" ON tasks
    FOR DELETE USING (auth.uid() = lawyer_id);


-- DOCUMENTS
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Lawyers can view their own documents" ON documents;
CREATE POLICY "Lawyers can view their own documents" ON documents
    FOR SELECT USING (auth.uid() = lawyer_id);

DROP POLICY IF EXISTS "Lawyers can insert their own documents" ON documents;
CREATE POLICY "Lawyers can insert their own documents" ON documents
    FOR INSERT WITH CHECK (auth.uid() = lawyer_id);

DROP POLICY IF EXISTS "Lawyers can update their own documents" ON documents;
CREATE POLICY "Lawyers can update their own documents" ON documents
    FOR UPDATE USING (auth.uid() = lawyer_id);

DROP POLICY IF EXISTS "Lawyers can delete their own documents" ON documents;
CREATE POLICY "Lawyers can delete their own documents" ON documents
    FOR DELETE USING (auth.uid() = lawyer_id);


-- POLICE RECORDS (Uses user_id as filter_column according to schema, assuming user_id IS the lawyer/user)
-- Schema says: user_id references users. 
-- We should verify if we filter by user_id or lawyer_id. 
-- schema_registry says "filter_column": "user_id". But let's check columns...
-- columns: id, record_number..., user_id (required).
-- Let's assume auth.uid() == user_id.

ALTER TABLE police_records ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view their own police records" ON police_records;
CREATE POLICY "Users can view their own police records" ON police_records
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert their own police records" ON police_records;
CREATE POLICY "Users can insert their own police records" ON police_records
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update their own police records" ON police_records;
CREATE POLICY "Users can update their own police records" ON police_records
    FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete their own police records" ON police_records;
CREATE POLICY "Users can delete their own police records" ON police_records
    FOR DELETE USING (auth.uid() = user_id);

-- CLIENTS (Reinforce/Ensure coverage if previous migration missed anything)
-- We rely on 20260203_fix_clients_rls.sql for clients, but re-asserting ENABLE RLS is harmless.
ALTER TABLE clients ENABLE ROW LEVEL SECURITY;
