import sys
import os

# Ensure we can import from e:\law
sys.path.append("e:\\law")

from dotenv import load_dotenv
load_dotenv()

try:
    from agents.config.settings import settings
    from api.security import SECRET_KEY, ALGORITHM

    print(f"✅ Settings Loaded Successfully")
    print(f"🔑 Secret Key (First 4 chars): {SECRET_KEY[:4]}****")
    print(f"🔒 Algorithm: {ALGORITHM}")
    
    # Verify it matches env
    env_secret = os.getenv("JWT_SECRET_KEY")
    if SECRET_KEY == env_secret:
        print("✅ Success: Code is using Environment Variable")
    else:
        print("❌ Error: Code mismatch with Environment Variable")

except Exception as e:
    print(f"❌ Failed to load security settings: {e}")
