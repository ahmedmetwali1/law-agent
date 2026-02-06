"""
Script to run Super Admin migration
Creates platform_settings, support_ticket_templates, and system_announcements tables
"""
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

def run_migration():
    """Execute migration 12 - Super Admin Dashboard"""
    
    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Error: Supabase credentials not found in .env")
        return False
    
    # Create Supabase client
    supabase = create_client(supabase_url, supabase_key)
    
    # Read migration file
    migration_file = "migrations/12_super_admin_dashboard.sql"
    
    if not os.path.exists(migration_file):
        print(f"❌ Error: Migration file not found: {migration_file}")
        return False
    
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    print(f"📝 Running migration: {migration_file}")
    print("=" * 60)
    
    try:
        # Execute SQL (Supabase Python client doesn't have direct SQL execution)
        # User needs to run this manually in Supabase SQL Editor
        print("⚠️  Manual Action Required:")
        print("")
        print("Please execute the following SQL in your Supabase SQL Editor:")
        print("")
        print("1. Go to: https://app.supabase.com/project/YOUR_PROJECT/sql")
        print("2. Copy the contents of: migrations/12_super_admin_dashboard.sql")
        print("3. Paste and execute")
        print("")
        print("=" * 60)
        print("")
        print("Alternatively, if you have psql installed:")
        print("")
        print("Run this command:")
        print(f"  psql $DATABASE_URL -f {migration_file}")
        print("")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Super Admin Dashboard - Migration Script")
    print("")
    run_migration()
