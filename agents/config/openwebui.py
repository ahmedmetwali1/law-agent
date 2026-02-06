"""
Open WebUI Client with Multi-Model Rotation
Unified interface for connecting to Open WebUI API with fallback/rotation support.
"""

from openai import OpenAI
from typing import List, Dict, Any, Optional
from agents.config.settings import settings
from langchain_openai import ChatOpenAI
import logging
import itertools

logger = logging.getLogger(__name__)


class OpenWebUIClient:
    """Client for interacting with Open WebUI API with Round-Robin model rotation"""
    
    def __init__(self):
        """Initialize Open WebUI client"""
        # Parse models list from settings
        models_str = settings.openwebui_models or settings.openwebui_model
        self.models_list = [m.strip() for m in models_str.split(",") if m.strip()]
        
        # Iterator for round-robin rotation
        self._model_cycler = itertools.cycle(self.models_list)
        
        self.client = OpenAI(
            base_url=settings.openwebui_api_url,
            api_key=settings.openwebui_api_key or "not-needed"
        )
        
        logger.info(f"Initialized Open WebUI with models: {self.models_list}")
    
    @property
    def current_model(self) -> str:
        """Get the next model in the rotation"""
        return next(self._model_cycler)

    def get_langchain_client(self, temperature: float = 0.7, json_mode: bool = False, streaming: bool = False, model_name: Optional[str] = None) -> ChatOpenAI:
        """
        Returns a LangChain ChatOpenAI instance with the currently rotated model (or specific model).
        """
        model = model_name if model_name else self.current_model
        logger.info(f"LangChain Request using model: {model} (streaming={streaming})")
        
        kwargs = {"temperature": temperature}
        if json_mode:
            kwargs["model_kwargs"] = {"response_format": {"type": "json_object"}}
            
        # Handle /v1 suffix for OpenAI client compatibility
        base_url = settings.openwebui_api_url
        if not base_url.endswith("/v1") and not base_url.endswith("/v1/"):
             base_url = f"{base_url}/v1"

        return ChatOpenAI(
            model=model,
            api_key=settings.openwebui_api_key if settings.openwebui_api_key else "sk-no-key-required",
            base_url=base_url,
            streaming=streaming,
            max_retries=1,
            **kwargs
        )
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None
    ) -> Any:
        """Generate chat completion using raw OpenAI-compatible client (with rotation)"""
        try:
            model = self.current_model
            logger.info(f"Raw Request using model: {model}")
            
            params = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": stream
            }
            
            if tools:
                params["tools"] = tools
            if tool_choice:
                params["tool_choice"] = tool_choice
            
            response = self.client.chat.completions.create(**params)
            
            if stream:
                full_response = ""
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        full_response += chunk.choices[0].delta.content
                return full_response
            else:
                if tools:
                    return response.choices[0].message
                return response.choices[0].message.content
                
        except Exception as e:
            logger.error(f"Error in Open WebUI rotation completion: {e}")
            raise
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding - uses the specific embedding model from settings"""
        try:
            response = self.client.embeddings.create(
                model=settings.openwebui_embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Embedding failure: {e}")
            raise

# Global client instance
openwebui_client = OpenWebUIClient()

def get_langchain_llm(temperature: float = 0.7, json_mode: bool = False, streaming: bool = False, model_name: Optional[str] = None) -> ChatOpenAI:
    """Factory for LangChain nodes"""
    return openwebui_client.get_langchain_client(temperature, json_mode, streaming, model_name)
