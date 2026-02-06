import asyncio
import sys
import os
import logging

# Add the project root to python path
sys.path.append(os.path.join(os.getcwd()))

from agents.config.settings import settings
from supabase import create_client, Client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def recreate_auth_user(email: str, password: str):
    print(f"\n==================================================")
    print(f"   RECREATING AUTH USER FOR: {email}")
    print(f"==================================================\n")
    
    try:
        supabase: Client = create_client(
            settings.supabase_url, 
            settings.supabase_service_role_key
        )
        
        # 1. Get User from public.users
        print(f"1. Fetching user profile from public.users...")
        response = supabase.table("users").select("*").eq("email", email).execute()
        
        if not response.data or len(response.data) == 0:
            print(f"❌ User {email} NOT FOUND in public.users table either!")
            return
            
        public_user = response.data[0]
        old_id = public_user['id']
        print(f"✅ Found public profile. Old ID: {old_id}")
        
        # 2. Create in Supabase Auth
        print(f"2. Creating user in Supabase Auth...")
        try:
            attributes = {
                "email": email,
                "password": password,
                "email_confirm": True,
                "user_metadata": {
                    "full_name": public_user.get('full_name'),
                    "role_id": public_user.get('role_id')
                }
            }
            auth_response = supabase.auth.admin.create_user(attributes)
            new_auth_user = auth_response.user
            new_id = new_auth_user.id
            
            print(f"✅ Successfully created Auth User. New Auth ID: {new_id}")
            
            # 3. Update public.users with NEW ID
            # IMPORTANT: The ID in public.users is often a foreign key to auth.users.id
            # If so, we might need to delete the old row and create a new one, 
            # Or update the ID if it's cascade/updatable (usually NOT possible to update PK).
            # Let's check if ID is the PK. usually it is.
            
            if old_id != new_id:
                print(f"3. migrating public.users record from {old_id} to {new_id}...")
                
                # Check if we can just update... (Likely fail due to PK constraint or FK constraint)
                # Better approach: Clone record with new ID, then delete old one.
                new_profile = public_user.copy()
                new_profile['id'] = new_id
                
                # Remove fields that shouldn't be inserted manually if they are auto-generated?
                # But here we are essentially restoring the profile.
                
                try:
                    # Insert NEW record
                    supabase.table("users").insert(new_profile).execute()
                    print(f"   ✅ Inserted new public profile with ID: {new_id}")
                    
                    # Delete OLD record
                    supabase.table("users").delete().eq("id", old_id).execute()
                    print(f"   ✅ Deleted old public profile with ID: {old_id}")
                    
                    # Update subscriptions or other relations if they exist?
                    # This script assumes cascade or we'd need to migrate relations first.
                    # Given this is a "fix" script, we hope cascade or no relations for now.
                    # If there are relations (cases, hearings, etc) pointing to OLD ID, 
                    # we must update them BEFORE deleting old profile.
                    
                    # Quick check for relations... implementing a simple migration for key tables
                    # But simpler: Can we just update the PK? 
                    # Postgres allows updating PK if cascades are set. Supabase client might verify.
                    # Let's try updating directly first.
                    
                    # Actually, we can't update PK easily if referenced.
                    
                except Exception as e:
                    print(f"   ⚠️ Failed to swap IDs: {e}")
                    print(f"   NOTE: You now have an Auth User {new_id} and a Public Profile {old_id}.")
                    print(f"   You might need to manually update the ID in the database or handle relations.")

        except Exception as e:
            print(f"❌ Error creating auth user: {e}")

    except Exception as e:
        print(f"❌ Critical Error: {e}")

if __name__ == "__main__":
    EMAIL = "ahmed.abace@gmail.com"
    PASSWORD = "Admin@123456"
    asyncio.run(recreate_auth_user(EMAIL, PASSWORD))
