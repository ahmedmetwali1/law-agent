
import asyncio
import json
from pydantic import BaseModel
from typing import List
from unittest.mock import AsyncMock, MagicMock
from langchain_core.messages import BaseMessage, AIMessage

# Import target function
from agents.core.graph_agent import generate_with_retry

# Mock Model
class MockModel(BaseModel):
    name: str
    age: int

# Mock LLM
class MockLLM:
    def __init__(self):
        self.attempts = 0
        
    async def ainvoke(self, messages):
        self.attempts += 1
        if self.attempts == 1:
            return AIMessage(content='{"name": "test", "age": "invalid"}') # Invalid type
        elif self.attempts == 2:
            return AIMessage(content='Broken JSON') # Invalid JSON
        else:
            return AIMessage(content='{"name": "success", "age": 25}') # Success

async def test_retry_logic():
    print("🧪 Testing Self-Healing Schema Adapter...")
    llm = MockLLM()
    
    try:
        result = await generate_with_retry(
            llm, 
            [], 
            MockModel, 
            max_retries=3
        )
        print(f"✅ Success! Encoded result: {result}")
        print(f"🔄 Total attempts: {llm.attempts} (Expected 3)")
        
        if llm.attempts == 3 and result.age == 25:
            print("🎉 Test PASSED: Adapted after 2 failures.")
        else:
            print("❌ Test FAILED: Logic did not retry correctly.")
            
    except Exception as e:
        print(f"❌ Test Failed with Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_retry_logic())
