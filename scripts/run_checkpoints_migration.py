"""
Run LangGraph Checkpoints Migration
Creates the 'langgraph_checkpoints' table in Supabase
"""
import sys
import os
from dotenv import load_dotenv

load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.config.database import get_supabase_client

def run_migration():
    """Execute the checkpoints table migration"""
    print("=" * 60)
    print("🚀 LangGraph Checkpoints Migration")
    print("=" * 60)
    
    try:
        # Read SQL file
        sql_file = os.path.join(
            os.path.dirname(__file__),
            "migrations",
            "create_langgraph_checkpoints.sql"
        )
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        print(f"📄 Loaded SQL from: {sql_file}")
        
        # Get Supabase client
        supabase = get_supabase_client()
        
        # Execute SQL via RPC
        # Note: Supabase client doesn't have direct SQL execution
        # We need to use the REST API or run this in Supabase SQL Editor
        
        print("\n⚠️ IMPORTANT:")
        print("Supabase Python client doesn't support raw SQL execution.")
        print("\nPlease run the following SQL in Supabase Dashboard:")
        print("1. Go to: https://supabase.com/dashboard → SQL Editor")
        print("2. Create a new query")
        print("3. Paste the following SQL:\n")
        print("-" * 60)
        print(sql)
        print("-" * 60)
        
        print("\n✅ After running the SQL, the system will work with persistent memory!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
