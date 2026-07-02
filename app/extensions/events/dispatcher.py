import logging
import traceback
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional

from app.extensions.events.event import Event

logger = logging.getLogger(__name__)

Handler = Callable[[Event], Any]


class EventDispatcher:
    """Synchronous in-process event bus.

    Listeners subscribe to event names (supports glob patterns via '*' suffix).
    """

    def __init__(self):
        self._listeners: Dict[str, List[Handler]] = defaultdict(list)
        self._wildcard: List[Handler] = []

    def on(self, event_name: str, handler: Handler):
        if event_name == "*":
            self._wildcard.append(handler)
        else:
            self._listeners[event_name].append(handler)

    def off(self, event_name: str, handler: Optional[Handler] = None):
        if handler is None:
            self._listeners.pop(event_name, None)
        else:
            try:
                self._listeners[event_name].remove(handler)
            except (KeyError, ValueError):
                pass

    def emit(self, event_name: str, data: Optional[Dict[str, Any]] = None,
             source: Optional[str] = None) -> Event:
        event = Event(name=event_name, data=data or {}, source=source)
        for h in self._wildcard:
            try:
                h(event)
            except Exception:
                logger.error("Wildcard handler error: %s", traceback.format_exc())
            if event.stopped:
                return event
        for h in self._listeners.get(event_name, []):
            try:
                h(event)
            except Exception:
                logger.error("Handler error for %s: %s", event_name, traceback.format_exc())
            if event.stopped:
                break
        return event

    def clear(self):
        self._listeners.clear()
        self._wildcard.clear()

    def listener_count(self) -> int:
        return sum(len(v) for v in self._listeners.values()) + len(self._wildcard)
