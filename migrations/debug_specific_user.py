import asyncio
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Error: Missing env vars")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

async def list_all_lawyers():
    print("--- Listing All Lawyers (Limit 20) ---")
    
    # Select all lawyers
    res = supabase.table("users").select("id, full_name, role").eq("role", "lawyer").limit(20).execute()
    
    if not res.data:
        print("No lawyers found.")
        return

    print(f"Found {len(res.data)} lawyers:")
    for u in res.data:
        name = u.get('full_name', 'No Name')
        print(f"User: {name} (ID: {u['id']})")
        
        # Get Subscriptions
        sub_res = supabase.table("lawyer_subscriptions").select("*").eq("lawyer_id", u['id']).order("created_at", desc=True).execute()
        if sub_res.data:
            print(f"  > Subscriptions ({len(sub_res.data)}):")
            for i, s in enumerate(sub_res.data):
                print(f"    {i+1}. ID: {s['id']} | Status: {s['status']}")
                print(f"       Start: {s['start_date']} | End: {s['end_date']}")
                print(f"       ExtraSto: {s.get('extra_storage_gb')} GB | ExtraWords: {s.get('extra_words')}")
                print(f"       Created: {s['created_at']}")
        else:
            print("  > No subscriptions found (Or disconnected?)")
        print("-" * 30)

if __name__ == "__main__":
    asyncio.run(list_all_lawyers())
