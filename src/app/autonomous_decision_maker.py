"""Evaluate and execute autonomous actions based on configurable rules."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List
import logging

logger = logging.getLogger(__name__)
system_logger = logging.getLogger('system_log')

# Load rules from rules.json relative to this file
RULES_PATH = Path(__file__).resolve().parent.parent / "config" / "rules.json"
with open(RULES_PATH, "r", encoding="utf-8") as file:
    rules: List[Dict[str, Any]] = json.load(file)["rules"]

def get_nested_value(data: Dict[str, Any], key_path: str):
    """Helper to get a nested value from a dictionary using a dot-separated path."""
    keys = key_path.split('.')
    current_value = data
    for key in keys:
        if isinstance(current_value, dict) and key in current_value:
            current_value = current_value[key]
        else:
            return None # Key not found
    return current_value

def evaluate_conditions(rule: Dict[str, Any], context: Dict[str, Any]) -> bool:
    """Evaluate whether ``rule`` should trigger given ``context``."""
    condition = rule["condition"]
    condition_type = condition["type"]

    if condition_type == "comparison":
        operand1_path = condition["operand1"]
        operand2_data = condition["operand2"]
        operator = condition["operator"]

        value1 = get_nested_value(context, operand1_path)

        if operand2_data["type"] == "datetime_offset":
            unit = operand2_data["unit"]
            offset_value = operand2_data["value"]
            if unit == "hours":
                value2 = datetime.now() - timedelta(hours=offset_value)
            else:
                logger.warning(f"Unrecognized datetime offset unit: {unit}")
                return False
        else:
            logger.warning(f"Unrecognized operand2 type: {operand2_data["type"]}")
            return False

        if value1 is None or value2 is None:
            return False

        if operator == "less_than":
            return value1 < value2
        else:
            logger.warning(f"Unrecognized comparison operator: {operator}")
            return False

    elif condition_type == "boolean_flag":
        flag_path = condition["flag"]
        flag_value = get_nested_value(context, flag_path)
        return bool(flag_value)

    else:
        logger.warning(f"Unrecognized condition type: {condition_type}")
        return False

def execute_action(action: Dict[str, Any], context: Dict[str, Any]) -> None:
    """Execute the given action with the provided context."""
    action_type = action["type"]
    params = action.get("params", {})

    # Resolve parameters that are context paths
    resolved_params = {}
    for key, value in params.items():
        if isinstance(value, str) and '.' in value:
            resolved_params[key] = get_nested_value(context, value)
        else:
            resolved_params[key] = value

    if action_type == "send_email":
        system_logger.info(f"Sending email to {resolved_params.get('to')} with subject: {resolved_params.get('subject')}")
        # Placeholder for actual email sending logic
    elif action_type == "log_error":
        system_logger.error(f"Application error: {resolved_params.get('message')}")
    elif action_type == "notify_support":
        system_logger.info(f"Notifying support team about error: {resolved_params.get('error_details')}")
        # Placeholder for actual support notification logic
    else:
        logger.warning(f"Unrecognized action type: {action_type}")

def make_autonomous_decisions(context: Dict[str, Any]) -> None:
    """Run the decision loop for all configured rules."""
    for rule in rules:
        if evaluate_conditions(rule, context):
            system_logger.info(f"Rule '{rule['id']}' triggered: {rule['description']}")
            for action in rule["actions"]:
                execute_action(action, context)



