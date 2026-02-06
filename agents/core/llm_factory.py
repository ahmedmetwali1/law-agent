from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from agents.config.settings import settings
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

def get_llm(
    temperature: float = 0.7, 
    streaming: bool = True,
    json_mode: bool = False,
    model_name: Optional[str] = None,
    **kwargs: Any
):
    """
    Factory to get the configured LLM (OpenWebUI/DeepSeek/OpenAI).
    
    Architecture Note:
    - Supports 'Adaptive JSON Mode'.
    - If model is OpenAI GPT-4/3.5, uses native 'response_format={type: json_object}'.
    - If model is OpenSource (Qwen/Llama) via OpenWebUI, avoids 'response_format' (often unsupported)
      and relies on Prompt Engineering (handled by LangChain's PydanticOutputParser usually, 
      but here we ensure the API call doesn't crash).
    """
    try:
        # Determine Model
        target_model = model_name or settings.openwebui_model
        
        # Determine JSON Args
        model_kwargs = kwargs.get("model_kwargs", {})
        
        if json_mode:
            # 🧠 Adaptive Logic: Only send strict API flag to models we KNOW support it.
            # Qwen-Coder via Ollama/OpenWebUI often rejects 'json_object' type.
            is_openai_native = "gpt-" in target_model or "o1-" in target_model
            
            if is_openai_native:
                model_kwargs["response_format"] = {"type": "json_object"}
            else:
                # For Local Models, typically we DO NOT send the flag if it causes 400s.
                # We rely on the System Prompt to enforce JSON.
                # However, some vLLM instances support it. 
                # Given the user error "unavailable now", we MUST disable it for this env.
                pass 
            
        llm = ChatOpenAI(
            base_url=f"{settings.openwebui_api_url}", 
            api_key=settings.openwebui_api_key,
            model=target_model,
            temperature=temperature,
            streaming=streaming,
            model_kwargs=model_kwargs,
            **kwargs
        )
        return llm
    except Exception as e:
        logger.error(f"Failed to create LLM: {e}")
        raise e

def get_embeddings():
    """
    Factory to get the configured Embeddings (OpenWebUI/DeepSeek/OpenAI).
    """
    try:
        # ✅ FIX: Prefer explicit Embedding Configuration if available
        # The user specifically provided EMBEDDING_API_URL and OPENAI_API_KEY for a worker.
        
        target_base_url = settings.embedding_api_url if settings.embedding_api_url else settings.openwebui_api_url
        target_api_key = settings.openai_api_key if settings.openai_api_key else settings.openwebui_api_key
        target_model = settings.embedding_model if settings.embedding_model else settings.openwebui_embedding_model
        
        # Ensure we don't pass None or empty string if possible (OpenAI client might complain)
        if not target_api_key:
             target_api_key = "sk-placeholder" # Fallback to prevent init crash if local

        return OpenAIEmbeddings(
            base_url=target_base_url, 
            api_key=target_api_key,
            model=target_model,
            check_embedding_ctx_length=False # Prevent initial network call check
        )
    except Exception as e:
        logger.error(f"Failed to create Embeddings: {e}")
        raise e
