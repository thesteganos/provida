name: "PRP Pró-Vida: Implementação do CLI e Modo de Consulta Rápida"
description: |
  Este PRP detalha a criação do CLI (Command Line Interface) para o projeto Pró-Vida e a implementação do seu primeiro e mais fundamental comando: `provida rapida <query>`.

## Purpose
O objetivo deste PRP é estabelecer a fundação do CLI Pró-Vida e entregar a primeira funcionalidade de valor para o usuário final: a capacidade de fazer uma pergunta e receber uma resposta rápida e baseada em evidências, utilizando o modo de "Consulta Rápida" (RAG).

## Core Principles
Esta implementação seguirá rigorosamente os princípios de engenharia de contexto definidos em `PRPs/templates/prp_base.md`, com ênfase em:
1.  **Context is King**: Todas as decisões de design e implementação são informadas pelo `provida.md`.
2.  **Validation Loops**: A implementação será guiada por testes, com testes de unidade e integração para cada componente.
3.  **Progressive Success**: Este PRP foca no "caminho feliz" do modo de consulta rápida. Funcionalidades mais complexas como o modo de "Pesquisa Profunda" serão abordadas em PRPs futuros.
4.  **Clareza e Precisão**: O código será claro, bem documentado e seguirá os padrões definidos.

---

## Goal
Construir um CLI funcional para o Pró-Vida com o comando `provida rapida <query>`, que responde a perguntas do usuário utilizando a arquitetura RAG (Retrieval-Augmented Generation) definida no `provida.md`.

## Why
- **Valor de negócio**: Oferece uma ferramenta de produtividade imediata para o cirurgião, reduzindo o tempo de pesquisa e melhorando o acesso a informações baseadas em evidências.
- **Impacto no usuário**: Permite que o cirurgião obtenha respostas rápidas para questões clínicas no ponto de atendimento, sem a necessidade de uma pesquisa demorada.
- **Fundação técnica**: Cria a espinha dorsal do CLI, o sistema de configuração e a primeira integração com os modelos de IA, servindo de base para futuras expansões.

## What
- Um CLI baseado em Typer.
- Um comando `rapida` que aceita uma string de consulta (query).
- O comando orquestra uma busca no Vector DB e uma chamada para o modelo `Gemini 2.5 Flash`.
- A resposta é exibida no console, incluindo o resumo e as fontes.

### Success Criteria
- [ ] O CLI é executável via `python -m src.provida.cli`.
- [ ] O comando `provida rapida "qual a dose recomendada de vitamina D?"` executa sem erros.
- [ ] A implementação carrega a chave de API e as configurações do modelo de um arquivo de configuração, não hardcoded.
- [ ] A lógica de RAG (busca e síntese) é implementada na função `perform_rag_query`.
- [ ] Testes de unidade para `rag.py` e `config.py` passam.
- [ ] Um teste de integração para o comando `rapida` passa.
- [ ] O comando `--help` do CLI exibe ajuda para o comando `rapida`.

## All Needed Context

### Documentation & References (list all context needed to implement the feature)
```yaml
- docfile: [provida.md]
  why: |
    Documento fundamental que descreve toda a arquitetura, agentes, modelos de LLM e fluxos de trabalho do projeto Pró-Vida.
    CRITICAL: As seções 3 (Estratégia de Modelos), 4.1 (Modo Consulta Rápida) e 7 (Arquitetura de Dados) são as mais relevantes para este PRP.

- url: [https://typer.tiangolo.com/]
  why: |
    Documentação oficial do Typer. Essencial para criar o CLI, comandos, argumentos e opções.

- url: [https://pydantic-docs.helpmanual.io/usage/settings/]
  why: |
    Documentação do Pydantic para gerenciamento de configurações. O padrão a ser seguido para carregar a chave de API e outras configurações de forma segura.
```

### Known Gotchas of our codebase & Library Quirks
```python
# CRITICAL: A chave de API do Google (SUA_GOOGLE_API_KEY) DEVE ser carregada via variável de ambiente. Use o Pydantic Settings para gerenciar isso.
# CRITICAL: Os nomes dos modelos de LLM DEVEM ser lidos de um arquivo de configuração, não hardcoded. `provida.md` especifica `Gemini 2.5 Flash` para o modo RAG.
# PATTERN: Todo o código de I/O (chamadas de API, acesso a DB) DEVE ser `async`.
# GOTCHA: A biblioteca do Google Gemini tem clientes `async` e `sync`. USE SEMPRE a versão `async`.
```

## Implementation Blueprint

### Data models and structure
```python
# Em `src/provida/models.py`

from pydantic import BaseModel, Field
from typing import List

class RagResponse(BaseModel):
    """Modelo para a resposta do modo RAG."""
    summary: str = Field(..., description="O resumo gerado pelo LLM.")
    sources: List[str] = Field(..., description="Lista de fontes utilizadas para gerar o resumo.")

class LLMSettings(BaseModel):
    """Configurações para os modelos de LLM."""
    rag_model: str = "gemini-2.5-flash"

class Settings(BaseModel):
    """Configurações do sistema."""
    google_api_key: str
    llm: LLMSettings

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

### list of tasks to be completed to fullfill the PRP in the order they should be completed
```yaml
Task 1:
CREATE src/provida/models.py:
  - Adicionar os modelos Pydantic `RagResponse`, `LLMSettings` e `Settings` conforme definido acima.

Task 2:
CREATE src/provida/config.py:
  - Implementar uma função `get_settings()` que carrega e retorna uma instância do modelo `Settings`.
  - Usar `@lru_cache` para garantir que as configurações sejam carregadas apenas uma vez.

Task 3:
CREATE src/provida/rag.py:
  - Implementar a função `async def perform_rag_query(query: str) -> RagResponse`.
  - A função deve seguir o pseudocódigo abaixo, incluindo mocks iniciais para o DB e o LLM.

Task 4:
CREATE src/provida/cli.py:
  - Usar Typer para criar um app e o comando `rapida`.
  - O comando `rapida` deve chamar `perform_rag_query` e imprimir a resposta no console.
  - Adicionar docstrings para a ajuda do Typer.

Task 5:
CREATE tests/test_rag.py:
  - Implementar o teste de unidade `test_perform_rag_query_happy_path` conforme o pseudocódigo.

Task 6:
CREATE tests/test_cli.py:
  - Implementar um teste de integração simples para o CLI usando `Typer.testing.CliRunner`.
```

### Per task pseudocode as needed added to each task
```python
# Task 3: Pseudocódigo para `perform_rag_query` em `src/provida/rag.py`

import asyncio
from .config import get_settings
from .models import RagResponse
# from google.generativeai.async import GenerativeModel

async def perform_rag_query(query: str) -> RagResponse:
    if not query:
        raise ValueError("A consulta não pode ser vazia.")

    settings = get_settings()

    # Mock da busca no Vector DB
    await asyncio.sleep(0.1) # Simular I/O
    relevant_chunks = [
        {"source": "Artigo_A.pdf", "text": "A gastrectomia vertical é eficaz..."},
        {"source": "Artigo_B.pdf", "text": "Complicações incluem fístulas..."}
    ]

    prompt = f"""
    Com base nos seguintes trechos, responda à pergunta: {query}
    Trechos: {''.join([c['text'] for c in relevant_chunks])}
    Resposta:
    """

    # Mock da chamada ao LLM
    await asyncio.sleep(0.2) # Simular I/O
    # llm = GenerativeModel(settings.llm.rag_model, api_key=settings.google_api_key)
    # response = await llm.generate_content_async(prompt)
    llm_summary = "A gastrectomia vertical é um procedimento eficaz, com riscos de complicações como fístulas."

    return RagResponse(
        summary=llm_summary,
        sources=[chunk['source'] for chunk in relevant_chunks]
    )

# Task 4: Pseudocódigo para `cli.py`

import typer
import asyncio
from .rag import perform_rag_query

app = typer.Typer()

@app.command()
def rapida(query: str = typer.Argument(..., help="A pergunta para a consulta rápida.")):
    """
    Executa uma consulta rápida no modo RAG para obter respostas baseadas em evidências.
    """
    print(f"Buscando resposta para: '{query}'...")
    try:
        response = asyncio.run(perform_rag_query(query))
        print("\n--- Resumo ---")
        print(response.summary)
        print("\n--- Fontes ---")
        for source in response.sources:
            print(f"- {source}")
    except ValueError as e:
        typer.echo(f"Erro: {e}", err=True)

def main():
    app()
```

## Validation Loop

### Level 1: Syntax & Style
```bash
ruff check src/ tests/ --fix
mypy src/ tests/
```

### Level 2: Unit Tests
```python
# Em tests/test_rag.py
import pytest
from src.provida.rag import perform_rag_query

@pytest.mark.asyncio
async def test_perform_rag_query_raises_on_empty_query():
    with pytest.raises(ValueError):
        await perform_rag_query("")
```

```bash
pytest tests/
```

### Level 3: Integration Test (CLI)
```bash
# Em tests/test_cli.py
from typer.testing import CliRunner
from src.provida.cli import app

runner = CliRunner()

def test_rapida_command():
    result = runner.invoke(app, ["rapida", "teste"])
    assert result.exit_code == 0
    assert "Resumo" in result.stdout
    assert "Fontes" in result.stdout
```

## Final validation Checklist
- [ ] Todos os testes passam: `pytest tests/`
- [ ] Sem erros de linting: `ruff check src/ tests/`
- [ ] Sem erros de tipo: `mypy src/ tests/`
- [ ] O comando `python -m src.provida.cli rapida "teste"` executa e mostra uma resposta formatada.
- [ ] O comando `python -m src.provida.cli rapida ""` falha com uma mensagem de erro clara.
- [ ] O código está alinhado com `provida.md`.

---

## Anti-Patterns to Avoid
- ❌ **NÃO** hardcode a `GOOGLE_API_KEY`.
- ❌ **NÃO** hardcode o nome do modelo `gemini-2.5-flash`.
- ❌ **NÃO** use chamadas síncronas (`requests.get`) em código `async`.
- ❌ **NÃO** ignore o tratamento de erro para queries vazias ou inválidas.
- ❌ **NÃO** escreva código sem o teste de unidade correspondente.
- ❌ **NÃO** coloque lógica de negócio complexa diretamente no arquivo do CLI (`cli.py`). O CLI deve apenas orquestrar chamadas para outras partes do sistema.
