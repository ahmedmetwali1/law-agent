"""
Professional Tool System for Personal Assistant Agent
نظام الأدوات الاحترافي للمساعد الشخصي

This module provides a unified interface for all agent tools with:
- Automatic tool detection and registration
- Function calling support
- Fallback mechanisms
- Error handling and retry logic
"""

from typing import Dict, Any, List, Optional, Callable
import logging
import json
from functools import wraps
from agents.storage.task_storage import task_storage

logger = logging.getLogger(__name__)


def resilient_tool(max_retries: int = 2):
    """
    Decorator to make tools resilient with automatic retry
    محاولة تلقائية عند الفشل
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries:
                        logger.warning(f"⚠️ Tool {func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): {e}")
                    else:
                        logger.error(f"❌ Tool {func.__name__} failed after {max_retries + 1} attempts: {e}")
            
            # Return error response
            return {
                "success": False,
                "error": str(last_error),
                "message": f"فشل في تنفيذ الأداة بعد {max_retries + 1} محاولات"
            }
        return wrapper
    return decorator


class UnifiedToolSystem:
    """
    Unified tool management system
    نظام موحد لإدارة جميع الأدوات
    """
    
    def __init__(self, lawyer_id: str, lawyer_name: str, current_user: Optional[Dict[str, Any]] = None):
        """
        Initialize with lawyer context
        
        Args:
            lawyer_id: Lawyer's user ID
            lawyer_name: Lawyer's full name
            current_user: Context of the current user (for audit logging)
        """
        self.lawyer_id = lawyer_id
        self.lawyer_name = lawyer_name
        self.current_user = current_user
        
        # ✨ NEW: Dynamic database tool generator
        self.db_generator = None
        
        # Tool instances (legacy)
        # Specialized tools
        self.deep_thinking_tool = None
        
        # Tool registry
        self.tools_registry: Dict[str, Callable] = {}
        
        logger.info(f"🔧 Initializing Unified Tool System for {lawyer_name}...")
        self._initialize_all_tools()
    
    def _initialize_all_tools(self):
        """Initialize all available tools"""
        try:
            # ✨ NEW: Initialize dynamic DB tool generator FIRST
            from agents.tools.db_tool_factory import DatabaseToolGenerator
            
            logger.info("🚀 Initializing Dynamic Database Tool Generator...")
            self.db_generator = DatabaseToolGenerator(
                lawyer_id=self.lawyer_id,
                current_user=self.current_user
            )
            
            # Register dynamic tools
            self._register_dynamic_db_tools()
            
            # Legacy tools (for backward compatibility)
            try:
                from agents.tools.deep_thinking import EnhancedDeepThinkingTool
                from agents.knowledge.hybrid_search import search
                
                # Initialize specialized tools
                self.deep_thinking_tool = EnhancedDeepThinkingTool()
                
                # Register specialized tools
                self._register_search_tools()
                self._register_thinking_tools()
                
                logger.info(f"✅ Specialized tools (Search, Thinking) loaded")
            except Exception as specialized_error:
                logger.warning(f"⚠️ Some specialized tools failed to load: {specialized_error}")
            
            logger.info("✅ System configured to use Dynamic Tools primarily")
            
            logger.info(f"✅ Total registered tools: {len(self.tools_registry)}")
            logger.info(f"   - Dynamic DB tools: {len(self.db_generator.get_all_tools())}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize tools: {e}")
            raise
    
    def _register_dynamic_db_tools(self):
        """✨ Register dynamically generated database tools"""
        if not self.db_generator:
            logger.warning("⚠️ DB generator not initialized")
            return
        
        dynamic_tools = self.db_generator.get_all_tools()
        
        for tool_name, tool_func in dynamic_tools.items():
            # Wrap with resilient_tool for error handling
            self.tools_registry[tool_name] = resilient_tool()(tool_func)
        
        logger.info(f"✅ Registered {len(dynamic_tools)} dynamic DB tools")

        # ---------------------------------------------------------------------
        # OVERRIDE: Register Task Tools manually to ensure Local Persistence
        # ---------------------------------------------------------------------
        self.tools_registry["insert_tasks"] = resilient_tool()(lambda **kwargs: {
            "success": True, 
            "data": task_storage.save_task(kwargs),
            "message": "تم إضافة المهمة بنجاح"
        })
        
        self.tools_registry["query_tasks"] = resilient_tool()(lambda **kwargs: {
            "success": True,
            "data": task_storage.list_tasks(lawyer_id=kwargs.get("lawyer_id")),
            "message": "تم استرجاع المهام"
        })
        
        self.tools_registry["delete_tasks"] = resilient_tool()(lambda **kwargs: {
            "success": task_storage.delete_task(kwargs.get("record_id") or kwargs.get("id")),
            "message": "تم حذف المهمة" if task_storage.delete_task(kwargs.get("record_id") or kwargs.get("id")) else "فشل الحذف"
        })

        self.tools_registry["update_tasks"] = resilient_tool()(lambda **kwargs: {
            "success": True,
            "data": task_storage.save_task(kwargs.get("updates", kwargs), task_id=kwargs.get("record_id") or kwargs.get("id")),
            "message": "تم تحديث المهمة"
        })
        logger.info("✅ Registered Local TaskStorage tools (Overriding dynamic tools)")

    

    
    def _register_search_tools(self):
        """Register search-related tools"""
        from agents.knowledge.hybrid_search import search
        
        self.tools_registry["search_legal_db"] = search
        self.tools_registry["search_internet"] = lambda query: {"result": "Feature coming soon"}
    
    def get_tools_for_llm(self) -> List[Dict[str, Any]]:
        """
        Get tools in OpenAI function calling format
        للاستخدام مع LLM function calling
        
        ✨ NEW: Prioritizes dynamic DB tools, falls back to legacy
        
        Returns:
            List of tool definitions
        """
        tools = []
        
        # ✨ PRIORITY 1: Dynamic DB tools (auto-generated from schema)
        if self.db_generator:
            dynamic_tools = self.db_generator.get_tools_for_llm()
            tools.extend(dynamic_tools)
            logger.debug(f"📊 Added {len(dynamic_tools)} dynamic DB tools")
        

        
        # Search tool
        tools.append({
            "type": "function",
            "function": {
                "name": "search_knowledge",
                "description": "البحث في قاعدة المعرفة القانونية السعودية (الأنظمة، القوانين، السوابق القضائية)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "استعلام البحث"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "عدد النتائج المطلوبة (افتراضي: 5)",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            }
        })
        

        
        logger.info(f"✅ Total tools for LLM: {len(tools)}")
        return tools
    
    def _convert_to_function_format(self, tool: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert tool definition to OpenAI function format
        """
        # Extract parameters from description (simplified)
        return {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": {
                    "type": "object",
                    "properties": {},  # TODO: Parse from description
                    "required": []
                }
            }
        }
    
    def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a tool by name
        
        ✨ NEW: Tries dynamic DB tools first, then falls back to legacy
        
        Args:
            tool_name: Name of the tool
            **kwargs: Tool arguments
        
        Returns:
            Tool execution result
        """
        # ✨ STRATEGY: Try dynamic tools directly first (faster)
        if self.db_generator and self.db_generator.get_tool(tool_name):
            try:
                logger.info(f"🚀 Executing dynamic tool: {tool_name}")
                result = self.db_generator.execute_tool(tool_name, **kwargs)
                
                if result.get("success"):
                    logger.info(f"✅ Dynamic tool {tool_name} succeeded")
                    return result
                else:
                    logger.warning(f"⚠️ Dynamic tool {tool_name} returned failure")
                    # Continue to registry fallback
            except Exception as e:
                logger.warning(f"⚠️ Dynamic tool {tool_name} raised exception: {e}")
                # Continue to registry fallback
        
        # Fallback: Try from registry (legacy tools)
        if tool_name not in self.tools_registry:
            logger.error(f"❌ Tool not found: {tool_name}")
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found",
                "message": f"الأداة '{tool_name}' غير موجودة"
            }
        
        try:
            logger.info(f"🔧 Executing tool from registry: {tool_name}")
            result = self.tools_registry[tool_name](**kwargs)
            logger.info(f"✅ Tool {tool_name} executed successfully")
            return result
        except Exception as e:
            logger.error(f"❌ Tool {tool_name} execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"فشل تنفيذ الأداة: {str(e)}"
            }
    
    def get_available_tools_list(self) -> List[str]:
        """Get list of all available tool names"""
        return list(self.tools_registry.keys())
    
    def tool_exists(self, tool_name: str) -> bool:
        """Check if a tool exists"""
        return tool_name in self.tools_registry
    
    def get_openai_tools(self) -> List[Dict[str, Any]]:
        """Alias for get_tools_for_llm - for compatibility"""
        return self.get_tools_for_llm()

    def _register_thinking_tools(self):
        """Register thinking tools"""
        if hasattr(self, 'deep_thinking_tool'):
            self.tools_registry["deep_think"] = self.deep_thinking_tool.run


__all__ = ["UnifiedToolSystem", "resilient_tool"]
