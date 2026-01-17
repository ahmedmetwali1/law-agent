"""
Intelligent Tool Selector
اختيار الأدوات الذكي باستخدام Reasoning Engine
"""

import logging
from typing import List, Dict, Any, Optional
from agents.reasoning.hybrid_reasoning import HybridReasoningEngine, ReasoningMode

logger = logging.getLogger(__name__)


class IntelligentToolSelector:
    """
    Selects tools intelligently using reasoning
    يختار الأدوات بذكاء بناءً على التفكير المنطقي
    """
    
    def __init__(self, reasoning_engine: HybridReasoningEngine = None):
        self.reasoning_engine = reasoning_engine or HybridReasoningEngine()
    
    def analyze_request(self, user_input: str, available_tools: List[str]) -> Dict[str, Any]:
        """
        Analyze user request and determine optimal tool strategy
        
        Args:
            user_input: User's request
            available_tools: List of available tool names
            
        Returns:
            Dict with:
                - strategy: 'search_first', 'create_directly', 'multi_step'
                - reasoning: Explanation
                - suggested_tools: List of tools to use
        """
        
        logger.info(f"🧠 Analyzing request with reasoning: {user_input[:50]}...")
        
        # Build reasoning prompt
        prompt = f"""
Analyze this user request and determine the best tool strategy:

Request: "{user_input}"

Available tools: {', '.join(available_tools)}

Think step by step:
1. What is the user trying to accomplish?
2. Do I need to search/check for existing data first?
3. Or can I create/modify directly?
4. What's the logical sequence of actions?

Based on this, what strategy should I use:
- 'search_first': Search before creating (e.g., "add case for client Ahmed" → search client first)
- 'create_directly': Create without searching (e.g., "add client Ahmed with phone 050..." → has all details)
- 'multi_step': Multiple operations (e.g., "add client and case")

Answer in this format:
Strategy: [search_first/create_directly/multi_step]
Reasoning: [brief explanation]
Tools: [tool1, tool2, ...]
"""
        
        # Use reasoning engine
        try:
            result = self.reasoning_engine.reason(
                query=prompt,
                mode=ReasoningMode.CHAIN_OF_THOUGHT
            )
            
            # Parse reasoning conclusion
            analysis = self._parse_reasoning_result(result.conclusion)
            
            logger.info(f"✅ Strategy: {analysis['strategy']}")
            logger.info(f"💭 Reasoning: {analysis['reasoning']}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Reasoning failed: {e}")
            # Fallback to simple heuristics
            return self._fallback_strategy(user_input, available_tools)
    
    def _parse_reasoning_result(self, conclusion: str) -> Dict[str, Any]:
        """Parse reasoning engine conclusion"""
        
        lines = conclusion.strip().split('\n')
        
        strategy = 'multi_step'  # Default
        reasoning = ''
        tools = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('Strategy:'):
                strategy = line.split(':', 1)[1].strip().lower()
            elif line.startswith('Reasoning:'):
                reasoning = line.split(':', 1)[1].strip()
            elif line.startswith('Tools:'):
                tools_str = line.split(':', 1)[1].strip()
                tools = [t.strip() for t in tools_str.replace('[', '').replace(']', '').split(',')]
        
        return {
            'strategy': strategy,
            'reasoning': reasoning,
            'suggested_tools': tools
        }
    
    def _fallback_strategy(self, user_input: str, available_tools: List[str]) -> Dict[str, Any]:
        """Fallback strategy using simple heuristics"""
        
        logger.warning("⚠️ Using fallback strategy (no reasoning)")
        
        input_lower = user_input.lower()
        
        # Check for common patterns
        if any(word in input_lower for word in ['أضف', 'ضيف', 'انشئ']):
            # Creating something
            if any(word in input_lower for word in ['للعميل', 'للموكل', 'لـ']):
                # "add case FOR client" → search client first
                return {
                    'strategy': 'search_first',
                    'reasoning': 'User wants to add to existing entity',
                    'suggested_tools': ['search_clients', 'create_case']
                }
            else:
                # "add client Ahmed 050..." → direct create
                return {
                    'strategy': 'create_directly',
                    'reasoning': 'Has complete info for creation',
                    'suggested_tools': ['create_client']
                }
        
        return {
            'strategy': 'multi_step',
            'reasoning': 'General request',
            'suggested_tools': []
        }
    
    def should_search_before_create(self, entity_type: str, user_input: str) -> bool:
        """
        Determine if we should search before creating
        
        Examples:
            "add case for Ahmed" → True (search Ahmed first)
            "add client Ahmed 0501234567" → False (has full details)
        """
        
        input_lower = user_input.lower()
        
        # Indicators that we should search first
        search_indicators = [
            'للعميل', 'للموكل', 'لـ', 'بخصوص', 'عن'
        ]
        
        # Indicators we have full details (can create directly)
        direct_create_indicators = [
            '050', '055', '056',  # Phone numbers
            '@',  # Email
            'رقم',  # Has ID/number
        ]
        
        if any(ind in input_lower for ind in search_indicators):
            # Mentioned existing entity - search first
            return True
        
        if any(ind in input_lower for ind in direct_create_indicators):
            # Has specific details - create directly
            return False
        
        # Default: search first to be safe
        return True


__all__ = ['IntelligentToolSelector']
