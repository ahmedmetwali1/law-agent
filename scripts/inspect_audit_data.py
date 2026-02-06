import asyncio
import os
import sys
from supabase import create_client, Client

# Add parent dir to path to import settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from agents.config.settings import settings
except ImportError:
    class Settings:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    settings = Settings()

async def inspect_audit_data():
    print("🕵️ Audit Log Data Inspector")
    print("----------------------------")
    
    url = settings.supabase_url
    key = settings.supabase_service_role_key
    
    if not url or not key:
        print("❌ Error: Missing credentials.")
        return

    supabase: Client = create_client(url, key)
    
    try:
        # Fetch unique action values
        # Note: 'distinct' is not directly exposed in simple postgrest-py easily without grouping, 
        # so we'll fetch all and aggregate in python (assuming log volume is low in dev)
        res = supabase.table("audit_logs").select("action").execute()
        
        actions = [row['action'] for row in res.data]
        unique_actions = set(actions)
        
        print(f"📊 Total Rows: {len(actions)}")
        print(f"🧩 Unique 'action' values found: {unique_actions}")
        
        valid_values = {'INSERT', 'UPDATE', 'DELETE'}
        invalid_values = unique_actions - valid_values
        
        if invalid_values:
            print(f"❌ Found INVALID values: {invalid_values}")
            print("   -> These values are preventing the constraint from being applied.")
        else:
            print("✅ All existing values are valid ('INSERT', 'UPDATE', 'DELETE').")
            print("   -> If migration failed, it might be due to a race condition or hidden character.")

    except Exception as e:
        print(f"❌ Failed to fetch data: {e}")

if __name__ == "__main__":
    asyncio.run(inspect_audit_data())
