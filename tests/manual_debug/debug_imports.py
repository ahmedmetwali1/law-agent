
import sys

print(f"Python: {sys.version}")

try:
    import psycopg_pool
    print("✅ psycopg_pool imported")
except ImportError as e:
    print(f"❌ psycopg_pool FAILED: {e}")

try:
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    print("✅ AsyncPostgresSaver imported (langgraph.checkpoint.postgres.aio)")
except ImportError as e:
    print(f"❌ AsyncPostgresSaver (aio) FAILED: {e}")
    # Try alternative path
    try:
        from langgraph.checkpoint.postgres import AsyncPostgresSaver
        print("✅ AsyncPostgresSaver imported (langgraph.checkpoint.postgres)")
    except ImportError as e2:
        print(f"❌ AsyncPostgresSaver (root) FAILED: {e2}")

try:
    import langgraph
    print(f"LangGraph version: {langgraph.__version__}")
except:
    print("LangGraph version unknown")
