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

async def check_duplicates():
    print("--- Checking for duplicate lawyer_subscriptions ---")
    
    # Get all subscriptions
    res = supabase.table("lawyer_subscriptions").select("id, lawyer_id, created_at, status, end_date").execute()
    
    if not res.data:
        print("No subscriptions found.")
        return

    lawyer_map = {}
    for sub in res.data:
        lid = sub['lawyer_id']
        if lid not in lawyer_map:
            lawyer_map[lid] = []
        lawyer_map[lid].append(sub)

    duplicates_found = 0
    for lid, subs in lawyer_map.items():
        if len(subs) > 1:
            duplicates_found += 1
            print(f"\nUser {lid} has {len(subs)} subscriptions:")
            # Sort by created_at
            subs.sort(key=lambda x: x['created_at'], reverse=True)
            for i, s in enumerate(subs):
                print(f"  {i+1}. ID: {s['id']} | Status: {s['status']} | Created: {s['created_at']} | End: {s['end_date']}")

    if duplicates_found == 0:
        print("\nNo users with multiple subscriptions found.")
    else:
        print(f"\nFound {duplicates_found} users with multiple subscriptions.")

if __name__ == "__main__":
    asyncio.run(check_duplicates())
