# Tarefas de Desenvolvimento do Projeto Pró-Vida

Este arquivo descreve as tarefas de desenvolvimento para o projeto Pró-Vida, divididas em fases lógicas de implementação.

## Fase 1: Fundação e Estrutura Básica (MVP)

- [x] **1.1: Configuração do Ambiente de Desenvolvimento**
  - [x] Definir a estrutura de diretórios do projeto.
  - [x] Criar e configurar o ambiente virtual (`venv`).
  - [x] Instalar dependências iniciais (`requirements.txt`).
  - [x] Configurar o `docker-compose.yml` para os serviços (Neo4j, MinIO).

- [x] **1.2: CLI Básica e Modos de Operação**
  - [x] Implementar a estrutura da CLI com `argparse` (Implementado com `Typer`).
  - [x] Criar os pontos de entrada para os modos `fast-query` e `deep-research`.

- [x] **1.3: Agente de Pesquisa Simples**
  - [x] Criar um `ResearchAgent` básico.
  - [x] Implementar uma ferramenta de busca na web (`web_search`).

- [x] **1.4: Orquestrador Simples**
  - [x] Criar um `DeepResearchOrchestrator` básico.
  - [x] Integrar o `ResearchAgent` no orquestrador.

## Fase 2: Integração com LLMs e Gerenciamento de Dados

- [x] **2.1: Módulo de Provedor de LLM**
  - [x] Criar um `LLMProvider` para interagir com a API do Gemini.
  - [x] Carregar a chave de API de forma segura a partir de variáveis de ambiente.

- [x] **2.2: Configuração de Modelos**
  - [x] Implementar a leitura do `config.yaml` para alocação de modelos.
  - [x] Permitir a seleção de modelos diferentes para cada agente/tarefa.

- [x] **2.3: Integração com MinIO S3**
  - [x] Criar um módulo para interagir com o MinIO.
  - [x] Implementar funções para upload e download de arquivos.

- [x] **2.4: Integração com Vector DB (ChromaDB)**
  - [x] Configurar o ChromaDB.
  - [x] Implementar funções para adicionar e buscar vetores.

- [x] **2.5: Integração de Ferramentas de Busca Reais**
  - [x] Implementar a integração com a Brave Search API para pesquisa web geral.
  - [x] Implementar a integração com a Entrez PubMed API para pesquisa acadêmica.
  - [x] Atualizar a ferramenta `web_search` para utilizar essas APIs.

## Fase 3: Agentes Avançados e Workflow de Pesquisa Profunda

- [x] **3.1: Agente de Planejamento e Simulação**
  - [x] Implementar o `PlanningAgent`.
  - [x] Gerar um plano de pesquisa detalhado a partir de um tópico.
  - [x] Estimar os recursos necessários (custo/tempo).

- [x] **3.2: Agente de Análise e Classificação**
  - [x] Implementar o `AnalysisAgent`.
  - [x] Classificar a informação por níveis de evidência (A, B, C, D, E).

- [x] **3.3: Agente de Síntese e Citação**
  - [x] Implementar o `SynthesisAgent`.
  - [x] Gerar resumos com citações no nível da frase.

- [x] **3.4: Orquestração com LangGraph**
  - [x] Implementar o workflow de pesquisa profunda com LangGraph.
  - [x] Orquestrar os agentes nas fases de planejamento, execução, análise e síntese.

## Fase 4: Autonomia e Manutenção

- [x] **4.1: Agente Curador de Conhecimento**
  - [x] **4.1.1:** Implementar o `KnowledgeCurationAgent` (nova classe/módulo).
  - [x] **4.1.2:** Implementar a lógica para atualização autônoma do grafo de conhecimento dentro do `KnowledgeCurationAgent`.

- [ ] **4.2: Agendamento de Tarefas**
  - [x] **4.2.1:** Implementar o agendamento de tarefas com `APScheduler` ou similar.
  - [x] **4.2.2:** Configurar a execução diária da curadoria de conhecimento usando o agendador.

- [x] **4.3: Logging e Diário de Bordo**
  - [x] **4.3.1:** Aprimorar o sistema de logging para registrar todas as ações significativas do sistema.
  - [x] **4.3.2:** Criar e gerenciar o arquivo `system_log.txt` com os registros das decisões autônomas do `KnowledgeCurationAgent`.

## Fase 5: Interface do Usuário e Funcionalidades Adicionais

- [ ] **5.1: Melhorias na CLI**
  - [x] **5.1.1:** Adicionar opções na CLI para configurar limites de busca para o modo "Pesquisa Profunda".
  - [x] **5.1.2:** Adicionar opções na CLI para selecionar níveis de detalhe para resumos em 'Consultas Rápidas'.
  - [x] **5.1.3:** Melhorar a apresentação dos resultados na CLI (ex: paginação, filtros).

- [ ] **5.2: Agente de Feedback**
  - [x] **5.2.1:** Implementar o `FeedbackAgent` (nova classe/módulo).
  - [x] **5.2.2:** Coletar feedback estruturado do usuário para refinar a memória dos agentes.

- [ ] **5.3: Exportação de Relatórios**
  - [x] **5.3.1:** Implementar a exportação de relatórios para PDF.
  - [x] **5.3.2:** Implementar a exportação de relatórios para DOCX.
  - [x] **5.3.3:** Implementar a exportação de relatórios para Markdown.

- [x] **5.4: Configurações de Pesquisa (UI/CLI)**
  - [x] **5.4.1:** Implementar interface (CLI ou UI) para ajustar o limite de buscas para o modo "Pesquisa Profunda".

- [ ] **5.5: Configurações de Automação (UI/CLI)**
  - [ ] **5.5.1:** Implementar interface (CLI ou UI) para ativar/desativar e configurar o agendamento da tarefa autônoma.

- [ ] **5.6: Configurações de Relatório (UI/CLI)**
  - [x] **5.6.1:** Implementar interface (CLI ou UI) para selecionar o formato de exportação padrão (PDF, DOCX, Markdown).

- [ ] **5.7: Configurações de Modelos (LLM) (UI/CLI)**
  - [ ] **5.7.1:** Implementar interface (CLI ou UI) para visualizar qual modelo está alocado para cada tarefa principal do sistema.
  - [ ] **5.7.2:** Implementar interface (CLI ou UI) para alterar qual modelo está alocado para cada tarefa principal do sistema.
  - [ ] **5.7.3:** Implementar interface (CLI ou UI) para atualizar a chave de API de forma segura.

## Fase 6: Melhorias de Código e Testes

- [ ] **6.1: Estrutura de Código e Modularidade**
  - [ ] **6.1.1:** Garantir que nenhum arquivo ultrapasse 500 linhas de código (refatorar se necessário).
  - [x] **6.1.2:** Organizar o código em módulos separados por funcionalidade ou responsabilidade.
  - [ ] **6.1.3:** **Consolidar Duplicação de Código:**
    - [ ] **6.1.3.1:** Unificar `ResearchAgent` e `web_search` entre `src/app/` e `src/pro_vida/`.
    - [ ] **6.1.3.2:** Padronizar o carregamento de configurações, removendo duplicações (`src/core/llm_provider.py` vs `src/app/core/llm_provider.py`, `config_models.py` vs `src/pro_vida/config/settings.py`).
    - [ ] **6.1.3.3:** Resolver a duplicação das aplicações frontend (`backend/frontend/` e `user-interface/`).
  - [ ] **6.1.4:** Mover `neo4j_manager.py` para `src/app/core/db/` para consistência na estrutura de diretórios.

- [ ] **6.2: Testes e Confiabilidade**
  - [ ] **6.2.1:** Criar testes unitários para novas funcionalidades.
  - [ ] **6.2.2:** Atualizar testes existentes conforme necessário.
  - [ ] **6.2.3:** **Completar Testes Pendentes:**
    - [x] **6.2.3.1:** Implementar testes para `test_cli.py`.
    - [x] **6.2.3.2:** Implementar testes para `test_rag.py`.
  - [ ] **6.2.4:** Expandir a cobertura de testes unitários para todas as funcionalidades novas e existentes.

- [ ] **6.3: Estilo e Convenções**
  - [ ] **6.3.1:** Seguir PEP8, usar type hints e formatar com `black`.
  - [x] **6.3.2:** Usar `pydantic` para validação de dados.
  - [ ] **6.3.3:** Escrever docstrings para todas as funções usando o estilo Google.
  - [ ] **6.3.4:** Adicionar comentários `# Reason:` para explicar a lógica complexa.

- [ ] **6.4: Documentação e Explicabilidade**
  - [x] **6.4.1:** Atualizar `README.md` com novas funcionalidades, alterações de dependências ou etapas de setup.
  - [ ] **6.4.2:** Comentar código não óbvio e garantir que tudo seja compreensível para um desenvolvedor médio.
  - [ ] **6.4.3:** **Melhorar Gerenciamento de Prompts:**
    - [ ] **6.4.3.1:** Externalizar prompts de LLM para um módulo ou arquivo de configuração dedicado.

## Fase 7: Configuração e Instalação

- [ ] **7.1: Configuração de Variáveis de Ambiente**
  - [ ] **7.1.1:** Configurar as variáveis de ambiente necessárias (`GOOGLE_API_KEY`, `BRAVE_API_KEY`, `ENTREZ_EMAIL`, `ENTREZ_API_KEY`).
  - [ ] **7.1.2:** Adicionar todas as variáveis de ambiente necessárias ao `.env.example`.

- [ ] **7.2: Instalação com Docker**
  - [ ] **7.2.1:** Garantir que a instalação via Docker funcione corretamente, incluindo a criação do bucket no MinIO.
  - [ ] **7.2.2:** Atualizar `Dockerfile` para iniciar a aplicação de forma adequada para produção, se aplicável, ou adicionar instruções claras para uso em desenvolvimento.
  - [ ] **7.2.3:** Garantir que `setup.sh` utilize `MINIO_BUCKET_NAME` de forma consistente (definir no `.env`).

- [ ] **7.3: Uso da Aplicação**
  - [ ] **7.3.1:** Documentar como usar a CLI do Pró-Vida para consultas rápidas e pesquisas profundas.

- [x] **7.4: Configuração de Modelos de Linguagem (LLM)**
  - [x] Implementar a leitura do `config.yaml` para alocação de modelos.
  - [x] Permitir a seleção de modelos diferentes para cada agente/tarefa.

- [ ] **7.5: Detecção de Idioma e Tradução**
  - [ ] **7.5.1:** Implementar a detecção de idioma e tradução de textos não em português usando o modelo Gemini 2.5 Flash-Lite.

- [ ] **7.6: Interface do Usuário**
  - [ ] **7.6.1:** Criar um painel de controle para visualização de dados, exploração do grafo e acesso aos PDFs originais.

- [ ] **7.7: Autonomia Controlada**
  - [ ] **7.7.1:** Implementar processos de Bootstrapping, Atualização Diária e Revisão Trimestral usando uma combinação de modelos Flash e Pro.

- [ ] **7.8: Aprimorar LLM Embedding:**
  - [ ] **7.8.1:** Substituir a função de embedding placeholder (`SentenceTransformerEmbeddingFunction`) em `src/app/core/vector_db.py` por um modelo de embedding mais robusto e apropriado para o projeto (e.g., um modelo Gemini).

---

## Fase 8: Consolidação e Refatoração Arquitetural (Descobertas da Análise Sistemática)

Esta fase aborda problemas críticos de duplicação, inconsistência e melhorias arquiteturais identificadas na análise detalhada do codebase.

### 🔴 Muito Crítico (Impacto Severo na Manutenibilidade, Funcionalidade ou Segurança)

- [x] **8.1: Eliminar Duplicação de Backends e Frontends**
  - [x] **8.1.1:** Remover o diretório `backend/` (incluindo `index.js`, `package.json`, `requirements.txt` e `frontend/`).
    - **Razão:** O projeto é primariamente Python; o backend Node.js é redundante e o frontend aninhado é uma duplicação.
  - [x] **8.1.2:** Remover o diretório `frontend/` (incluindo `src/App.css`, `src/App.js`).
    - **Razão:** Duplicação de aplicação frontend com `user-interface/`.
  - [x] **8.1.3:** Consolidar `user-interface/` como o frontend principal.
    - **Razão:** Garantir uma única fonte de verdade para a interface do usuário.

- [x] **8.2: Consolidar Módulos Python Duplicados**
  - [x] **8.2.1:** Remover o diretório `src/pro_vida/` (incluindo `orchestrator.py`, `models.py`, `automation.py`, `config.py`, `agents/research_agent.py`, `tools/web_search.py`, `tests/`).
    - **Razão:** Duplicação de funcionalidades e estrutura de diretórios com `src/app/`.
  - [x] **8.2.2:** Remover `src/orchestrator.py` (raiz).
    - **Razão:** Duplicação de orquestrador com `src/app/orchestrator.py`.
  - [x] **8.2.3:** Remover `src/settings.py` (raiz).
    - **Razão:** Duplicação de sistema de configuração com `src/app/config/settings.py`.
  - [x] **8.2.4:** Remover `src/app/scheduler.py`.
    - **Razão:** Duplicação de agendador com `src/app/scheduler_service.py`.
  - [x] **8.2.5:** Remover `src/core/llm_provider.py` (raiz).
    - **Razão:** Duplicação de provedor de LLM com `src/app/core/llm_provider.py`.

- [x] **8.3: Eliminar Mocks de Bibliotecas Externas**
  - [x] **8.3.1:** Remover o diretório `langgraph/` (incluindo `graph.py`, `__init__.py`).
    - **Razão:** Implementação mock/duplicada da biblioteca `langgraph` oficial.
  - [x] **8.3.2:** Remover o diretório `google/` (incluindo `generativeai.py`, `__init__.py`).
    - **Razão:** Implementação mock/duplicada da biblioteca `google-generativeai` oficial.

- [x] **8.4: Consolidar Documentação de Escopo**
  - [x] **8.4.1:** Consolidar `provida.md` e `PROJETO_PRO-VIDA_ESCOPO_FINAL.md` em um único documento de arquitetura (ex: `ARCHITECTURE.md` ou `PROJECT_SCOPE.md`).
    - **Razão:** Evitar inconsistências e ter uma única fonte de verdade para a arquitetura do projeto.

- [x] **8.5: Implementar Testes Críticos Ausentes**
  - [x] **8.5.1:** Implementar testes de integração abrangentes para `test_cli.py`.
    - **Razão:** Testes cruciais para a funcionalidade da CLI estão ausentes.
  - [x] **8.5.2:** Implementar testes de unidade abrangentes para `test_rag.py`.
    - **Razão:** Testes cruciais para a lógica central de RAG estão ausentes.

- [x] **8.6: Refatorar Modelos de Configuração Pydantic**
  - [x] **8.6.1:** Refatorar `src/app/config/settings.py` para espelhar a estrutura ideal do `config.yaml` e garantir consistência em `DatabaseSettings`.
    - **Razão:** Inconsistência na estrutura de configuração e duplicação de modelos.
  - [x] **8.6.2:** Remover `config_models.py`.
    - **Razão:** Duplicação de modelos Pydantic de configuração.

- [x] **8.7: Desmockar Funcionalidades Essenciais**
  - [x] **8.7.1:** Desmockar e integrar o `ResearchAgent` em `src/app/agents/knowledge_curation_agent.py`.
    - **Razão:** Funcionalidade central de autonomia está mockada.
  - [x] **8.7.2:** Desmockar o `plan_node` em `src/app/orchestrator_graph.py`.
    - **Razão:** Funcionalidade central de planejamento está mockada.

### 🔴 Crítico (Impacto Significativo na Manutenibilidade, Performance ou Bugs)

- [x] **8.8: Assincronicidade em Ferramentas de Busca**
  - [x] **8.8.1:** Refatorar `src/app/tools/pubmed_search.py` para ser totalmente assíncrono.
    - **Razão:** Chamadas síncronas bloqueiam o loop de eventos assíncrono.
  - [x] **8.8.2:** Refatorar `src/app/tools/web_search.py` para ser totalmente assíncrono.
    - **Razão:** Chamadas síncronas bloqueiam o loop de eventos assíncrono.

- [x] **8.9: Validação de Entrada e Saída com Pydantic**
  - [x] **8.9.1:** Implementar validação Pydantic para entrada e saída em `src/app/agents/feedback_agent.py`.
    - **Razão:** Aumentar robustez e consistência dos dados.
  - [x] **8.9.2:** Implementar validação Pydantic para entrada e saída em `src/app/agents/verification_agent.py`.
    - **Razão:** Aumentar robustez e consistência dos dados.
  - [x] **8.9.3:** Implementar validação Pydantic para entrada e saída em `src/app/agents/claim_extraction_agent.py`.
    - **Razão:** Aumentar robustez e consistência dos dados.
  - [x] **8.9.4:** Implementar validação Pydantic para entrada e saída em `src/app/agents/analysis_agent.py`.
    - **Razão:** Aumentar robustez e consistência dos dados.
  - [ ] **8.9.5:** Implementar validação Pydantic para entrada e saída em `src/app/agents/synthesis_agent.py`.
    - **Razão:** Aumentar robustez e consistência dos dados.
  - [ ] **8.9.6:** Implementar validação Pydantic para entrada em `src/app/agents/knowledge_graph_agent.py`.
    - **Razão:** Aumentar robustez e consistência dos dados.
  - [ ] **8.9.7:** Implementar validação Pydantic para entrada e saída em `fact_checking_service.py`.
    - **Razão:** Aumentar robustez e consistência dos dados.
  - [ ] **8.9.8:** Implementar validação Pydantic para entrada em `src/app/reporting/markdown_exporter.py`, `src/app/reporting/docx_exporter.py`, `src/app/reporting/pdf_exporter.py`.
    - **Razão:** Aumentar robustez e consistência dos dados.

- [ ] **8.10: Tratamento de Erros Robusto**
  - [ ] **8.10.1:** Adicionar tratamento de erros mais robusto nos nós do `langgraph` em `src/app/orchestrator_graph.py`.
    - **Razão:** Evitar que falhas em nós quebrem o workflow completo.
  - [ ] **8.10.2:** Adicionar tratamento de erros na invocação do grafo em `src/app/orchestrator.py`.
    - **Razão:** Capturar e logar falhas na orquestração.
  - [ ] **8.10.3:** Adicionar tratamento de erros na conexão ChromaDB em `src/app/rag.py`.
    - **Razão:** Fornecer feedback adequado em caso de falha de conexão.

- [ ] **8.11: Gerenciamento de Dependências**
  - [ ] **8.11.1:** Fixar as versões de todas as dependências em `requirements.txt`.
    - **Razão:** Garantir reprodutibilidade do ambiente.
  - [ ] **8.11.2:** Verificar e remover redundância de `requests` em `requirements.txt`.
    - **Razão:** Reduzir dependências desnecessárias.

- [ ] **8.12: Configuração do Docker Compose**
  - [ ] **8.12.1:** Adicionar `command` para iniciar a aplicação Python no serviço `provida-app` em `docker-compose.yml`.
    - **Razão:** O contêiner não inicia a aplicação automaticamente.
  - [ ] **8.12.2:** Adicionar `MINIO_BUCKET_NAME` ao `.env.example` e garantir que seja passado corretamente para o serviço `minio-setup` em `docker-compose.yml` e `setup.sh`.
    - **Razão:** Variável crítica para o setup do MinIO está ausente.

- [ ] **8.13: Atualização de Ativos e Metadados do Frontend**
  - [ ] **8.13.1:** Substituir `user-interface/src/logo.svg` pelo logotipo do projeto.
    - **Razão:** Branding e identidade visual.
  - [ ] **8.13.2:** Atualizar `user-interface/public/manifest.json` com metadados do projeto Pró-Vida.
    - **Razão:** Branding e funcionalidade PWA.
  - [ ] **8.13.3:** Substituir `user-interface/public/logo512.png` e `user-interface/public/logo192.png` pelos logotipos do projeto.
    - **Razão:** Branding e identidade visual.
  - [ ] **8.13.4:** Atualizar `user-interface/public/index.html` com título, descrição e `theme-color` do projeto.
    - **Razão:** Branding e SEO.
  - [ ] **8.13.5:** Substituir `user-interface/public/favicon.ico` pelo ícone do projeto.
    - **Razão:** Branding e identidade visual.
  - [ ] **8.13.6:** Atualizar `user-interface/src/App.js` com conteúdo específico do projeto.
    - **Razão:** Funcionalidade central da interface do usuário.
  - [ ] **8.13.7:** Atualizar `user-interface/src/App.css` com estilos do design do projeto.
    - **Razão:** Branding e experiência do usuário.
  - [ ] **8.13.8:** Substituir `user-interface/README.md` por um README específico do projeto.
    - **Razão:** Documentação clara para o frontend.

- [ ] **8.14: Integração das Diretrizes de Prompt no Código**
  - [ ] **8.14.1:** Externalizar prompts de LLM em `src/app/agents/feedback_agent.py`, `src/app/rag.py`, `src/app/agents/planning_agent.py`, `src/app/agents/synthesis_agent.py`, `src/app/agents/claim_extraction_agent.py`, `src/app/agents/analysis_agent.py`.
    - **Razão:** Manutenibilidade, versionamento e aplicação consistente das diretrizes de prompt da Seção 10 do documento de escopo.

- [ ] **8.15: Formalizar Linguagem de Regras**
  - [ ] **8.15.1:** Refatorar `src/app/autonomous_decision_maker.py` para usar uma linguagem de regras mais robusta e escalável (ex: objetos JSON para condições e ações).
    - **Razão:** A implementação atual é frágil e não escalável.
  - [ ] **8.15.2:** Formalizar a linguagem de regras em `src/config/rules.json` (ex: usando um esquema JSON).
    - **Razão:** Garantir consistência e validade das regras.

### 🟡 Prioritário (Melhorias na Qualidade de Código, Robustez ou UX)

- [ ] **8.16: Melhorias na CLI**
  - [ ] **8.16.1:** Robustez do `highlight_keywords` em `src/app/cli.py` (escapar caracteres especiais).
    - **Razão:** Prevenir erros com regex.
  - [ ] **8.16.2:** Geração de nomes de arquivo para relatórios em `src/app/cli.py` (usar "slugification" mais robusta).
    - **Razão:** Robustez na criação de arquivos.

- [ ] **8.17: Robustez na Extração de Dados**
  - [ ] **8.17.1:** Melhorar a robustez na extração de `documents` e `metadatas` em `src/app/rag.py`.
    - **Razão:** Prevenir erros se a estrutura de retorno do ChromaDB mudar.

- [ ] **8.18: Consistência na `ResearchState`**
  - [ ] **8.18.1:** Usar modelos Pydantic para `collected_data`, `analyzed_data`, `final_report` e `verification_report` em `src/app/orchestrator_graph.py` e `src/app/orchestrator.py`.
    - **Razão:** Garantir validação e tipagem forte em todo o workflow.

- [ ] **8.19: Implementar Funcionalidades Pendentes**
  - [ ] **8.19.1:** Implementar `perform_quarterly_review` e `bootstrap_knowledge` em `src/app/agents/knowledge_curation_agent.py`.
    - **Razão:** Completar funcionalidades de autonomia.
  - [ ] **8.19.2:** Implementar interface (CLI ou UI) para ativar/desativar e configurar o agendamento da tarefa autônoma (Fase 5.5.1).
    - **Razão:** Completar funcionalidades de UI.
  - [ ] **8.19.3:** Implementar detecção de idioma e tradução de textos não em português (Fase 7.5.1).
    - **Razão:** Completar funcionalidades de processamento de dados.
  - [ ] **8.19.4:** Criar um painel de controle para visualização de dados, exploração do grafo e acesso aos PDFs originais (Fase 7.6.1).
    - **Razão:** Completar funcionalidades de UI.
  - [ ] **8.19.5:** Implementar processos de Bootstrapping, Atualização Diária e Revisão Trimestral usando combinação de modelos Flash e Pro (Fase 7.7.1).
    - **Razão:** Completar funcionalidades de autonomia.
  - [ ] **8.19.6:** Substituir a função de embedding placeholder em `src/app/core/vector_db.py` por um modelo de embedding mais robusto (Fase 7.8.1).
    - **Razão:** Melhorar a qualidade do embedding.

- [ ] **8.20: Melhorias no Logging**
  - [ ] **8.20.1:** Adicionar tratamento de erros na criação de diretórios/arquivos de log em `src/app/config/logging_config.py`.
    - **Razão:** Robustez na configuração de logging.
  - [ ] **8.20.2:** Integrar `src/app/autonomous_decision_maker.py` com o sistema de logging centralizado.
    - **Razão:** Garantir que decisões autônomas sejam registradas no `system_log.txt`.
  - [ ] **8.20.3:** Detalhamento do "Diário de Bordo" em `PROJETO_PRO-VIDA_ESCOPO_FINAL.md` (ou o documento consolidado).
    - **Razão:** Melhorar a documentação da observabilidade.

- [ ] **8.21: Melhorias na Documentação**
  - [ ] **8.21.1:** Atualizar `README.md` com informações sobre `BRAVE_API_KEY`, `ENTREZ_EMAIL`, `ENTREZ_API_KEY` e criar `CONTRIBUTING.md`.
    - **Razão:** Completar e manter a documentação do projeto.
  - [ ] **8.21.2:** Consistência da documentação do módulo de busca web (`docs/web_search.md`) com a implementação real, detalhes sobre auto-detecção, informações sobre API Keys e formato de retorno.
    - **Razão:** Garantir que a documentação reflita o código.
  - [ ] **8.21.3:** Documentar a linguagem de regras em `src/config/rules.json`.
    - **Razão:** Melhorar a manutenibilidade das regras.

- [ ] **8.22: Otimização de Imagem Docker**
  - [ ] **8.22.1:** Otimizar a camada de dependências no `Dockerfile`.
    - **Razão:** Reduzir o tempo de build e o tamanho da imagem.

- [ ] **8.23: Configuração de Proxy para Desenvolvimento**
  - [ ] **8.23.1:** Adicionar configuração de proxy no `user-interface/package.json` para desenvolvimento.
    - **Razão:** Melhorar a experiência do desenvolvedor.

- [ ] **8.24: Refatorar Componentes Frontend**
  - [ ] **8.24.1:** Refatorar `user-interface/src/App.js` para componentes menores e mais gerenciáveis.
    - **Razão:** Melhorar a manutenibilidade do código frontend.
  - [ ] **8.24.2:** Adotar uma abordagem de estilização consistente em `user-interface/src/App.css`.
    - **Razão:** Melhorar a manutenibilidade do código frontend.

- [ ] **8.25: Testes de Frontend**
  - [ ] **8.25.1:** Atualizar `user-interface/src/App.test.js` para testar conteúdo real e adicionar testes de interação e funcionalidade.
    - **Razão:** Garantir a correção e cobertura dos testes frontend.

- [ ] **8.26: Configuração de Docker Compose**
  - [ ] **8.26.1:** Adicionar `healthcheck` para os serviços `neo4j`, `minio` e `chroma` em `docker-compose.yml`.
    - **Razão:** Aumentar a robustez da inicialização dos serviços.
  - [ ] **8.26.2:** Expor portas para `provida-app` em `docker-compose.yml` se uma API HTTP for implementada.
    - **Razão:** Permitir comunicação externa com o backend Python.

### ⚪ Normal (Melhorias Menores, Limpeza, Considerações de Longo Prazo)

- [ ] **8.27: Limpeza de Código**
  - [ ] **8.27.1:** Remover comentário de logging redundante em `src/main.py`.
    - **Razão:** Limpeza de código.
  - [ ] **8.27.2:** Remover conteúdo não utilizado em `user-interface/src/App.js`.
    - **Razão:** Limpeza de código.
  - [ ] **8.27.3:** Remover `Documentos de Suporte .md` se não for utilizado.
    - **Razão:** Limpeza de repositório.
  - [ ] **8.27.4:** Remover `tasks` da seção `automation` em `config.yaml` se não houver uso dinâmico.
    - **Razão:** Limpeza de configuração.

- [ ] **8.28: Melhorias de Estilo e Convenções**
  - [ ] **8.28.1:** Adicionar docstrings detalhadas para helpers em `src/app/cli.py`.
    - **Razão:** Qualidade de código.
  - [ ] **8.28.2:** Adicionar docstrings detalhadas para exportadores em `src/app/reporting/markdown_exporter.py`, `src/app/reporting/docx_exporter.py`, `src/app/reporting/pdf_exporter.py`.
    - **Razão:** Qualidade de código.
  - [ ] **8.28.3:** Categorizar e adicionar comentários em `requirements.txt`.
    - **Razão:** Legibilidade.
  - [ ] **8.28.4:** Adicionar docstrings detalhadas para `main()` em `src/main.py`.
    - **Razão:** Qualidade de código.
  - [ ] **8.28.5:** Adicionar docstrings detalhadas para `setup_logging()` em `src/app/config/logging_config.py`.
    - **Razão:** Qualidade de código.
  - [ ] **8.28.6:** Adicionar docstrings/comentários para cron jobs em `config.yaml`.
    - **Razão:** Clareza da configuração.
  - [ ] **8.28.7:** Adicionar docstrings detalhadas para `add_job` e `remove_job` em `src/app/scheduler_service.py`.
    - **Razão:** Qualidade de código.
  - [ ] **8.28.8:** Adicionar docstrings e tipagem em `src/app/autonomous_decision_maker.py`.
    - **Razão:** Qualidade de código.
  - [ ] **8.28.9:** Adicionar docstrings e tipagem em `neo4j_manager.py`.
    - **Razão:** Qualidade de código.

- [ ] **8.29: Otimizações Menores**
  - [ ] **8.29.1:** Consistência na reutilização de `maxBytes` e `backupCount` em `src/app/config/logging_config.py`.
    - **Razão:** Clareza da configuração.
  - [ ] **8.29.2:** Logging/saída mais detalhada em `setup.sh`.
    - **Razão:** Observabilidade.
  - [ ] **8.29.3:** Tratamento de erros para `mc` em `setup.sh`.
    - **Razão:** Robustez do script.
  - [ ] **8.29.4:** Versão do Docker Compose em `docker-compose.yml`.
    - **Razão:** Boas práticas.
  - [ ] **8.29.5:** Adicionar `description` em `user-interface/public/manifest.json`.
    - **Razão:** Completude do manifesto PWA.
  - [ ] **8.29.6:** Revisar `start_url` em `user-interface/public/manifest.json`.
    - **Razão:** Completude do manifesto PWA.
  - [ ] **8.29.7:** Adicionar diretiva `Sitemap` em `user-interface/public/robots.txt`.
    - **Razão:** SEO.
  - [ ] **8.29.8:** Escolha do Modelo LLM em `src/app/agents/feedback_agent.py`, `src/app/rag.py`, `src/app/agents/knowledge_curation_agent.py`, `src/app/agents/planning_agent.py`, `src/app/agents/synthesis_agent.py`, `src/app/agents/claim_extraction_agent.py`, `src/app/agents/analysis_agent.py`.
    - **Razão:** Otimização e fine-tuning.
  - [ ] **8.29.9:** Consistência na geração de `sources` em `src/app/rag.py`.
    - **Razão:** Refinamento.
  - [ ] **8.29.10:** Retorno de `knowledge_graph_node` em `src/app/orchestrator_graph.py`.
    - **Razão:** Estilo de código.
  - [ ] **8.29.11:** Remover exemplo de uso em `src/app/autonomous_decision_maker.py`.
    - **Razão:** Limpeza de código.
  - [ ] **8.29.12:** Scripts de Teste Mais Específicos em `user-interface/package.json`.
    - **Razão:** Experiência do desenvolvedor.
  - [ ] **8.29.13:** Remover conteúdo não utilizado em `user-interface/src/App.js`.
    - **Razão:** Limpeza de código.
  - [ ] **8.29.14:** Consistência na Configuração de Cron Jobs em `src/app/scheduler_service.py`.
    - **Razão:** Correção.
