import asyncio
import sys
import os

# Add the project root to python path
sys.path.append(os.path.join(os.getcwd()))

from agents.config.database import get_supabase_client
from api.security import verify_password, hash_password

async def debug_hash():
    email = "ahmed.abace@gmail.com"
    password = "Admin@123456"
    
    print(f"Checking hash for {email} with password '{password}'")
    
    supabase = get_supabase_client()
    
    # 1. Get User
    result = supabase.table("users").select("password_hash").eq("email", email).execute()
    
    if not result.data:
        print("❌ User not found in DB")
        return
        
    stored_hash = result.data[0]['password_hash']
    print(f"Stored Hash: {stored_hash}")
    
    # 2. Verify with api.security (used by auth.py)
    is_valid = verify_password(password, stored_hash)
    print(f"✅ api.security.verify_password result: {is_valid}")
    
    # 3. Test generating a new hash
    new_hash = hash_password(password)
    print(f"New Generated Hash: {new_hash}")
    print(f"Verify new hash: {verify_password(password, new_hash)}")

if __name__ == "__main__":
    asyncio.run(debug_hash())
