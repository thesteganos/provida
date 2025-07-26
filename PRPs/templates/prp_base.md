name: "Modelo de PRP Pró-Vida"
description: |
  Este modelo é para criar Planos de Pesquisa de Projeto (PRPs) para o ecossistema Pró-Vida.

## Goal
[Descreva o objetivo desta tarefa ou recurso em uma frase.]

## Why
[Explique o valor de negócio e o impacto no usuário.]

## What
[Descreva o comportamento visível ao usuário e os requisitos técnicos.]

### Success Criteria
- [ ] [Resultado mensurável específico]

## All Needed Context

### Documentation & References
```yaml
- docfile: [provida.md]
  why: [O documento principal que descreve o sistema Pró-Vida.]
- docfile: [PRPs/provida_cli_prp.md]
  why: [O PRP que descreve a implementação do CLI Pró-Vida.]
```

### Known Gotchas of our codebase & Library Quirks
```python
# CRITICAL: A chave de API do Google deve ser carregada a partir de variáveis de ambiente.
# CRITICAL: Os nomes dos modelos de LLM não devem ser "hardcoded".
```

## Implementation Blueprint

### Data models and structure
[Descreva os modelos de dados e a estrutura necessários para esta tarefa.]

### list of tasks to be completed to fullfill the PRP in the order they should be completed
```yaml
Task 1:
...

Task N:
...
```

### Per task pseudocode as needed added to each task
```python
# Task 1
# ...
```

## Validation Loop

### Level 1: Syntax & Style
```bash
ruff check src/ --fix
mypy src/
```

### Level 2: Unit Tests
```python
# ...
```

```bash
uv run pytest tests/
```

### Level 3: Integration Test
```bash
# ...
```