import asyncio
import os
from dotenv import load_dotenv
import logging

# Load Env
load_dotenv()

# Setup minimal logging to avoid crash
logging.basicConfig(level=logging.INFO)

# Mock Depends
from unittest.mock import MagicMock
# We need to hack the import because clean 'api.routers.admin_subscriptions' requires app context maybe? 
# Hopefully not.

from api.routers.admin_subscriptions import list_all_subscriptions

async def test_logic():
    print("--- Testing API Logic Internally ---")
    try:
        # User doesn't matter, pass empty dict or mock
        # check_admin_access is a dependency, but list_all_subscriptions takes current_user as arg
        # We can pass a mock user
        mock_user = {"id": "admin", "role": "admin"}
        
        subscriptions = await list_all_subscriptions(status=None, current_user=mock_user)
        
        found = False
        for sub in subscriptions:
            if "Ahmed Metwally" in sub['lawyer_name'] or "احمد متولى" in sub['lawyer_name']:
                found = True
                print(f"User: {sub['lawyer_name']}")
                print(f"Status: {sub['status']}")
                print(f"End Date: {sub['end_date']}")
                print(f"Words Used: {sub['words_used']}")
                print(f"Max Words: {sub['max_words']}")
                print(f"Max Storage: {sub['max_storage']}")
                print(f"Assistants Count: {sub['assistants_count']}")
                print(f"Extra Words (Calculated?): {sub['max_words']} - Base")
        
        if not found:
            print("Target user not found in subscription list.")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_logic())
