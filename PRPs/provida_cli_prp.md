name: "Pró-Vida CLI PRP"
description: |
  Este PRP descreve a implementação do CLI Pró-Vida, um assistente de pesquisa autônomo para cirurgia bariátrica.

## Goal
Construir um CLI para o ecossistema Pró-Vida que permita aos usuários interagir com os modos "Consulta Rápida" e "Pesquisa Profunda", gerenciar configurações e executar tarefas de manutenção.

## Why
- Fornecer uma interface de linha de comando para o sistema Pró-Vida.
- Permitir que os usuários realizem pesquisas, gerenciem configurações e executem tarefas de manutenção de forma eficiente.
- Automatizar o processo de pesquisa e análise de informações para cirurgiões bariátricos.

## What
Um CLI com os seguintes comandos:
- `provida rapida <query>`: Executa uma consulta rápida usando o modo RAG.
- `provida profunda <query>`: Inicia uma pesquisa profunda sobre um tópico.
- `provida config <setting> <value>`: Gerencia as configurações do sistema.
- `provida manter`: Executa tarefas de manutenção, como atualização de conhecimento.

### Success Criteria
- [ ] O comando `provida rapida` retorna uma resposta rápida e relevante.
- [ ] O comando `provida profunda` inicia uma pesquisa profunda e exibe o progresso.
- [ ] O comando `provida config` permite que os usuários visualizem e atualizem as configurações.
- [ ] O comando `provida manter` executa as tarefas de manutenção com sucesso.

## All Needed Context

### Documentation & References
```yaml
- docfile: [provida.md]
  why: [O documento principal que descreve o sistema Pró-Vida.]
```

### Known Gotchas of our codebase & Library Quirks
```python
# CRITICAL: A chave de API do Google deve ser carregada a partir de variáveis de ambiente.
# CRITICAL: Os nomes dos modelos de LLM não devem ser "hardcoded".
```

## Implementation Blueprint

### Data models and structure
```python
# Pydantic models para as configurações do sistema
from pydantic import BaseModel

class LLMSettings(BaseModel):
    planning_model: str
    analysis_model: str
    synthesis_model: str
    rag_model: str
    chat_model: str
    translation_model: str
    extraction_model: str

class SystemSettings(BaseModel):
    google_api_key: str
    deep_search_limit: int
    llm: LLMSettings
```

### list of tasks to be completed to fullfill the PRP in the order they should be completed
```yaml
Task 1:
CREATE src/provida/cli.py:
  - Implementar a estrutura básica do CLI usando Typer.
  - Adicionar os comandos `rapida`, `profunda`, `config` e `manter`.

Task 2:
CREATE src/provida/config.py:
  - Implementar a lógica para carregar e salvar as configurações do sistema a partir de um arquivo YAML.
  - Usar os modelos Pydantic para validação.

Task 3:
CREATE src/provida/agents.py:
  - Implementar a lógica para interagir com os modelos Gemini.
  - Criar funções para cada um dos agentes descritos no `provida.md`.

Task 4:
CREATE src/provida/modes.py:
  - Implementar a lógica para os modos "Consulta Rápida" e "Pesquisa Profunda".
  - Integrar os agentes para executar as tarefas de cada modo.
```

## Validation Loop

### Level 1: Syntax & Style
```bash
ruff check src/ --fix
mypy src/
```

### Level 2: Unit Tests
```python
# CREATE tests/test_cli.py
def test_rapida_command():
    ...

def test_profunda_command():
    ...

# CREATE tests/test_config.py
def test_load_config():
    ...

def test_save_config():
    ...
```

```bash
uv run pytest tests/
```

### Level 3: Integration Test
```bash
# Testar os comandos do CLI
provida rapida "qual o tratamento para obesidade?"
provida profunda "novas técnicas em cirurgia bariátrica"
```
