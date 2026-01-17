"""
MCP - Model Context Protocol
بروتوكول السياق الموحد للتواصل بين الوكلاء

Based on 2025 standards for agent communication
Similar to USB-C for AI systems - vendor-neutral protocol

Features:
- Standardized message format
- Asynchronous communication
- Type-safe messaging
- Event-driven architecture
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import asyncio
import logging
import json

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """Types of messages in MCP"""
    REQUEST = "request"
    RESPONSE = "response"
    EVENT = "event"
    COMMAND = "command"
    QUERY = "query"
    NOTIFICATION = "notification"


class MessagePriority(str, Enum):
    """Message priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class MCPMessage:
    """Standard MCP message format"""
    message_id: str
    message_type: MessageType
    sender: str
    receiver: str
    payload: Dict[str, Any]
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None  # For request-response pairing
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "message_id": self.message_id,
            "type": self.message_type.value,
            "sender": self.sender,
            "receiver": self.receiver,
            "payload": self.payload,
            "priority": self.priority.value,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "metadata": self.metadata
        }
    
    def to_json(self) -> str:
        """Serialize to JSON"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPMessage':
        """Deserialize from dictionary"""
        return cls(
            message_id=data["message_id"],
            message_type=MessageType(data["type"]),
            sender=data["sender"],
            receiver=data["receiver"],
            payload=data["payload"],
            priority=MessagePriority(data.get("priority", "normal")),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            correlation_id=data.get("correlation_id"),
            metadata=data.get("metadata", {})
        )


class MCPAgent:
    """
    MCP-compatible agent
    Can send and receive messages via the protocol
    """
    
    def __init__(self, agent_id: str, agent_type: str = "generic"):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.message_handlers: Dict[MessageType, Callable] = {}
        self.message_queue: asyncio.Queue = asyncio.Queue()
        
        logger.info(f"✅ MCP Agent '{agent_id}' initialized")
    
    def register_handler(
        self,
        message_type: MessageType,
        handler: Callable
    ) -> None:
        """Register a message handler"""
        self.message_handlers[message_type] = handler
        logger.debug(f"Registered handler for {message_type.value}")
    
    async def send_message(
        self,
        receiver: str,
        message_type: MessageType,
        payload: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> MCPMessage:
        """Send a message to another agent"""
        message = MCPMessage(
            message_id=f"{self.agent_id}_{datetime.now().timestamp()}",
            message_type=message_type,
            sender=self.agent_id,
            receiver=receiver,
            payload=payload,
            priority=priority
        )
        
        logger.info(f"📤 {self.agent_id} → {receiver}: {message_type.value}")
        return message
    
    async def receive_message(self, message: MCPMessage) -> Optional[MCPMessage]:
        """Receive and process a message"""
        logger.info(f"📥 {self.agent_id} ← {message.sender}: {message.message_type.value}")
        
        # Check if we have a handler
        handler = self.message_handlers.get(message.message_type)
        
        if handler:
            # Process message
            result = await handler(message)
            
            # If it's a request, send response
            if message.message_type == MessageType.REQUEST:
                response = MCPMessage(
                    message_id=f"{self.agent_id}_resp_{datetime.now().timestamp()}",
                    message_type=MessageType.RESPONSE,
                    sender=self.agent_id,
                    receiver=message.sender,
                    payload=result,
                    correlation_id=message.message_id
                )
                return response
        
        else:
            logger.warning(f"No handler for {message.message_type.value}")
        
        return None


class MessageBus:
    """
    Central message bus for MCP communication
    Routes messages between agents
    """
    
    def __init__(self):
        self.agents: Dict[str, MCPAgent] = {}
        self.message_history: List[MCPMessage] = []
        self.subscriptions: Dict[str, List[str]] = {}  # topic -> agent_ids
        
        logger.info("✅ MCP Message Bus initialized")
    
    def register_agent(self, agent: MCPAgent) -> None:
        """Register an agent with the bus"""
        self.agents[agent.agent_id] = agent
        logger.info(f"📝 Agent '{agent.agent_id}' registered with message bus")
    
    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            logger.info(f"Agent '{agent_id}' unregistered")
    
    async def route_message(self, message: MCPMessage) -> Optional[MCPMessage]:
        """Route a message to the receiver"""
        # Log message
        self.message_history.append(message)
        
        # Find receiver
        receiver_agent = self.agents.get(message.receiver)
        
        if receiver_agent:
            # Deliver message
            response = await receiver_agent.receive_message(message)
            
            # If there's a response, route it back
            if response:
                self.message_history.append(response)
                sender_agent = self.agents.get(response.receiver)
                if sender_agent:
                    await sender_agent.receive_message(response)
            
            return response
        else:
            logger.error(f"Receiver '{message.receiver}' not found")
            return None
    
    async def broadcast(
        self,
        sender: str,
        topic: str,
        payload: Dict[str, Any]
    ) -> None:
        """Broadcast a message to all subscribed agents"""
        subscribers = self.subscriptions.get(topic, [])
        
        logger.info(f"📢 Broadcasting '{topic}' to {len(subscribers)} agents")
        
        for agent_id in subscribers:
            if agent_id != sender:  # Don't send to self
                message = MCPMessage(
                    message_id=f"broadcast_{datetime.now().timestamp()}",
                    message_type=MessageType.EVENT,
                    sender=sender,
                    receiver=agent_id,
                    payload={"topic": topic, "data": payload}
                )
                await self.route_message(message)
    
    def subscribe(self, agent_id: str, topic: str) -> None:
        """Subscribe an agent to a topic"""
        if topic not in self.subscriptions:
            self.subscriptions[topic] = []
        
        if agent_id not in self.subscriptions[topic]:
            self.subscriptions[topic].append(agent_id)
            logger.debug(f"Agent '{agent_id}' subscribed to '{topic}'")
    
    def unsubscribe(self, agent_id: str, topic: str) -> None:
        """Unsubscribe an agent from a topic"""
        if topic in self.subscriptions and agent_id in self.subscriptions[topic]:
            self.subscriptions[topic].remove(agent_id)
            logger.debug(f"Agent '{agent_id}' unsubscribed from '{topic}'")
    
    def get_message_history(
        self,
        agent_id: Optional[str] = None,
        limit: int = 100
    ) -> List[MCPMessage]:
        """Get message history"""
        if agent_id:
            # Filter by agent
            filtered = [
                m for m in self.message_history
                if m.sender == agent_id or m.receiver == agent_id
            ]
            return filtered[-limit:]
        
        return self.message_history[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get message bus statistics"""
        return {
            "total_agents": len(self.agents),
            "total_messages": len(self.message_history),
            "active_topics": len(self.subscriptions),
            "agents": list(self.agents.keys()),
            "topics": list(self.subscriptions.keys())
        }


class MCPProtocol:
    """
    Complete MCP Protocol implementation
    Manages agents and message bus
    """
    
    def __init__(self):
        self.bus = MessageBus()
        self.protocol_version = "1.0"
        
        logger.info("=" * 60)
        logger.info("✅ MCP Protocol initialized (v1.0)")
        logger.info("=" * 60)
    
    def create_agent(
        self,
        agent_id: str,
        agent_type: str = "generic"
    ) -> MCPAgent:
        """Create and register a new MCP agent"""
        agent = MCPAgent(agent_id=agent_id, agent_type=agent_type)
        self.bus.register_agent(agent)
        return agent
    
    async def send_request(
        self,
        sender_id: str,
        receiver_id: str,
        request_data: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL
    ) -> Optional[MCPMessage]:
        """Send a request and wait for response"""
        sender = self.bus.agents.get(sender_id)
        
        if not sender:
            logger.error(f"Sender '{sender_id}' not found")
            return None
        
        message = await sender.send_message(
            receiver=receiver_id,
            message_type=MessageType.REQUEST,
            payload=request_data,
            priority=priority
        )
        
        response = await self.bus.route_message(message)
        return response
    
    async def send_command(
        self,
        sender_id: str,
        receiver_id: str,
        command: str,
        params: Dict[str, Any] = None
    ) -> None:
        """Send a command (fire-and-forget)"""
        sender = self.bus.agents.get(sender_id)
        
        if not sender:
            logger.error(f"Sender '{sender_id}' not found")
            return
        
        message = await sender.send_message(
            receiver=receiver_id,
            message_type=MessageType.COMMAND,
            payload={"command": command, "params": params or {}}
        )
        
        await self.bus.route_message(message)
    
    def get_protocol_info(self) -> Dict[str, Any]:
        """Get protocol information"""
        return {
            "version": self.protocol_version,
            "bus_stats": self.bus.get_stats(),
            "message_types": [t.value for t in MessageType],
            "priority_levels": [p.value for p in MessagePriority]
        }


__all__ = [
    "MCPProtocol",
    "MCPAgent",
    "MessageBus",
    "MCPMessage",
    "MessageType",
    "MessagePriority"
]
