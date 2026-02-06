from agents.config.database import get_supabase_client
import json
from datetime import datetime

def datetime_handler(x):
    if isinstance(x, datetime):
        return x.isoformat()
    return str(x)

def inspect_schema():
    db = get_supabase_client()
    
    # 1. Inspect 'documents' table
    print("--- Documents Table ---")
    try:
        res = db.table("documents").select("*").limit(1).execute()
        if res.data:
            print("Columns:", list(res.data[0].keys()))
        else:
            print("No data in documents table.")
    except Exception as e:
        print(f"Error inspecting documents: {e}")

    # 2. Inspect 'ai_chat_messages' (just to be safe)
    print("\n--- AI Chat Messages Table ---")
    try:
        res = db.table("ai_chat_messages").select("*").limit(1).execute()
        if res.data:
            print("Columns:", list(res.data[0].keys()))
    except Exception as e:
        print(f"Error inspecting messages: {e}")

if __name__ == "__main__":
    inspect_schema()
