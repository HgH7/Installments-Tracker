from app.extensions.events.dispatcher import EventDispatcher
from app.extensions.events.event import Event
from app.extensions.events.hooks import HookRegistry

dispatcher = EventDispatcher()
hooks = HookRegistry()

__all__ = ["EventDispatcher", "Event", "HookRegistry", "dispatcher", "hooks"]
