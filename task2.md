# Análise de Código e Propostas de Melhoria

## 1. Visão Geral

Após uma análise sistemática do código-fonte do projeto Pró-Vida, foram identificados diversos pontos para melhoria que visam aumentar a robustez, manutenibilidade e eficiência do sistema. As tarefas abaixo detalham as ações necessárias para implementar essas melhorias.

---

## 2. Lista de Tarefas

### Tarefa 1: Correção de Importação Faltante em `cli.py`

*   **Problema:** O módulo `datetime` é importado localmente dentro da função `deep_research` e no bloco `if __name__ == "__main__":` no arquivo `src/app/cli.py`. Isso viola as convenções de estilo do Python (PEP 8) e pode levar a erros de `NameError` se as funções que dependem dele forem chamadas de outros contextos.
*   **Sugestão de Melhoria:** Mover a importação `import datetime` para o topo do arquivo, junto com as outras importações de bibliotecas padrão. Isso garante que o módulo esteja disponível globalmente no escopo do arquivo.

### Tarefa 2: Implementar Nó de Coleta de Dados no Grafo de Pesquisa

*   **Problema:** O grafo de pesquisa definido em `src/app/orchestrator_graph.py` não possui um nó para executar a coleta de dados, que é uma etapa fundamental do "Modo de Pesquisa Profunda". Atualmente, o `plan_node` apenas inicializa `collected_data` como uma lista vazia.
*   **Sugestão de Melhoria:**
    1.  **Criar `DataCollectionAgent`:** Desenvolver um novo agente em `src/app/agents/data_collection_agent.py` responsável por interagir com as ferramentas de busca (ex: Brave Search, PubMed) e coletar os dados.
    2.  **Implementar `collection_node`:** Adicionar um novo nó assíncrono `collection_node` em `src/app/orchestrator_graph.py` que utilize o `DataCollectionAgent` para buscar informações com base no `research_plan`.
    3.  **Atualizar o Grafo:** Integrar o `collection_node` ao fluxo do LangGraph, posicionando-o após o `plan_node` e antes do `analysis_node`.
    4.  **Atualizar `ResearchState`:** Garantir que o `ResearchState` seja corretamente populado com os `CollectedDataItem` retornados pelo novo nó.

### Tarefa 3: Refatorar Lógica de Exportação de Relatórios

*   **Problema:** A lógica para exportar relatórios nos formatos PDF, DOCX e Markdown está duplicada na função `deep_research` em `src/app/cli.py`. Isso viola o princípio DRY (Don't Repeat Yourself) e dificulta a manutenção.
*   **Sugestão de Melhoria:**
    1.  **Criar Módulo de Utilitários:** Criar um novo arquivo `src/app/reporting/utils.py`.
    2.  **Implementar Função Centralizada:** Desenvolver uma função `export_report_formats` neste novo módulo que receba os dados do relatório e uma lista de formatos desejados (ex: `['pdf', 'docx']`).
    3.  **Refatorar `cli.py`:** Substituir o código duplicado em `src/app/cli.py` por uma única chamada à nova função utilitária, simplificando o corpo da função `deep_research`.

### Tarefa 4: Melhorar o Tratamento de Exceções

*   **Problema:** O código utiliza blocos `except Exception` genéricos em vários locais (`cli.py`, `rag.py`), o que pode mascarar bugs e dificultar o diagnóstico de erros.
*   **Sugestão de Melhoria:**
    *   **Em `rag.py`:** Capturar exceções específicas que a biblioteca `chromadb` pode levantar (ex: `chromadb.errors.ChromaError`).
    *   **Em `cli.py`:** Capturar exceções relacionadas a I/O (ex: `IOError`, `FileNotFoundError`) ao salvar arquivos de configuração ou relatórios.
    *   **Em todos os agentes:** Garantir que as chamadas de API para LLMs tratem exceções específicas da biblioteca do provedor (ex: `google.api_core.exceptions.GoogleAPICallError`).

### Tarefa 5: Externalizar Configurações Codificadas

*   **Problema:** Parâmetros críticos, como o `n_results=5` na função `perform_rag_query` em `src/app/rag.py`, estão codificados diretamente no fonte. Isso limita a flexibilidade e exige alterações no código para ajustes simples.
*   **Sugestão de Melhoria:**
    1.  **Adicionar ao `config.yaml`:** Mover o parâmetro `n_results` para o arquivo `config.yaml` sob uma nova seção, como `rag_settings`.
    2.  **Atualizar `settings.py`:** Adicionar o novo campo ao modelo Pydantic correspondente em `app/config/settings.py`.
    3.  **Utilizar a Configuração:** Modificar a chamada em `src/app/rag.py` para ler o valor a partir do objeto `settings` global.

### Tarefa 6: Remover Arquivo `main.py` Vazio

*   **Problema:** O arquivo `src/app/main.py` está vazio e não é utilizado, uma vez que `src/app/cli.py` serve como o ponto de entrada principal da aplicação.
*   **Sugestão de Melhoria:** Remover o arquivo `src/app/main.py` para limpar a estrutura do projeto e evitar confusão para futuros desenvolvedores.

### Tarefa 7: Documentar o Código

*   **Problema:** Embora a arquitetura esteja bem documentada, o código em si carece de docstrings detalhadas em algumas funções e classes, especialmente nos agentes e nos nós do grafo.
*   **Sugestão de Melhoria:** Adicionar ou aprimorar as docstrings em todos os agentes, nós do grafo e funções principais, explicando seus propósitos, argumentos e valores de retorno, seguindo um padrão consistente (ex: Google Style Docstrings).
