import asyncio
import os
import sys
from supabase import create_client, Client

# Add parent dir to path to import settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from agents.config.settings import settings
except ImportError:
    # Fallback if running directly without package context
    class Settings:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    settings = Settings()

async def test_audit_constraint():
    print("🕵️ Audit Log Constraint Debugger")
    print("--------------------------------")
    
    url = settings.supabase_url
    key = settings.supabase_service_role_key
    
    if not url or not key:
        print("❌ Error: Missing credentials. Check SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.")
        return

    supabase: Client = create_client(url, key)
    
    # 1. Test INSERT (Should work)
    print("\n1. Testing 'INSERT' action...")
    try:
        res = supabase.table("audit_logs").insert({
            "table_name": "debug_test",
            "action": "INSERT",
            "record_id": "00000000-0000-0000-0000-000000000000"
        }).execute()
        print("✅ INSERT action: Allowed")
    except Exception as e:
        print(f"❌ INSERT action: Failed! {e}")

    # 2. Test UPDATE (The suspect)
    print("\n2. Testing 'UPDATE' action...")
    try:
        res = supabase.table("audit_logs").insert({
            "table_name": "debug_test",
            "action": "UPDATE",
            "record_id": "00000000-0000-0000-0000-000000000000"
        }).execute()
        print("✅ UPDATE action: Allowed (Constraint is FIXED!)")
    except Exception as e:
        print(f"❌ UPDATE action: Failed! {e}")
        print("   -> This confirms the constraint is still restricting 'UPDATE'.")

    # 3. Test DELETE (The other suspect)
    print("\n3. Testing 'DELETE' action...")
    try:
        res = supabase.table("audit_logs").insert({
            "table_name": "debug_test",
            "action": "DELETE",
            "record_id": "00000000-0000-0000-0000-000000000000"
        }).execute()
        print("✅ DELETE action: Allowed")
    except Exception as e:
        print(f"❌ DELETE action: Failed! {e}")

    # Cleanup
    print("\n🧹 Cleaning up debug logs...")
    try:
        supabase.table("audit_logs").delete().eq("table_name", "debug_test").execute()
    except:
        pass

if __name__ == "__main__":
    asyncio.run(test_audit_constraint())
