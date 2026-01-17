"""
Open WebUI Client
Unified interface for connecting to Open WebUI API
"""

from openai import OpenAI
from typing import List, Dict, Any, Optional
from agents.config.settings import settings
import logging

logger = logging.getLogger(__name__)


class OpenWebUIClient:
    """Client for interacting with Open WebUI API"""
    
    def __init__(self):
        """Initialize Open WebUI client"""
        self.client = OpenAI(
            base_url=settings.openwebui_api_url,
            api_key=settings.openwebui_api_key or "not-needed"  # Some Open WebUI instances don't need API key
        )
        self.model = settings.openwebui_model
        logger.info(f"Initialized Open WebUI client with model: {self.model}")
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None
    ) -> Any:
        """
        Generate chat completion using Open WebUI
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            tools: Optional list of tools for function calling
            tool_choice: Optional tool choice ('auto', 'none', or specific tool)
            
        Returns:
            Generated text response or full response object (if tools used)
        """
        try:
            # Build request parameters
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": stream
            }
            
            # Add tools if provided
            if tools:
                params["tools"] = tools
            if tool_choice:
                params["tool_choice"] = tool_choice
            
            response = self.client.chat.completions.create(**params)
            
            if stream:
                # Handle streaming response
                full_response = ""
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        full_response += chunk.choices[0].delta.content
                return full_response
            else:
                # If tools were provided, return full response (may include tool_calls)
                if tools:
                    return response.choices[0].message
                # Otherwise, just return content
                return response.choices[0].message.content
                
        except Exception as e:
            logger.error(f"Error in Open WebUI chat completion: {e}")
            raise
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using Open WebUI
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector
        """
        try:
            # Use Open WebUI embedding model
            response = self.client.embeddings.create(
                model=settings.openwebui_embedding_model,
                input=text
            )
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding with Open WebUI: {e}")
            # Fallback to OpenAI if available
            if settings.embedding_provider == "openai" and settings.openai_api_key:
                logger.info("Falling back to OpenAI for embeddings")
                from openai import OpenAI as OpenAIClient
                openai_client = OpenAIClient(api_key=settings.openai_api_key)
                response = openai_client.embeddings.create(
                    model=settings.embedding_model,
                    input=text
                )
                return response.data[0].embedding
            raise
    
    def list_models(self) -> List[str]:
        """
        List available models in Open WebUI
        
        Returns:
            List of model names
        """
        try:
            models = self.client.models.list()
            return [model.id for model in models.data]
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []
    
    def get_model_info(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get information about a specific model
        
        Args:
            model_name: Model name (defaults to current model)
            
        Returns:
            Model information dict
        """
        model = model_name or self.model
        try:
            model_info = self.client.models.retrieve(model)
            return {
                "id": model_info.id,
                "created": getattr(model_info, "created", None),
                "owned_by": getattr(model_info, "owned_by", "unknown")
            }
        except Exception as e:
            logger.error(f"Error getting model info: {e}")
            return {"id": model, "error": str(e)}


# Global client instance
openwebui_client = OpenWebUIClient()


def get_completion(
    prompt: str,
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2000
) -> str:
    """
    Convenience function for getting completions
    
    Args:
        prompt: User prompt
        system_prompt: Optional system prompt
        temperature: Sampling temperature
        max_tokens: Maximum tokens
        
    Returns:
        Generated response
    """
    messages = []
    
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    
    messages.append({"role": "user", "content": prompt})
    
    return openwebui_client.chat_completion(
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens
    )


def get_embedding(text: str) -> List[float]:
    """
    Convenience function for getting embeddings
    
    Args:
        text: Input text
        
    Returns:
        Embedding vector
    """
    return openwebui_client.generate_embedding(text)
