from agents.tools.lookup_tools import LookupPrincipleTool
from agents.tools.read_tool import ReadDocumentTool
from langchain_core.tools import StructuredTool

print("--- STRICTNESS VERIFICATION ---")

def check_strictness(tool_name, tool_instance):
    print(f"\nChecking {tool_name}...")
    try:
        lc_tool = tool_instance.to_langchain_tool()
        print(f"  Type: {type(lc_tool)}")
        
        # Check args_schema
        if lc_tool.args_schema:
            print(f"  Schema: {lc_tool.args_schema.__name__}")
            # Check if strict is True? 
            # Note: StructuredTool might store strictness in private attributes or just use it during binding.
            # But we can verify if the method override was called by printing something inside, 
            # or just trusting the source code if we see the method.
            
            # Let's inspect the object properties
            print(f"  Description: {lc_tool.description[:50]}...")
            
        else:
            print("  ❌ Schema: None")
            
    except Exception as e:
        print(f"  ❌ Error converting: {e}")

lookup = LookupPrincipleTool()
check_strictness("LookupPrincipleTool", lookup)

read = ReadDocumentTool()
check_strictness("ReadDocumentTool", read)

print("\n--- CODE INSPECTION ---")
import inspect
print("Lookup Override Source:")
print(inspect.getsource(LookupPrincipleTool.to_langchain_tool))

print("Read Override Source:")
print(inspect.getsource(ReadDocumentTool.to_langchain_tool))
