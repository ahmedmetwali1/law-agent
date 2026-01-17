"""
Intent Analyzer
تحليل نية المستخدم واستخراج المهام
"""

import json
import logging
import uuid
from typing import List, Dict, Any
from agents.planning.task_models import Task
from agents.planning.intelligent_tool_selector import IntelligentToolSelector

logger = logging.getLogger(__name__)


class IntentAnalyzer:
    """Analyzes user intent and extracts tasks"""
    
    def __init__(self, llm_client, reasoning_engine=None):
        self.llm_client = llm_client
        self.tool_selector = IntelligentToolSelector(reasoning_engine)
    
    def analyze(self, user_input: str, chat_history: List[Dict] = None, available_tools: List[str] = None) -> List[Task]:
        """
        Extract structured tasks from user input WITH INTELLIGENT REASONING
        
        Args:
            user_input: User's request
            chat_history: Previous conversation for context
            available_tools: List of available tool names
            
        Returns:
            List of Task objects
        """
        logger.info(f"🔍 Analyzing intent: {user_input[:100]}...")
        
        # 🧠 STEP 1: Intelligent tool strategy analysis
        if available_tools:
            strategy = self.tool_selector.analyze_request(user_input, available_tools)
            logger.info(f"📋 Tool strategy: {strategy['strategy']}")
            logger.info(f"💭 Reasoning: {strategy['reasoning']}")
        else:
            strategy = None
        
        # Build prompt for LLM with intelligent hints
        prompt = self._build_extraction_prompt(user_input, chat_history, strategy)
        
        # Call LLM to extract tasks
        try:
            response = self.llm_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1  # Low temperature for structured extraction
            )
            
            # Parse JSON response
            tasks_data = json.loads(response)
            
            # Convert to Task objects
            tasks = self._build_tasks(tasks_data)
            
            logger.info(f"✅ Extracted {len(tasks)} tasks")
            return tasks
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse LLM response: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Intent analysis failed: {e}")
            return []
    
    def _build_extraction_prompt(self, user_input: str, chat_history: List[Dict] = None, strategy: Dict = None) -> str:
        """Build prompt for task extraction WITH INTELLIGENT HINTS"""
        
        context = ""
        if chat_history:
            # Include recent context
            recent = chat_history[-3:] if len(chat_history) > 3 else chat_history
            context = "\n".join([
                f"{msg['role']}: {msg['content']}" 
                for msg in recent
            ])
        
        # Add intelligent strategy hints
        strategy_hint = ""
        if strategy:
            strategy_hint = f"""

🧠 INTELLIGENT ANALYSIS:
Strategy: {strategy['strategy']}
Reasoning: {strategy['reasoning']}
Suggested approach: {"Search for existing data before creating" if strategy['strategy'] == 'search_first' else "Create directly with provided information"}
"""
        
        prompt = f"""Extract tasks from the following user request.

User Request: "{user_input}"

{f'Previous Context:\\n{context}\\n' if context else ''}
{strategy_hint}

Identify all tasks the user wants to perform and return them as JSON array.

Each task should have:
- type: tool name (create_client, create_case, create_hearing, search_knowledge, etc.)
- params: parameters for the tool
- depends_on: list of task indices this depends on (e.g., [0] means depends on first task)

Available tools:
- create_client(full_name, phone, email, address)
- create_case(client_id, case_title, case_number, court_name, case_type)
- create_hearing(case_id, hearing_date, hearing_time, court_name)
- search_knowledge(query)
- get_client_details(client_id)
- list_all_clients()
- search_clients(query)

Example:
Input: "أضف موكل أحمد 0501234567 وافتح له قضية عقد"
Output:
[
  {{
    "type": "create_client",
    "params": {{"full_name": "أحمد", "phone": "0501234567"}},
    "depends_on": []
  }},
  {{
    "type": "create_case",
    "params": {{"client_id": "$0", "case_title": "عقد تجاري", "case_type": "تجاري"}},
    "depends_on": [0]
  }}
]

Note: Use "$0", "$1" etc. to reference results from previous tasks (e.g., "$0" = result of task 0)

Return ONLY the JSON array, no explanations.
"""
        
        return prompt
    
    def _build_tasks(self, tasks_data: List[Dict]) -> List[Task]:
        """Convert JSON data to Task objects"""
        
        tasks = []
        
        for i, task_data in enumerate(tasks_data):
            task = Task(
                id=f"task_{i}",
                type=task_data['type'],
                params=task_data['params'],
                depends_on=[f"task_{idx}" for idx in task_data.get('depends_on', [])]
            )
            tasks.append(task)
        
        return tasks
    
    def is_multi_step_request(self, user_input: str) -> bool:
        """
        🔍 ENHANCED: Better multi-step detection
        
        Detects if request likely has multiple steps based on:
        - Multiple action verbs
        - Multiple entities
        - Connectors like "و" (and)
        - Complex instructions with details
        
        Examples of multi-step:
        - "أضف موكل أحمد وافتح قضية" ✅ (2 actions)
        - "ضيف قضية رقم 123 وجدول جلسة" ✅ (2 actions + details)
        - "ابحث عن أحمد واعرض قضاياه" ✅ (2 actions)
        
        Examples of single-step:
        - "أضف موكل أحمد" ❌ (1 action)
        - "ما هي جلساتي اليوم؟" ❌ (question)
        """
        
        user_lower = user_input.lower()
        
        # Count action verbs
        act_verbs = [
            'أضف', 'ضيف', 'افتح', 'جدول', 'احذف', 'امسح', 
            'عدل', 'حدث', 'ابحث', 'اعرض', 'اطبع'
        ]
        action_count = sum(1 for verb in act_verbs if verb in user_lower)
        
        # Count entities
        entities = [
            'موكل', 'عميل', 'قضية', 'قضيه', 
            'جلسة', 'جلسه', 'وكالة', 'مستند'
        ]
        entity_count = sum(1 for entity in entities if entity in user_lower)
        
        # Check for connectors
        has_connector = ' و ' in user_input or ' ثم ' in user_input
        
        # Check for long detailed request (likely complex)
        is_detailed = len(user_input) > 50 and any(char.isdigit() for char in user_input)
        
        # Multi-step criteria:
        is_multi_step = (
            action_count >= 2 or  # Multiple actions
            (action_count >= 1 and entity_count >= 2) or  # Action + multiple entities
            (has_connector and entity_count >= 2) or  # Connector + entities
            (is_detailed and entity_count >= 2)  # Detailed + entities
        )
        
        if is_multi_step:
            logger.info(f"🎭 Multi-step detected: actions={action_count}, entities={entity_count}")
        
        return is_multi_step


__all__ = ['IntentAnalyzer']
