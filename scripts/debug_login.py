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

# Force UTF-8 for stdout/stderr
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

async def debug_login(email: str, password: str):
    print(f"\n==================================================")
    print(f"   DEBUGGING LOGIN FOR: {email}")
    print(f"==================================================\n")
    print(f"Supabase URL: {settings.supabase_url}")
    
    # Check if URL matches the one in user logs
    if "152.67.159.164" not in settings.supabase_url and "localhost" not in settings.supabase_url:
        print(f"⚠️ WARNING: Configured URL might differ from logs")

    try:
        supabase: Client = create_client(
            settings.supabase_url, 
            settings.supabase_service_role_key
        )
        
        # 1. Inspect User Status via Admin API
        print(f"\n--- 1. Inspecting User Status (Admin API) ---")
        user_id = None
        try:
            users = supabase.auth.admin.list_users()
            target_user = next((u for u in users if u.email == email), None)
            
            if target_user:
                user_id = target_user.id
                print(f"✅ User Found in Auth DB:")
                print(f"   - ID: {target_user.id}")
                print(f"   - Email Confirmed: {target_user.email_confirmed_at}")
                print(f"   - Last Sign In: {target_user.last_sign_in_at}")
                print(f"   - App Metadata: {target_user.app_metadata}")
                
                # Check for issues
                if not target_user.email_confirmed_at:
                    print(f"❌ ISSUE: Email is NOT confirmed.")
                    print(f"   -> Attempting to confirm email now...")
                    try:
                        supabase.auth.admin.update_user_by_id(
                            user_id, 
                            {"email_confirm": True}
                        )
                        print(f"   ✅ Email manually confirmed via Admin API.")
                    except Exception as e:
                        print(f"   ❌ Failed to confirm email: {e}")

            else:
                print(f"❌ User {email} NOT FOUND in Supabase Auth DB!")
                return

        except Exception as e:
            print(f"❌ Error inspecting admin user: {e}")

        # 2. Attempt Login via Client (Simulating Frontend)
        print(f"\n--- 2. Attempting Direct Login (Client API) ---")
        try:
            response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.session:
                print(f"✅ Login SUCCESSFUL!")
                print(f"   - Access Token: {response.session.access_token[:20]}...")
            else:
                print(f"❓ Login returned no session but no exception")

        except Exception as e:
             # Try to print more details about the exception
             print(f"❌ Login FAILED: {e}")
             if hasattr(e, 'message'):
                 print(f"   - Message: {e.message}")
             if hasattr(e, 'code'):
                 print(f"   - Code: {e.code}")
             if hasattr(e, 'response'): 
                 try:
                     print(f"   - Response: {e.response.text}")
                 except: pass

        # 3. Double Check Password Update
        print(f"\n--- 3. Verifying Password Reset ---")
        print(f"   -> Attempting to update password again to ensure synchronization...")
        try:
            if user_id:
                # Force update password again
                supabase.auth.admin.update_user_by_id(
                    user_id, 
                    {"password": password}
                )
                print(f"   ✅ Admin forced password update done.")
            else:
                print(f"   ⚠️ Skipping password update (No User ID)")
        except Exception as e:
            print(f"   ❌ Failed to force update password: {e}")

    except Exception as e:
        print(f"❌ Critical Connection Error: {e}")

if __name__ == "__main__":
    EMAIL = "ahmed.abace@gmail.com"
    PASSWORD = "Admin@123456"
    asyncio.run(debug_login(EMAIL, PASSWORD))
