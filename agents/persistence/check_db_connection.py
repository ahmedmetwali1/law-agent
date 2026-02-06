"""
Database Connection Health Check
فحص صحة الاتصال بقاعدة البيانات
"""
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.persistence.postgres_persistence import persistence

async def check_connection():
    """التحقق من صحة الاتصال"""
    print("=" * 60)
    print("🔍 Database Connection Health Check")
    print("=" * 60)
    
    try:
        persistence.initialize()
        
        if persistence.is_postgres_available:
            print("✅ Postgres Connection: HEALTHY")
            # Extract and display connection info (hide password)
            db_url = persistence.db_url
            if '@' in db_url:
                parts = db_url.split('@')
                host_info = parts[1].split('/')[0]
                print(f"   Target: {host_info}")
            
            # Test pool operations
            if persistence._pool:
                print("\n🔧 Testing pool operations...")
                try:
                    await persistence._pool.open()
                    print("   ✅ Pool opened successfully")
                    
                    # Get connection stats
                    print(f"   📊 Pool size: {persistence._pool.max_size}")
                    print(f"   📊 Min connections: {persistence._pool.min_size}")
                    
                    await persistence._pool.close()
                    print("   ✅ Pool closed successfully")
                except Exception as e:
                    print(f"   ❌ Pool operation failed: {e}")
                    return False
            
            print("\n✅ All checks passed!")
            print("   System is ready for persistent conversations.")
            return True
            
        else:
            print("⚠️ Using In-Memory Fallback (MemorySaver)")
            print("   Conversations will NOT persist across restarts")
            print("\n📝 Action Required:")
            print("   1. Add DATABASE_URL to .env file")
            print("   2. Restart the server")
            return False
        
    except Exception as e:
        print(f"❌ Connection Check Failed: {e}")
        print("\n📝 Troubleshooting:")
        print("   1. Verify DATABASE_URL in .env")
        print("   2. Check network connectivity")
        print("   3. Verify database credentials")
        return False
    finally:
        print("=" * 60)

if __name__ == "__main__":
    result = asyncio.run(check_connection())
    sys.exit(0 if result else 1)
