-- Audit Logging System
-- Date: 2026-02-03
-- Purpose: Automate audit trails at the database level.

-- 1. Ensure Audit Table Exists (Idempotent)
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name TEXT NOT NULL,
    record_id UUID,
    action TEXT NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
    old_values JSONB,
    new_values JSONB,
    user_id UUID DEFAULT auth.uid(),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    ip_address TEXT, 
    user_agent TEXT
);

-- 2. Create the Trigger Function
CREATE OR REPLACE FUNCTION process_audit_log() RETURNS TRIGGER AS $$
DECLARE
    payload JSONB;
    v_old_data JSONB;
    v_new_data JSONB;
    v_user_id UUID;
BEGIN
    -- Get User ID safely
    v_user_id := auth.uid();

    IF (TG_OP = 'DELETE') THEN
        v_old_data := to_jsonb(OLD);
        INSERT INTO audit_logs (table_name, record_id, action, old_values, user_id)
        VALUES (TG_TABLE_NAME, OLD.id, 'DELETE', v_old_data, v_user_id);
        RETURN OLD;
    ELSIF (TG_OP = 'UPDATE') THEN
        v_old_data := to_jsonb(OLD);
        v_new_data := to_jsonb(NEW);
        
        -- Optimization: Only log if data actually changed
        IF v_old_data != v_new_data THEN
            INSERT INTO audit_logs (table_name, record_id, action, old_values, new_values, user_id)
            VALUES (TG_TABLE_NAME, NEW.id, 'UPDATE', v_old_data, v_new_data, v_user_id);
        END IF;
        RETURN NEW;
    ELSIF (TG_OP = 'INSERT') THEN
        v_new_data := to_jsonb(NEW);
        INSERT INTO audit_logs (table_name, record_id, action, new_values, user_id)
        VALUES (TG_TABLE_NAME, NEW.id, 'INSERT', v_new_data, v_user_id);
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 3. Apply Triggers to Key Tables (Drop first to avoid duplication)

-- CLIENTS
DROP TRIGGER IF EXISTS audit_clients_trigger ON clients;
CREATE TRIGGER audit_clients_trigger
AFTER INSERT OR UPDATE OR DELETE ON clients
FOR EACH ROW EXECUTE FUNCTION process_audit_log();

-- CASES
DROP TRIGGER IF EXISTS audit_cases_trigger ON cases;
CREATE TRIGGER audit_cases_trigger
AFTER INSERT OR UPDATE OR DELETE ON cases
FOR EACH ROW EXECUTE FUNCTION process_audit_log();

-- DOCUMENTS
DROP TRIGGER IF EXISTS audit_documents_trigger ON documents;
CREATE TRIGGER audit_documents_trigger
AFTER INSERT OR UPDATE OR DELETE ON documents
FOR EACH ROW EXECUTE FUNCTION process_audit_log();

-- TASKS
DROP TRIGGER IF EXISTS audit_tasks_trigger ON tasks;
CREATE TRIGGER audit_tasks_trigger
AFTER INSERT OR UPDATE OR DELETE ON tasks
FOR EACH ROW EXECUTE FUNCTION process_audit_log();

-- HEARINGS
DROP TRIGGER IF EXISTS audit_hearings_trigger ON hearings;
CREATE TRIGGER audit_hearings_trigger
AFTER INSERT OR UPDATE OR DELETE ON hearings
FOR EACH ROW EXECUTE FUNCTION process_audit_log();

-- POLICE_RECORDS
DROP TRIGGER IF EXISTS audit_police_records_trigger ON police_records;
CREATE TRIGGER audit_police_records_trigger
AFTER INSERT OR UPDATE OR DELETE ON police_records
FOR EACH ROW EXECUTE FUNCTION process_audit_log();

-- USERS (Auditing user changes is critical)
DROP TRIGGER IF EXISTS audit_users_trigger ON users;
CREATE TRIGGER audit_users_trigger
AFTER INSERT OR UPDATE OR DELETE ON users
FOR EACH ROW EXECUTE FUNCTION process_audit_log();
