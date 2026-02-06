-- 1. DROP ALL EXISTING POLICIES (Clean Slate)
DROP POLICY IF EXISTS "Lawyers can delete their own clients" ON clients;
DROP POLICY IF EXISTS "Lawyers can view their own clients" ON clients;
DROP POLICY IF EXISTS "Lawyers can update their own clients" ON clients;
DROP POLICY IF EXISTS "Lawyers can insert their own clients" ON clients;
DROP POLICY IF EXISTS "Service Role Full Access" ON clients;

-- 2. CREATE SERVICE ROLE BYPASS POLICY (Explicit & Permissive)
CREATE POLICY "Service Role Full Access"
ON clients
FOR ALL
USING ((select auth.role()) = 'service_role')
WITH CHECK ((select auth.role()) = 'service_role');

-- 3. CREATE LAWYER POLICIES (Restricted)
CREATE POLICY "Lawyers can view their own clients"
ON clients
FOR SELECT
USING (auth.uid() = lawyer_id);

CREATE POLICY "Lawyers can insert their own clients"
ON clients
FOR INSERT
WITH CHECK (auth.uid() = lawyer_id);

CREATE POLICY "Lawyers can update their own clients"
ON clients
FOR UPDATE
USING (auth.uid() = lawyer_id);

CREATE POLICY "Lawyers can delete their own clients"
ON clients
FOR DELETE
USING (auth.uid() = lawyer_id);

-- 4. Enable RLS on Table (Just in case)
ALTER TABLE clients ENABLE ROW LEVEL SECURITY;
