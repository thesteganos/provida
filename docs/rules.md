# Rule Language

The file `src/config/rules.json` defines a simple rule engine used by
`autonomous_decision_maker.py`. Each rule has the following fields:

- `id`: unique identifier.
- `description`: human friendly explanation.
- `condition`: expression evaluated against a context dictionary.
- `action`: one or more actions separated by `&&` to execute when the
  condition is true.

Rules are stored as an array under the `rules` key:

```json
{
  "rules": [
    {
      "id": "rule1",
      "description": "If the user has not interacted with the application in the last 24 hours, send a reminder email.",
      "condition": "user.lastInteraction < now - 24 hours",
      "action": "sendReminderEmail(user.email)"
    }
  ]
}
```

The `condition` strings are parsed by the decision maker and should be
kept simple (comparisons or boolean flags). Actions are interpreted by
`autonomous_decision_maker.py` to trigger custom logic.
