import asyncio
from api.database import get_supabase_client

async def fetch_countries():
    client = get_supabase_client()
    try:
        res = client.table("countries").select("id, name, name_ar").execute()
        print("--- Countries ---")
        found_sa = False
        sa_id = None
        for c in res.data:
            print(f"Name: {c.get('name')} | Arabic: {c.get('name_ar')} | ID: {c.get('id')}")
            if c.get('name').lower() == 'saudi arabia' or 'saudi' in c.get('name').lower():
                sa_id = c.get('id')
                found_sa = True
        
        if found_sa:
            print(f"\n✅ FOUND SAUDI ID: {sa_id}")
        else:
            print("\n❌ Saudi Arabia not found in DB.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(fetch_countries())
