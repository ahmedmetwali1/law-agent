import asyncio
import sys
import os

sys.path.append(os.path.join(os.getcwd()))

from agents.config.database import get_supabase_client
from api.security import hash_password

async def force_reset():
    email = "ahmed.abace@gmail.com"
    new_pass = "123456"
    
    print(f"Force resetting password for {email} to '{new_pass}'")
    
    supabase = get_supabase_client()
    
    # 1. Get User ID
    res = supabase.table("users").select("id").eq("email", email).execute()
    if not res.data:
        print("User not found!")
        return
        
    user_id = res.data[0]['id']
    
    # 2. Hash and Update
    hashed = hash_password(new_pass)
    
    update_res = supabase.table("users").update({
        "password_hash": hashed,
        "updated_at": "now()"
    }).eq("id", user_id).execute()
    
    if update_res.data:
        print("✅ Password updated successfully to '123456'")
    else:
        print("❌ Failed to update password")

if __name__ == "__main__":
    asyncio.run(force_reset())
