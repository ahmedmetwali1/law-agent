import logging
import asyncio
import json
from typing import Callable, Any, Dict, Optional, List
from langchain_core.messages import BaseMessage

logger = logging.getLogger(__name__)

class FailoverError(Exception):
    """Exception raised when all retries fail."""
    def __init__(self, message, reason=None):
        super().__init__(message)
        self.reason = reason

class ResiliencyManager:
    """
    Manages execution loops, retries, and error handling for LLM tasks.
    """
    
    @staticmethod
    def classify_error(error: Exception) -> str:
        msg = str(error).lower()
        if "context_length_exceeded" in msg or "maximum context length" in msg:
            return "context_overflow"
        if "rate limit" in msg or "429" in msg:
            return "rate_limit"
        if "json" in msg or "parse" in msg:
            return "parser_error"
        if "timeout" in msg:
            return "timeout"
        return "unknown"

    @staticmethod
    async def run_with_retries(
        func: Callable[[], Any],
        max_attempts: int = 3,
        on_error: Optional[Callable[[Exception, int], Any]] = None
    ) -> Any:
        """
        Executes an async function with robust retry logic.
        
        Args:
            func: The async function to execute (e.g. LLM invoke).
            max_attempts: Max retry attempts.
            on_error: Callback to handle/log errors or Adjust context before next retry.
                      Should return True to continue retry, False to stop.
        """
        last_error = None
        
        for attempt in range(1, max_attempts + 1):
            try:
                return await func()
            except Exception as e:
                last_error = e
                error_type = ResiliencyManager.classify_error(e)
                logger.warning(f"⚠️ Attempt {attempt}/{max_attempts} failed: {error_type} - {str(e)}")
                
                if attempt == max_attempts:
                    break
                
                # Custom Handler (e.g. Compaction)
                if on_error:
                    should_continue = await on_error(e, attempt)
                    if not should_continue:
                        break
                
                # Backoff
                if error_type == "rate_limit":
                    await asyncio.sleep(2 * attempt)
                else:
                    await asyncio.sleep(0.5)
                    
        raise FailoverError(f"Operation failed after {max_attempts} attempts. Last error: {last_error}", reason="max_retries")

    @staticmethod
    def parse_json_safely(text: str) -> Dict:
        """
        Tries to parse JSON even if it has markdown blocks.
        """
        text = text.strip()
        # Remove markdown code blocks if present
        if text.startswith("```"):
            lines = text.split("\n")
            if len(lines) >= 2:
                # Remove first and last line assume ```json ... ```
                text = "\n".join(lines[1:-1])
        
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Fallback: aggressive search for { ... }
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                try:
                    return json.loads(text[start:end+1])
                except:
                    pass
            raise
