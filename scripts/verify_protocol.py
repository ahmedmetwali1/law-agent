import asyncio
import aiohttp
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Test Configuration
API_URL = "http://localhost:8000/api/chat/stream"
TEST_SESSION_ID = "test-session-verification-viva"
TEST_MESSAGE = "Hello, this is a protocol verification test."

async def test_sse_stream():
    """
    Connects to the stream endpoint and verifies the SSE protocol strictness:
    1. Events start with `data: `
    2. Events end with `\n\n`
    3. JSON content is valid
    4. No leaked internal keys in `token` content.
    """
    logger.info(f"🚀 Starting Protocol Verification on {API_URL}...")
    
    # Needs Auth Token usually, but for local dev maybe disabled? 
    # If auth is required, this script might fail 401. 
    # Let's assume we need a token. I'll print a warning if 401.
    
    headers = {
        "Content-Type": "application/json",
        # "Authorization": "Bearer YOUR_TOKEN_HERE" # User might need to provide this if strict auth is on.
    }

    payload = {
        "session_id": TEST_SESSION_ID,
        "message": TEST_MESSAGE,
        "mode": "auto"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, json=payload, headers=headers) as response:
                if response.status == 401:
                    logger.error("❌ Authentication Failed (401). Please disable auth for test or provide token.")
                    return
                
                if response.status != 200:
                    logger.error(f"❌ Server Error: {response.status}")
                    text = await response.text()
                    logger.error(f"Response: {text}")
                    return

                logger.info("✅ Connection Established. Reading Stream...")
                
                buffer = ""
                async for chunk, _ in response.content.iter_chunks():
                    decoded_chunk = chunk.decode('utf-8')
                    buffer += decoded_chunk
                    
                    # Split by double newline
                    while "\n\n" in buffer:
                        event_str, buffer = buffer.split("\n\n", 1)
                        await validate_event(event_str)

    except Exception as e:
        logger.error(f"❌ Connection Error: {e}")

async def validate_event(event_str):
    if not event_str.startswith("data: "):
        logger.warning(f"⚠️ Invalid Prefix: {event_str[:20]}...")
        return

    json_str = event_str.replace("data: ", "").strip()
    
    if json_str == "[DONE]":
        logger.info("✅ Stream Completed Successfully [DONE]")
        return

    try:
        data = json.loads(json_str)
        event_type = data.get("type")
        
        # Validation Rules
        if not event_type:
            logger.error("❌ Event Type Missing")
            return

        if event_type == "token":
            content = data.get("content", "")
            if "action" in content and ("{" in content or '"' in content):
                 logger.error(f"🚨 POTENTIAL LEAK DETECTED in Token: {content}")
            else:
                 logger.info(f"🔹 Token: {content[:30]}...")
                 
        elif event_type == "reasoning_chunk":
            logger.info(f"🧠 Reasoning: {data.get('content')[:30]}...")
            
        elif event_type == "step_update":
            payload = data.get("payload", {})
            logger.info(f"🔄 Step: {payload.get('message') or payload}")

        elif event_type == "error":
             logger.error(f"❌ Stream Error Event: {data.get('content')}")

    except json.JSONDecodeError:
        logger.error(f"❌ Malformed JSON: {json_str}")

if __name__ == "__main__":
    # Create an event loop to run the async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(test_sse_stream())
