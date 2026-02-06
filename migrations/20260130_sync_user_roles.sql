-- Function to fetch the role name from the roles table
-- This keeps the technical 'role' column in sync with the role_id
CREATE OR REPLACE FUNCTION sync_user_role()
RETURNS TRIGGER AS $$
BEGIN
    -- We sync with 'name' (English) to maintain compatibility with backend logic
    -- The frontend uses role object for display (Arabic name)
    SELECT name INTO NEW.role FROM roles WHERE id = NEW.role_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to run before insert or any update to role_id on users table
DROP TRIGGER IF EXISTS trg_sync_user_role ON users;
CREATE TRIGGER trg_sync_user_role
BEFORE INSERT OR UPDATE OF role_id ON users
FOR EACH ROW
EXECUTE FUNCTION sync_user_role();

-- Perform initial sync for all existing users
UPDATE users u
SET role = r.name
FROM roles r
WHERE u.role_id = r.id;

-- Ensure roles table has the correct Arabic names for basic roles
UPDATE roles SET name_ar = 'مدير النظام' WHERE name = 'manager';
UPDATE roles SET name_ar = 'محامي' WHERE name = 'lawyer';
UPDATE roles SET name_ar = 'مساعد' WHERE name = 'assistant';
