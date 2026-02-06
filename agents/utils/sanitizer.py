from typing import List, Dict, Any, Union
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
import logging

logger = logging.getLogger(__name__)

class Sanitizer:
    """
    Sanitizes and compacts chat history and tools to prevent Context Overflow.
    Based on 'Progressive Disclosure' principles.
    """

    @staticmethod
    def compact_history(history: List[BaseMessage], max_tokens: int = 4000) -> List[BaseMessage]:
        """
        Compacts history by merging consecutive user messages and trimming old ones.
        Does NOT rely on a tokenizer for speed, uses character heuristic (1 token ~= 4 chars).
        """
        if not history:
            return []

        cleaned_history = []
        
        # 1. Merge Consecutive User Messages
        current_msg = None
        
        for msg in history:
            if isinstance(msg, HumanMessage):
                if current_msg and isinstance(current_msg, HumanMessage):
                    # Merge content
                    current_msg = HumanMessage(content=f"{current_msg.content}\n\n{msg.content}")
                else:
                    if current_msg: cleaned_history.append(current_msg)
                    current_msg = msg
            else:
                if current_msg:
                    cleaned_history.append(current_msg)
                    current_msg = None
                cleaned_history.append(msg)
        
        if current_msg:
            cleaned_history.append(current_msg)

        # 2. Trim Old Context (Heuristic)
        # Keep System Messages always!
        system_messages = [m for m in cleaned_history if isinstance(m, SystemMessage)]
        other_messages = [m for m in cleaned_history if not isinstance(m, SystemMessage)]
        
        # Simple heuristic: Only keep last N messages or char limit
        # Let's say max chars per message is 
        total_chars = sum(len(str(m.content)) for m in other_messages)
        max_chars = max_tokens * 4
        
        if total_chars > max_chars:
            logger.warning(f"🧹 History too long ({total_chars} chars). Compacting...")
            # Keep last 6 messages usually safe for recent context
            # But if individual messages are huge (e.g. OCR results), we must truncate THEM.
            
            compacted_others = []
            for m in reversed(other_messages):
                if len(str(m.content)) > 2000:
                    # Truncate content of very large messages in history
                    # But don't break JSON if possible? For History it's just string.
                    preview = str(m.content)[:500] + "\n... [Content Truncated for Memory] ..."
                    if isinstance(m, AIMessage):
                        compacted_others.insert(0, AIMessage(content=preview))
                    elif isinstance(m, HumanMessage):
                        compacted_others.insert(0, HumanMessage(content=preview))
                    else:
                        compacted_others.insert(0, m) # ToolMessage?
                else:
                    compacted_others.insert(0, m)
                
                # Check size again
                current_size = sum(len(str(x.content)) for x in compacted_others)
                if current_size > max_chars:
                    # Drop oldest (processed first in reversed loop means we inserted them last... wait)
                    # We are iterating reversed (newest first). So 'm' is newer.
                    # We insert at 0. So list grows [newest, ..., oldest] -> No.
                    # reversed: [newest, 2nd_newest, ...]
                    # Loop 1: insert(0, newest) -> [newest]
                    # Loop 2: insert(0, 2nd_newest) -> [2nd_newest, newest]
                    # If this list gets too big, we STOP adding older messages.
                    break
            
            other_messages = compacted_others

        return system_messages + other_messages

    @staticmethod
    def sanitize_tools_context(tool_results: List[Dict], max_len: int = 1500) -> List[Dict]:
        """
        Compacts tool outputs. If a tool result is huge (e.g. PDF text), 
        we replace it with a summary if it's not the critical focus.
        """
        clean_results = []
        for res in tool_results:
            content = res.get("content", "")
            if len(content) > max_len:
                # Naive truncation
                # In a real system, we'd ask an LLM to summarize, but that costs time/tokens.
                # We just clip for now.
                content = content[:max_len] + "... [Output Truncated]"
                
            clean_results.append({
                **res,
                "content": content
            })
        return clean_results
