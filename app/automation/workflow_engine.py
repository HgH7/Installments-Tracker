import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from app.events import dispatcher

logger = logging.getLogger(__name__)

WORKFLOWS_DB = "data/automation_workflows.json"

StepHandler = Callable[[Dict[str, Any]], Dict[str, Any]]


@dataclass
class WorkflowStep:
    id: str
    type: str
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Workflow:
    id: str
    name: str
    trigger_event: str
    steps: List[WorkflowStep] = field(default_factory=list)
    enabled: bool = True


class WorkflowEngine:
    """Sequential multi-step automation workflows."""

    def __init__(self):
        self._workflows: Dict[str, Workflow] = {}
        self._step_registry: Dict[str, StepHandler] = {}
        self._load_workflows()
        self._wire_events()

    def register_step_handler(self, step_type: str, handler: StepHandler):
        self._step_registry[step_type] = handler

    def add_workflow(self, wf: Workflow) -> str:
        self._workflows[wf.id] = wf
        self._save_workflows()
        return wf.id

    def remove_workflow(self, wf_id: str):
        self._workflows.pop(wf_id, None)
        self._save_workflows()

    def get_workflow(self, wf_id: str) -> Optional[Workflow]:
        return self._workflows.get(wf_id)

    def list_workflows(self) -> List[Workflow]:
        return list(self._workflows.values())

    def _wire_events(self):
        def handler(event):
            for wf in self._workflows.values():
                if wf.enabled and wf.trigger_event == event.name:
                    self._execute(wf, event.data)

        dispatcher.on("*", handler)

    def _execute(self, wf: Workflow, data: Dict[str, Any]):
        ctx = dict(data)
        for step in wf.steps:
            handler = self._step_registry.get(step.type)
            if not handler:
                logger.warning("No handler for step type: %s", step.type)
                continue
            try:
                result = handler({**ctx, **step.config})
                if result:
                    ctx.update(result)
            except Exception as e:
                logger.error("Workflow step %s failed: %s", step.id, e)
                break
        dispatcher.emit("automation.workflow_completed", {"workflow_id": wf.id})

    def _load_workflows(self):
        if os.path.exists(WORKFLOWS_DB):
            try:
                with open(WORKFLOWS_DB) as f:
                    data = json.load(f)
                for w in data:
                    steps = [WorkflowStep(**s) for s in w.pop("steps", [])]
                    self._workflows[w["id"]] = Workflow(**w, steps=steps)
            except (json.JSONDecodeError, IOError):
                pass

    def _save_workflows(self):
        os.makedirs(os.path.dirname(WORKFLOWS_DB), exist_ok=True)
        serializable = []
        for wf in self._workflows.values():
            d = {"id": wf.id, "name": wf.name, "trigger_event": wf.trigger_event,
                 "enabled": wf.enabled, "steps": [s.__dict__ for s in wf.steps]}
            serializable.append(d)
        with open(WORKFLOWS_DB, "w") as f:
            json.dump(serializable, f, indent=2)

    def builtin_step_handlers(self) -> Dict[str, StepHandler]:
        return {
            "create_reminder": lambda ctx: (
                dispatcher.emit("reminder.generated", ctx), ctx
            )[1],
            "generate_document": lambda ctx: (
                dispatcher.emit("document.generate", ctx), ctx
            )[1],
            "log_activity": lambda ctx: (
                dispatcher.emit("activity.logged", ctx), ctx
            )[1],
            "send_notification": lambda ctx: (
                dispatcher.emit("notification.send", ctx), ctx
            )[1],
            "delay": lambda ctx: ctx,
            "filter": lambda ctx: ctx if ctx.get("status") == ctx.get("value") else {},
        }
