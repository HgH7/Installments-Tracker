from app.events.dispatcher import EventDispatcher
from app.events.event import Event
from app.events.hooks import HookRegistry

dispatcher = EventDispatcher()
hooks = HookRegistry()

__all__ = ["EventDispatcher", "Event", "HookRegistry", "dispatcher", "hooks"]
