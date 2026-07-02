import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from app.events import dispatcher

logger = logging.getLogger(__name__)

RULES_DB = "data/automation_rules.json"

ConditionCheck = Callable[[Dict[str, Any]], bool]
ActionRun = Callable[[Dict[str, Any]], None]


@dataclass
class Rule:
    id: str
    name: str
    event: str
    conditions: List[dict] = field(default_factory=list)
    actions: List[dict] = field(default_factory=list)
    enabled: bool = True
    description: str = ""


class RuleEngine:
    """Evaluates rules when events fire and runs matching actions."""

    def __init__(self):
        self._rules: Dict[str, Rule] = {}
        self._condition_registry: Dict[str, ConditionCheck] = {}
        self._action_registry: Dict[str, ActionRun] = {}
        self._load_rules()
        self._wire_events()

    # ── Registration ─────────────────────────────────────────────────────

    def register_condition(self, name: str, fn: ConditionCheck):
        self._condition_registry[name] = fn

    def register_action(self, name: str, fn: ActionRun):
        self._action_registry[name] = fn

    # ── CRUD ─────────────────────────────────────────────────────────────

    def add_rule(self, rule: Rule) -> str:
        self._rules[rule.id] = rule
        self._save_rules()
        return rule.id

    def remove_rule(self, rule_id: str):
        self._rules.pop(rule_id, None)
        self._save_rules()

    def update_rule(self, rule: Rule):
        self._rules[rule.id] = rule
        self._save_rules()

    def get_rule(self, rule_id: str) -> Optional[Rule]:
        return self._rules.get(rule_id)

    def list_rules(self) -> List[Rule]:
        return list(self._rules.values())

    # ── Evaluation ───────────────────────────────────────────────────────

    def _wire_events(self):
        def handler(event):
            for rule in self._rules.values():
                if rule.enabled and rule.event == event.name:
                    self._evaluate(rule, event.data)

        dispatcher.on("*", handler)

    def _evaluate(self, rule: Rule, data: Dict[str, Any]):
        for cond in rule.conditions:
            check = self._condition_registry.get(cond.get("type"))
            if check and not check(data):
                return
        for action in rule.actions:
            runner = self._action_registry.get(action.get("type"))
            if runner:
                try:
                    runner(data)
                except Exception as e:
                    logger.error("Rule action failed: %s", e)
        dispatcher.emit("automation.rule_fired", {"rule_id": rule.id, "data": data})

    # ── Persistence ──────────────────────────────────────────────────────

    def _load_rules(self):
        if os.path.exists(RULES_DB):
            try:
                with open(RULES_DB) as f:
                    data = json.load(f)
                for r in data:
                    self._rules[r["id"]] = Rule(**r)
            except (json.JSONDecodeError, IOError):
                pass

    def _save_rules(self):
        os.makedirs(os.path.dirname(RULES_DB), exist_ok=True)
        with open(RULES_DB, "w") as f:
            json.dump([r.__dict__ for r in self._rules.values()], f, indent=2)

    def builtin_conditions(self):
        return {
            "amount_gt": lambda d: d.get("amount", 0) > float(d.get("threshold", 0)),
            "status_is": lambda d: d.get("status") == d.get("value"),
        }

    def builtin_actions(self):
        return {
            "log": lambda d: logger.info("Rule action: %s", d),
            "send_reminder": lambda d: dispatcher.emit("reminder.generated", d),
            "generate_document": lambda d: dispatcher.emit("document.generate", d),
        }
