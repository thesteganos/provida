"""Evaluate and execute autonomous actions based on configurable rules."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

# Load rules from rules.json relative to this file
RULES_PATH = Path(__file__).resolve().parent.parent / "config" / "rules.json"
with open(RULES_PATH, "r", encoding="utf-8") as file:
    rules: List[Dict[str, Any]] = json.load(file)["rules"]

def evaluate_conditions(rule: Dict[str, Any], context: Dict[str, Any]) -> bool:
    """Evaluate whether ``rule`` should trigger given ``context``."""
    # Simple condition evaluation for demonstration purposes
    if rule['id'] == 'rule1':
        # Example condition: user has not interacted in the last 24 hours
        last_interaction = context.get('user', {}).get('lastInteraction', datetime.now() - timedelta(days=25))
        return last_interaction < datetime.now() - timedelta(days=24)
    elif rule['id'] == 'rule2':
        # Example condition: application detected an error
        error_detected = context.get('application', {}).get('errorDetected', False)
        return error_detected
    return False

def execute_action(action: str, context: Dict[str, Any]) -> None:
    """Execute the given action string with the provided context."""
    # Simple action execution for demonstration purposes
    if action == 'sendReminderEmail(user.email)':
        user_email = context.get('user', {}).get('email', 'default@example.com')
        print(f"Sending reminder email to {user_email}")
    elif action == 'logError(application.error) && notifySupportTeam(application.error)':
        error = context.get('application', {}).get('error', 'Unknown error')
        print(f"Logging error: {error}")
        print(f"Notifying support team about error: {error}")

def make_autonomous_decisions(context: Dict[str, Any]) -> None:
    """Run the decision loop for all configured rules."""
    for rule in rules:
        if evaluate_conditions(rule, context):
            actions = rule["action"].split(" && ")
            for action in actions:
                execute_action(action, context)

# Example usage
if __name__ == "__main__":
    context = {
        'user': {
            'lastInteraction': datetime.now() - timedelta(days=25),
            'email': 'user@example.com'
        },
        'application': {
            'errorDetected': True,
            'error': 'Sample error'
        }
    }
    make_autonomous_decisions(context)

