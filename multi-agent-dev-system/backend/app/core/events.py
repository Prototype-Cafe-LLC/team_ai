"""Event bus for the multi-agent system."""
from typing import Dict, List, Callable, Any, Optional
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class EventBus:
    """Simple event bus for system-wide events."""
    
    def __init__(self):
        """Initialize event bus."""
        self.subscribers: Dict[str, List[Callable]] = {}
        self.event_history: List[Dict[str, Any]] = []
        self.max_history = 1000
        
    async def emit(self, event_type: str, data: Dict[str, Any]):
        """Emit an event.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        # Add to history
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)
            
        # Notify subscribers
        if event_type in self.subscribers:
            tasks = []
            for callback in self.subscribers[event_type]:
                if asyncio.iscoroutinefunction(callback):
                    tasks.append(callback(event_type, data))
                else:
                    callback(event_type, data)
                    
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
                
        # Also emit to wildcard subscribers
        if "*" in self.subscribers:
            tasks = []
            for callback in self.subscribers["*"]:
                if asyncio.iscoroutinefunction(callback):
                    tasks.append(callback(event_type, data))
                else:
                    callback(event_type, data)
                    
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
                
        logger.debug(f"Emitted event: {event_type}")
        
    def subscribe(self, event_type: str, callback: Callable):
        """Subscribe to an event type.
        
        Args:
            event_type: Type of event to subscribe to (use "*" for all)
            callback: Callback function
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
            
        self.subscribers[event_type].append(callback)
        logger.debug(f"Subscribed to event: {event_type}")
        
    def unsubscribe(self, event_type: str, callback: Callable):
        """Unsubscribe from an event type.
        
        Args:
            event_type: Type of event
            callback: Callback function to remove
        """
        if event_type in self.subscribers:
            try:
                self.subscribers[event_type].remove(callback)
                if not self.subscribers[event_type]:
                    del self.subscribers[event_type]
            except ValueError:
                pass
                
    def get_history(
        self, 
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get event history.
        
        Args:
            event_type: Filter by event type
            limit: Maximum number of events to return
            
        Returns:
            List of events
        """
        if event_type:
            filtered = [e for e in self.event_history if e["type"] == event_type]
            return filtered[-limit:]
        else:
            return self.event_history[-limit:]
            
    def clear_history(self):
        """Clear event history."""
        self.event_history.clear()