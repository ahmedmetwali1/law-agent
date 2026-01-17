"""
Smart Tool Executor for Professional Assistant
منفذ الأدوات الذكي للمساعد الاحترافي

This module handles intelligent tool execution with:
- Automatic tool detection from user query
- Multi-step execution
- Fallback mechanisms
- Result formatting
"""

from typing import Dict, Any, List, Optional
import logging
import re
import json

logger = logging.getLogger(__name__)


class SmartToolExecutor:
    """
    Intelligent tool execution engine
    محرك تنفيذ الأدوات الذكي
    """
    
    def __init__(self, unified_tools):
        """
        Initialize with unified tool system
        
        Args:
            unified_tools: UnifiedToolSystem instance
        """
        self.tools = unified_tools
        self.execution_history = []
        logger.info("🤖 Smart Tool Executor initialized")
    
    def detect_and_execute(self, user_query: str, chat_history: List[Dict] = None) -> Dict[str, Any]:
        """
        Detect intent and execute appropriate tools
        
        Args:
            user_query: User's message
            chat_history: Previous conversation
        
        Returns:
            Execution result with formatted response
        """
        query_lower = user_query.lower()
        
        # Pattern matching for common queries
        executed_tools = []
        results = {}
        
        # 1. Today's hearings
        if any(keyword in query_lower for keyword in ["جلسات اليوم", "جلساتي اليوم", "مواعيد اليوم", "today", "هل لدي جلسات"]):
            logger.info("🎯 Detected: Today's hearings query")
            result = self.tools.execute_tool("get_today_hearings")
            executed_tools.append("get_today_hearings")
            results["hearings_today"] = result
        
        # 2. Upcoming hearings
        elif any(keyword in query_lower for keyword in ["جلسات قادمة", "جلسات الأسبوع", "upcoming"]):
            logger.info("🎯 Detected: Upcoming hearings query")
            result = self.tools.execute_tool("get_upcoming_hearings", days=7)
            executed_tools.append("get_upcoming_hearings")
            results["hearings_upcoming"] = result
        
        # 3. List all clients
        elif any(keyword in query_lower for keyword in ["موكليني", "الموكلين", "عدد الموكلين", "كم موكل", "my clients", "list clients"]):
            logger.info("🎯 Detected: List clients query")
            result = self.tools.execute_tool("list_all_clients")
            executed_tools.append("list_all_clients")
            results["clients"] = result
        
        # 4. Search clients
        elif any(keyword in query_lower for keyword in ["ابحث عن موكل", "موكل اسمه", "client named"]):
            # Extract search term
            search_term = self._extract_search_term(user_query)
            if search_term:
                logger.info(f"🎯 Detected: Search clients for '{search_term}'")
                result = self.tools.execute_tool("search_clients", query=search_term)
                executed_tools.append("search_clients")
                results["search_results"] = result
        
        # 5. Active cases
        elif any(keyword in query_lower for keyword in ["قضايا نشطة", "القضايا النشطة", "active cases"]):
            logger.info("🎯 Detected: Active cases query")
            result = self.tools.execute_tool("list_active_cases")
            executed_tools.append("list_active_cases")
            results["active_cases"] = result
        
        # 6. Search cases
        elif any(keyword in query_lower for keyword in ["ابحث عن قضية", "قضايا محكمة", "قضايا في"]):
            search_term = self._extract_search_term(user_query)
            if search_term:
                logger.info(f"🎯 Detected: Search cases for '{search_term}'")
                result = self.tools.execute_tool("search_cases", query=search_term)
                executed_tools.append("search_cases")
                results["search_results"] = result
        
        # 7. My profile
        elif any(keyword in query_lower for keyword in ["بياناتي", "معلوماتي", "my profile", "ملفي"]):
            logger.info("🎯 Detected: Profile query")
            result = self.tools.execute_tool("get_my_profile")
            executed_tools.append("get_my_profile")
            results["profile"] = result
        
        # 8. Legal knowledge search (fallback)
        elif "?" in user_query or any(keyword in query_lower for keyword in ["ما هو", "ما هي", "كيف", "متى", "لماذا", "what", "how"]):
            logger.info("🎯 Detected: Knowledge question")
            result = self.tools.execute_tool("search_knowledge", query=user_query, max_results=3)
            executed_tools.append("search_knowledge")
            results["knowledge"] = result
        
        # Log execution
        if executed_tools:
            self.execution_history.append({
                "query": user_query,
                "tools_used": executed_tools,
                "success": all(r.get("success", False) for r in results.values())
            })
            logger.info(f"✅ Executed {len(executed_tools)} tool(s): {executed_tools}")
        
        return {
            "tools_executed": executed_tools,
            "results": results,
            "formatted_response": self._format_results(results, user_query) if results else None
        }
    
    def _extract_search_term(self, query: str) -> Optional[str]:
        """Extract search term from query"""
        # Simple extraction - looks for quoted text or after keywords
        patterns = [
            r'"([^"]+)"',  # Quoted text
            r'اسمه ([^\s]+)',  # "اسمه X"
            r'عن ([^\s]+)',  # "عن X"
            r'في ([^\s]+)',  # "في X"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                return match.group(1)
        
        # Fallback: last word
        words = query.split()
        if len(words) > 2:
            return words[-1]
        
        return None
    
    def _format_results(self, results: Dict[str, Any], original_query: str) -> str:
        """
        Format tool results into user-friendly response
        
        Args:
            results: Dict of tool results
            original_query: Original user query
        
        Returns:
            Formatted markdown response
        """
        response_parts = []
        
        for tool_type, result in results.items():
            if not result.get("success"):
                continue
            
            if tool_type == "hearings_today":
                response_parts.append(self._format_hearings(result, "اليوم"))
            elif tool_type == "hearings_upcoming":
                response_parts.append(self._format_hearings(result, "القادمة"))
            elif tool_type == "clients":
                response_parts.append(self._format_clients(result))
            elif tool_type == "active_cases":
                response_parts.append(self._format_cases(result))
            elif tool_type == "search_results":
                response_parts.append(self._format_search_results(result))
            elif tool_type == "profile":
                response_parts.append(self._format_profile(result))
            elif tool_type == "knowledge":
                response_parts.append(self._format_knowledge(result))
        
        return "\n\n".join(response_parts) if response_parts else "لم أتمكن من العثور على نتائج."
    
    def _format_hearings(self, result: Dict, timeframe: str) -> str:
        """Format hearings result"""
        hearings = result.get("hearings", [])
        count = len(hearings)
        
        if count == 0:
            return f"📅 **ليس لديك جلسات {timeframe}** - استمتع بوقتك! 🎉"
        
        lines = [f"📅 **جلساتك {timeframe}** ({count} جلسة):\n"]
        
        for i, h in enumerate(hearings, 1):
            time = h.get("hearing_time", "غير محدد")
            case = h.get("case_number", "غير محدد")
            client = h.get("client_name", "غير محدد")
            court = h.get("court_name", "غير محددة")
            room = h.get("court_room", "؟")
            
            lines.append(f"{i}. ⏰ **{time}** - قضية {case}")
            lines.append(f"   👤 موكل: {client} | 🏛️ {court} | 🚪 قاعة {room}")
        
        return "\n".join(lines)
    
    def _format_clients(self, result: Dict) -> str:
        """Format clients list"""
        clients = result.get("clients", [])
        count = len(clients)
        
        if count == 0:
            return "👥 **لا توجد موكلين حالياً**"
        
        lines = [f"👥 **موكليك** ({count} موكل):\n"]
        
        for i, c in enumerate(clients[:10], 1):  # Show first 10
            name = c.get("full_name", "غير محدد")
            phone = c.get("phone", "")
            poa = " ✅ وكالة" if c.get("has_power_of_attorney") else ""
            
            lines.append(f"{i}. **{name}**{poa}")
            if phone:
                lines.append(f"   📞 {phone}")
        
        if count > 10:
            lines.append(f"\n... و{count - 10} موكل آخرين")
        
        return "\n".join(lines)
    
    def _format_cases(self, result: Dict) -> str:
        """Format cases list"""
        cases = result.get("cases", [])
        count = len(cases)
        
        if count == 0:
            return "⚖️ **لا توجد قضايا نشطة حالياً**"
        
        lines = [f"⚖️ **القضايا النشطة** ({count} قضية):\n"]
        
        for i, c in enumerate(cases[:5], 1):
            number = c.get("case_number", "غير محدد")
            court = c.get("court_name", "غير محددة")
            ctype = c.get("case_type", "")
            
            lines.append(f"{i}. **{number}** - {court}")
            if ctype:
                lines.append(f"   النوع: {ctype}")
        
        if count > 5:
            lines.append(f"\n... و{count - 5} قضية أخرى")
        
        return "\n".join(lines)
    
    def _format_search_results(self, result: Dict) -> str:
        """Format search results"""
        items = result.get("clients") or result.get("cases") or []
        count = len(items)
        
        if count == 0:
            return "🔍 **لم أجد نتائج مطابقة**"
        
        return f"🔍 **وجدت {count} نتيجة** - استخدم الأداة لعرض التفاصيل"
    
    def _format_profile(self, result: Dict) -> str:
        """Format profile info"""
        profile = result.get("profile", {})
        name = profile.get("full_name", "المحامي")
        email = profile.get("email", "")
        phone = profile.get("phone", "")
        
        lines = [f"👤 **ملفك الشخصي**\n"]
        lines.append(f"الاسم: {name}")
        if email:
            lines.append(f"البريد: {email}")
        if phone:
            lines.append(f"الهاتف: {phone}")
        
        return "\n".join(lines)
    
    def _format_knowledge(self, result: Dict) -> str:
        """Format knowledge search results"""
        results = result.get("results", [])
        count = len(results)
        
        if count == 0:
            return "🔍 **لم أجد معلومات قانونية ذات صلة**"
        
        lines = [f"📚 **نتائج البحث القانوني** ({count} نتيجة):\n"]
        
        for i, r in enumerate(results, 1):
            content = r.get("content", "")[:200]  # First 200 chars
            lines.append(f"{i}. {content}...")
        
        return "\n".join(lines)


__all__ = ["SmartToolExecutor"]
