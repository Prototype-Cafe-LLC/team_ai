"""Test event bus functionality."""
import pytest
import asyncio
from app.core.events import EventBus


class TestEventBus:
    """Test EventBus class."""
    
    @pytest.fixture
    def event_bus(self):
        """Create event bus instance."""
        return EventBus()
    
    @pytest.mark.asyncio
    async def test_emit_and_subscribe(self, event_bus: EventBus):
        """Test basic emit and subscribe functionality."""
        received_events = []
        
        def handler(event_type: str, data: dict):
            received_events.append((event_type, data))
        
        # Subscribe to event
        event_bus.subscribe("test_event", handler)
        
        # Emit event
        await event_bus.emit("test_event", {"message": "Hello"})
        
        # Verify event was received
        assert len(received_events) == 1
        assert received_events[0][0] == "test_event"
        assert received_events[0][1]["message"] == "Hello"
    
    @pytest.mark.asyncio
    async def test_async_handler(self, event_bus: EventBus):
        """Test async event handler."""
        received_events = []
        
        async def async_handler(event_type: str, data: dict):
            await asyncio.sleep(0.01)  # Simulate async work
            received_events.append((event_type, data))
        
        # Subscribe async handler
        event_bus.subscribe("async_event", async_handler)
        
        # Emit event
        await event_bus.emit("async_event", {"value": 42})
        
        # Verify event was received
        assert len(received_events) == 1
        assert received_events[0][1]["value"] == 42
    
    @pytest.mark.asyncio
    async def test_wildcard_subscription(self, event_bus: EventBus):
        """Test wildcard subscription to all events."""
        all_events = []
        
        def wildcard_handler(event_type: str, data: dict):
            all_events.append(event_type)
        
        # Subscribe to all events
        event_bus.subscribe("*", wildcard_handler)
        
        # Emit various events
        await event_bus.emit("event1", {})
        await event_bus.emit("event2", {})
        await event_bus.emit("event3", {})
        
        # Should receive all events
        assert len(all_events) == 3
        assert "event1" in all_events
        assert "event2" in all_events
        assert "event3" in all_events
    
    @pytest.mark.asyncio
    async def test_multiple_subscribers(self, event_bus: EventBus):
        """Test multiple subscribers to same event."""
        results = []
        
        def handler1(event_type: str, data: dict):
            results.append("handler1")
        
        def handler2(event_type: str, data: dict):
            results.append("handler2")
        
        async def handler3(event_type: str, data: dict):
            results.append("handler3")
        
        # Subscribe multiple handlers
        event_bus.subscribe("multi_event", handler1)
        event_bus.subscribe("multi_event", handler2)
        event_bus.subscribe("multi_event", handler3)
        
        # Emit event
        await event_bus.emit("multi_event", {})
        
        # All handlers should be called
        assert len(results) == 3
        assert "handler1" in results
        assert "handler2" in results
        assert "handler3" in results
    
    @pytest.mark.asyncio
    async def test_unsubscribe(self, event_bus: EventBus):
        """Test unsubscribing from events."""
        call_count = 0
        
        def handler(event_type: str, data: dict):
            nonlocal call_count
            call_count += 1
        
        # Subscribe
        event_bus.subscribe("unsub_event", handler)
        
        # Emit - should receive
        await event_bus.emit("unsub_event", {})
        assert call_count == 1
        
        # Unsubscribe
        event_bus.unsubscribe("unsub_event", handler)
        
        # Emit again - should not receive
        await event_bus.emit("unsub_event", {})
        assert call_count == 1  # Still 1
    
    @pytest.mark.asyncio
    async def test_event_history(self, event_bus: EventBus):
        """Test event history tracking."""
        # Emit several events
        await event_bus.emit("history_event1", {"value": 1})
        await event_bus.emit("history_event2", {"value": 2})
        await event_bus.emit("history_event1", {"value": 3})
        
        # Get all history
        history = event_bus.get_history()
        assert len(history) >= 3
        
        # Get filtered history
        filtered = event_bus.get_history(event_type="history_event1")
        assert len(filtered) == 2
        assert all(e["type"] == "history_event1" for e in filtered)
        
        # Test limit
        limited = event_bus.get_history(limit=2)
        assert len(limited) <= 2
    
    @pytest.mark.asyncio
    async def test_error_handling(self, event_bus: EventBus):
        """Test error handling in event handlers."""
        successful_calls = []
        
        def failing_handler(event_type: str, data: dict):
            raise Exception("Handler failed")
        
        def working_handler(event_type: str, data: dict):
            successful_calls.append(event_type)
        
        # Subscribe both handlers
        event_bus.subscribe("error_event", failing_handler)
        event_bus.subscribe("error_event", working_handler)
        
        # Emit event - should not crash
        await event_bus.emit("error_event", {})
        
        # Working handler should still be called
        assert len(successful_calls) == 1
        assert successful_calls[0] == "error_event"
    
    @pytest.mark.asyncio
    async def test_concurrent_emit(self, event_bus: EventBus):
        """Test concurrent event emission."""
        received_events = []
        
        async def slow_handler(event_type: str, data: dict):
            await asyncio.sleep(0.05)
            received_events.append(data["id"])
        
        event_bus.subscribe("concurrent_event", slow_handler)
        
        # Emit multiple events concurrently
        tasks = []
        for i in range(5):
            task = event_bus.emit("concurrent_event", {"id": i})
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        
        # All events should be received
        assert len(received_events) == 5
        assert set(received_events) == {0, 1, 2, 3, 4}
    
    @pytest.mark.asyncio
    async def test_history_limit(self, event_bus: EventBus):
        """Test event history size limit."""
        # Emit more events than the limit
        for i in range(1500):
            await event_bus.emit("spam_event", {"index": i})
        
        history = event_bus.get_history()
        
        # Should be limited to max_history (1000)
        assert len(history) == 1000
        
        # Should keep the most recent events
        assert history[-1]["data"]["index"] == 1499