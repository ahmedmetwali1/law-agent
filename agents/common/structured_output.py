
import json
import logging
from typing import Type, TypeVar, Optional, Any, Dict
from pydantic import BaseModel, ValidationError
import re

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

def extract_json_content(text: str) -> str:
    """
    Extract JSON content from a string, handling code blocks.
    """
    text = text.strip()
    
    # Try markdown code blocks first
    json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if json_match:
        return json_match.group(1)
        
    # Try finding the first '{' and last '}'
    start = text.find("{")
    end = text.rfind("}")
    
    if start != -1 and end != -1 and end > start:
        return text[start:end+1]
        
    return text

def parse_structured_output(response: str, model: Type[T]) -> Optional[T]:
    """
    Robustly parse LLM response into a Pydantic model.
    Encapsulates all the messy regex/json logic in one place.
    """
    cleaned_json = extract_json_content(response)
    
    try:
        # First attempt: Direct parse
        data = json.loads(cleaned_json)
        return model.model_validate(data)
    except json.JSONDecodeError as e:
        logger.warning(f"⚠️ JSON Decode Error: {e}. Content: {cleaned_json[:50]}...")
        # TODO: Implement auto-repair logic here in future (e.g., using a repair llm call)
        return None
    except ValidationError as e:
        logger.warning(f"⚠️ Pydantic Validation Error: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Structured parsing failed: {e}")
        return None

def validate_response_format(response: str, expected_schema: Dict[str, Any]) -> bool:
    """
    Simple validation without Pydantic model class
    """
    try:
        content = extract_json_content(response)
        data = json.loads(content)
        
        # Check if all required keys exist
        for key in expected_schema.keys():
            if key not in data:
                return False
        return True
    except:
        return False
