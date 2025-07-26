name: "PRP Pró-Vida: Modelo Detalhado para Engenharia de Contexto"
description: |
  Modelo de PRP otimizado para o projeto Pró-Vida, focado em fornecer contexto rico e loops de validação para que os agentes de IA implementem funcionalidades de forma autônoma e iterativa.

## Purpose
Este modelo serve como um blueprint para a criação de Planos de Pesquisa de Projeto (PRPs) no ecossistema Pró-Vida. Seu propósito é garantir que cada PRP contenha informações suficientes para que um agente de IA possa:
1.  Entender completamente os requisitos da tarefa.
2.  Seguir os padrões de arquitetura e código do projeto.
3.  Implementar a funcionalidade de forma correta e consistente.
4.  Validar seu próprio trabalho através de testes e linting.
5.  Atingir um resultado funcional com o mínimo de intervenção humana.

## Core Principles
Os princípios a seguir, baseados na engenharia de contexto, devem guiar a criação de todos os PRPs:
1.  **Context is King**: Forneça TODA a documentação, exemplos e ressalvas necessárias. O agente só sabe o que está no PRP.
2.  **Validation Loops**: Forneça testes executáveis e comandos de lint que o agente possa rodar para validar e corrigir seu trabalho.
3.  **Information Dense**: Utilize palavras-chave, nomes de arquivos e padrões do código-fonte existente para guiar o agente.
4.  **Progressive Success**: Comece com a implementação mais simples possível, valide-a, e então adicione complexidade em passos subsequentes.
5.  **Clareza e Precisão**: Evite ambiguidades. Seja explícito sobre o que precisa ser feito e como.
6.  **Alinhamento com `provida.md`**: Todas as implementações devem estar alinhadas com a visão, arquitetura e requisitos definidos no documento `provida.md`.

---

## Goal
[Descreva o que precisa ser construído de forma clara e concisa. Seja específico sobre o estado final desejado.]
*Exemplo: Implementar o comando `provida rapida <query>` no CLI, que utiliza o modo RAG para responder a perguntas do usuário com base no conhecimento existente.*

## Why
[Justifique a necessidade da funcionalidade. Qual o valor para o negócio? Qual o impacto para o usuário?]
*Exemplo:*
- *Valor de negócio: Reduzir o tempo que o cirurgião gasta em pesquisas preliminares.*
- *Impacto no usuário: Fornecer respostas rápidas e baseadas em evidências para perguntas clínicas durante a prática diária.*
- *Integração: Este é o primeiro comando do CLI, servindo como base para os demais.*

## What
[Descreva o comportamento visível ao usuário e os requisitos técnicos detalhados.]
*Exemplo:*
- *O usuário poderá executar `provida rapida "qual a melhor técnica para gastrectomia vertical?"`.*
- *O sistema deve usar o modelo `Gemini 2.5 Flash` (conforme `provida.md`).*
- *A resposta deve ser gerada a partir da base de conhecimento vetorial.*
- *O comando deve ter um timeout de 30 segundos.*

### Success Criteria
[Liste os resultados específicos e mensuráveis que definem o sucesso.]
- [ ] O comando `provida rapida` é adicionado ao CLI e responde a queries.
- [ ] A implementação utiliza o `Vector DB` para buscar informações relevantes.
- [ ] O modelo `Gemini 2.5 Flash` é usado para sintetizar a resposta.
- [ ] Todos os testes de unidade e integração para o comando passam.
- [ ] O comando é documentado na ajuda do CLI (`--help`).

## All Needed Context

### Documentation & References (list all context needed to implement the feature)
```yaml
# MUST READ - Inclua estes na sua janela de contexto.
- docfile: [provida.md]
  why: |
    Documento fundamental que descreve toda a arquitetura, agentes, modelos de LLM e fluxos de trabalho do projeto Pró-Vida.
    CRITICAL: Preste atenção especial às seções 3 (Estratégia de Modelos), 4 (Modos de Operação) e 6 (Workflow Principal).

- file: [src/provida/config.py] # (Exemplo, se já existisse)
  why: |
    Mostra o padrão para carregar configurações, incluindo a chave de API e os nomes dos modelos, de forma segura a partir de variáveis de ambiente e arquivos de configuração.
    PATTERN: Seguir o padrão de uso de Pydantic para validação e carregamento de configurações.

- url: [https://typer.tiangolo.com/tutorial/first-steps/]
  why: |
    Tutorial oficial do Typer, a biblioteca que será usada para construir o CLI.
    CRITICAL: Entender como criar comandos, argumentos e opções.
```

### Known Gotchas of our codebase & Library Quirks
```python
# CRITICAL: A chave de API do Google (SUA_GOOGLE_API_KEY) DEVE ser carregada via variável de ambiente (`os.getenv`). NUNCA a coloque diretamente no código.
# CRITICAL: Os nomes dos modelos de LLM (e.g., 'gemini-1.5-pro-latest') NÃO DEVEM ser hardcoded. Devem ser lidos de um arquivo de configuração central (a ser criado em `src/provida/config.py`).
# PATTERN: Todas as funções que fazem I/O (chamadas de API, acesso a banco de dados) DEVEM ser `async`.
# GOTCHA: A biblioteca do Google para Gemini pode ter um cliente `async` e um `sync`. CERTIFIQUE-SE de usar a versão `async` em todo o projeto.
```

## Implementation Blueprint

### Data models and structure
Create the core data models, we ensure type safety and consistency. Use Pydantic for all data modeling.
```python
# Em `src/provida/models.py` (crie este arquivo se necessário)

from pydantic import BaseModel, Field
from typing import List

class QueryRequest(BaseModel):
    """Modelo para uma requisição de consulta do usuário."""
    query: str = Field(..., description="O texto da pergunta do usuário.")
    mode: str = Field(default="rapida", description="Modo de operação: 'rapida' ou 'profunda'.")

class DocumentChunk(BaseModel):
    """Representa um trecho de documento da base de conhecimento."""
    source_id: str
    text: str
    embedding: List[float]

class RagResponse(BaseModel):
    """Modelo para a resposta do modo RAG."""
    summary: str
    sources: List[str]
```

### list of tasks to be completed to fullfill the PRP in the order they should be completed
```yaml
Task 1:
CREATE src/provida/cli.py:
  - Usar Typer para criar a estrutura inicial do CLI.
  - Adicionar um comando placeholder `rapida` que aceita uma string como argumento.

Task 2:
CREATE src/provida/config.py:
  - Implementar uma classe `Settings` com Pydantic para carregar a `GOOGLE_API_KEY` de variáveis de ambiente.
  - Adicionar a configuração dos modelos de LLM conforme especificado em `provida.md`.

Task 3:
MODIFY src/provida/cli.py:
  - Importar e usar a lógica de configuração.
  - Implementar a lógica do comando `rapida` para chamar uma função (a ser criada) que orquestra a busca RAG.

Task 4:
CREATE src/provida/rag.py:
  - Implementar a função `perform_rag_query(query: str) -> RagResponse`.
  - Esta função deve:
    1. Conectar-se ao Vector DB (inicialmente pode ser um mock).
    2. Buscar chunks de documentos relevantes para a query.
    3. Chamar o LLM `Gemini 2.5 Flash` com os chunks e a query para gerar uma síntese.
    4. Retornar um objeto `RagResponse`.
```

### Per task pseudocode as needed added to each task
```python
# Task 4: Pseudocódigo para `perform_rag_query` em `src/provida/rag.py`

from .config import get_settings
from .models import RagResponse
# from google.generativeai.async import GenerativeModel # Exemplo de import

async def perform_rag_query(query: str) -> RagResponse:
    # PATTERN: Carregar configurações no início da função.
    settings = get_settings()

    # 1. Conectar ao Vector DB (a ser implementado)
    # vector_db_client = await get_vector_db_client() # Exemplo
    # relevant_chunks = await vector_db_client.search(query, top_k=5)

    # Mock inicial para desenvolvimento
    relevant_chunks = [
        {"source": "Artigo_A.pdf", "text": "A gastrectomia vertical é eficaz..."},
        {"source": "Artigo_B.pdf", "text": "Complicações incluem fístulas..."}
    ]

    # 2. Preparar o prompt para o LLM
    prompt = f"""
    Com base nos seguintes trechos de documentos, responda à pergunta do usuário.
    Pergunta: {query}

    Documentos:
    {''.join([chunk['text'] for chunk in relevant_chunks])}

    Resposta:
    """

    # 3. Chamar o LLM
    # CRITICAL: Usar o modelo definido nas configurações para o modo RAG.
    # llm = GenerativeModel(settings.llm.rag_model)
    # response = await llm.generate_content_async(prompt)

    # Mock da resposta do LLM
    llm_summary = "A gastrectomia vertical é um procedimento eficaz, mas com riscos de complicações como fístulas."

    # 4. Formatar a resposta
    # PATTERN: Usar os modelos Pydantic para estruturar a saída.
    return RagResponse(
        summary=llm_summary,
        sources=[chunk['source'] for chunk in relevant_chunks]
    )
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Rode estes PRIMEIRO - corrija qualquer erro antes de prosseguir
ruff check src/ --fix
mypy src/
# Expected: Sem erros. Se houver, LEIA o erro e corrija o código.
```

### Level 2: Unit Tests
```python
# CREATE tests/test_rag.py com estes casos de teste:
import pytest
from src.provida.rag import perform_rag_query
from src.provida.models import RagResponse

@pytest.mark.asyncio
async def test_perform_rag_query_happy_path():
    """Testa o fluxo básico do `perform_rag_query` com mocks."""
    # Arrange (com mocks para o DB e LLM)
    query = "O que é gastrectomia vertical?"

    # Act
    result = await perform_rag_query(query)

    # Assert
    assert isinstance(result, RagResponse)
    assert "gastrectomia" in result.summary.lower()
    assert len(result.sources) > 0
```

```bash
# Rode e itere até passar:
pytest tests/
# Se falhar: Leia o erro, entenda a causa, corrija o código, rode novamente.
```

### Level 3: Integration Test (CLI)
```bash
# Teste o comando do CLI diretamente
python -m src.provida.cli rapida "qual o tratamento para obesidade?"

# Expected: Uma resposta resumida impressa no console, seguida pelas fontes.
# If error: Use logs e debugging para encontrar a falha no fluxo.
```

## Final validation Checklist
- [ ] Todos os testes passam: `pytest tests/`
- [ ] Sem erros de linting: `ruff check src/`
- [ ] Sem erros de tipo: `mypy src/`
- [ ] Teste manual do CLI bem-sucedido.
- [ ] Casos de erro (e.g., query vazia) são tratados graciosamente.
- [ ] Logs são informativos, mas não excessivamente verbosos.
- [ ] O código está alinhado com `provida.md`.

---

## Anti-Patterns to Avoid
- ❌ **NÃO** crie novos padrões de código quando já existem exemplos no projeto.
- ❌ **NÃO** pule a validação de entrada (e.g., queries vazias) porque "deveria funcionar".
- ❌ **NÃO** ignore testes falhando. Corrija a causa raiz no código, não no teste.
- ❌ **NÃO** misture código síncrono e assíncrono de forma inadequada. Use `await` corretamente.
- ❌ **NÃO** hardcode valores que devem vir de configuração (nomes de modelos, chaves de API, timeouts).
- ❌ **NÃO** use `except Exception:`. Capture exceções específicas (`ValueError`, `HTTPError`, etc.).