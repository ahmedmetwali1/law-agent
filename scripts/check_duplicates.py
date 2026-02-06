import asyncio
import sys
import os

# Add the project root to python path
sys.path.append(os.path.join(os.getcwd()))

from agents.config.database import get_supabase_client

async def check_duplicates():
    email = "ahmed.abace@gmail.com"
    print(f"Checking for duplicates for: {email}")
    
    supabase = get_supabase_client()
    
    # Get ALL users with this email
    result = supabase.table("users").select("id, email, password_hash, created_at").eq("email", email).execute()
    
    if not result.data:
        print("❌ No users found")
        return
        
    print(f"Found {len(result.data)} records:")
    for user in result.data:
        print(f"ID: {user['id']}")
        print(f"Created: {user['created_at']}")
        print(f"Hash: {user['password_hash'][:20]}...")
        print("-" * 30)

if __name__ == "__main__":
    asyncio.run(check_duplicates())
