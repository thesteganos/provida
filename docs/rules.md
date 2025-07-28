# Rule Language

The file `src/config/rules.json` defines a simple rule engine used by
`autonomous_decision_maker.py`. Each rule has the following fields:

- `id`: unique identifier.
- `description`: human friendly explanation.
- `condition`: a structured object defining the criteria for the rule to trigger.
- `actions`: a list of structured objects, each defining an action to execute when the condition is true.

Rules are stored as an array under the `rules` key:

```json
{
  "rules": [
    {
      "id": "user_inactivity_reminder",
      "description": "Send a reminder email if the user has not interacted with the application in the last 24 hours.",
      "condition": {
        "type": "comparison",
        "operator": "less_than",
        "operand1": "user.lastInteraction",
        "operand2": {
          "type": "datetime_offset",
          "unit": "hours",
          "value": 24
        }
      },
      "actions": [
        {
          "type": "send_email",
          "params": {
            "to": "user.email",
            "subject": "Lembrete: Sua atenção é necessária no Pró-Vida",
            "body": "Olá, notamos que você não interage com o Pró-Vida há algum tempo. Gostaríamos de lembrá-lo de nossas funcionalidades."
          }
        }
      ]
    }
  ]
}
```

The `condition` object defines how the rule is evaluated. Supported types include:
- `comparison`: Compares two operands using a specified operator (e.g., `less_than`). `operand1` can be a path to a context value, and `operand2` can be a static value or a `datetime_offset` relative to `now`.
- `boolean_flag`: Evaluates a boolean flag from the context.

Each `action` object defines a specific operation to be performed. Supported types include:
- `send_email`: Sends an email with specified `to`, `subject`, and `body`.
- `log_error`: Logs an error message.
- `notify_support`: Notifies the support team with error details.

Parameters within actions (e.g., `user.email` in `send_email`) are resolved dynamically from the context dictionary.
