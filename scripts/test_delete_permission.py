
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.config.settings import settings
from supabase import create_client, Client
import asyncio

SUPABASE_URL = settings.supabase_url
SUPABASE_KEY = settings.supabase_service_role_key
LAWYER_ID = "4e22ac65-9024-42f9-9b94-dc4980c51ad6"


if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: Missing credentials in settings")
    exit(1)

import jwt

def check_key_role(token):
    try:
        # Decode without verification just to inspect payload
        decoded = jwt.decode(token, options={"verify_signature": False})
        role = decoded.get("role", "unknown")
        print(f"🔑 Token Role: {role}")
        return role
    except Exception as e:
        print(f"⚠️ Could not decode token: {e}")
        return "error"

async def test_delete():
    role = check_key_role(SUPABASE_KEY)
    
    print(f"🔧 Initializing Supabase Client...")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # 1. Insert Dummy Client
    dummy_client = {
        "full_name": "Test Delete Permission",
        "email": "test_del@example.com",
        "phone": "0000000000",
        "lawyer_id": LAWYER_ID
    }
    
    print(f"📝 Attempting to INSERT dummy client...")
    try:
        insert_res = supabase.table("clients").insert(dummy_client).execute()
        if not insert_res.data:
            print("❌ Insert Failed: No data returned.")
            return
        
        client_id = insert_res.data[0]['id']
        print(f"✅ Insert Successful. ID: {client_id}")
        
    except Exception as e:
        print(f"❌ Insert Failed with Exception: {type(e)}")
        if hasattr(e, 'message'):
            print(f"Message: {e.message}")
        if hasattr(e, 'code'):
            print(f"Code: {e.code}")
        if hasattr(e, 'details'):
            print(f"Details: {e.details}")
        print(f"Raw: {e}")
        return

    # 2. Attempt Delete
    print(f"🗑️ Attempting to DELETE client {client_id}...")
    try:
        # Use count='exact' to verify deletion
        delete_res = supabase.table("clients").delete(count='exact').eq("id", client_id).execute()
        
        print(f"📊 Delete Response: {delete_res}")
        
        if delete_res.count is not None and delete_res.count > 0:
            print(f"✅ Delete Successful! Count: {delete_res.count}")
        else:
            print(f"❌ Delete Failed! Count is 0. RLS or Constraints likely blocking.")
            
    except Exception as e:
        print(f"❌ Delete Failed with Exception: {type(e)}")
        print(f"Raw: {e}")

if __name__ == "__main__":
    asyncio.run(test_delete())
