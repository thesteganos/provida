# Tarefas de Desenvolvimento do Projeto Pró-Vida

Este arquivo descreve as tarefas de desenvolvimento para o projeto Pró-Vida, divididas em fases lógicas de implementação.

## Fase 1: Fundação e Estrutura Básica (MVP)

- [x] **1.1: Configuração do Ambiente de Desenvolvimento**
  - [x] Definir a estrutura de diretórios do projeto.
  - [x] Criar e configurar o ambiente virtual (`venv`).
  - [x] Instalar dependências iniciais (`requirements.txt`).
  - [x] Configurar o `docker-compose.yml` para os serviços (Neo4j, MinIO).

- [x] **1.2: CLI Básica e Modos de Operação**
  - [x] Implementar a estrutura da CLI com `argparse`.
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

- [ ] **4.1: Agente Curador de Conhecimento**
  - [ ] Implementar o `KnowledgeCurationAgent`.
  - [ ] Implementar a lógica para atualização autônoma do grafo de conhecimento.

- [ ] **4.2: Agendamento de Tarefas**
  - [ ] Implementar o agendamento de tarefas com `APScheduler` ou similar.
  - [ ] Configurar a execução diária da curadoria de conhecimento.

- [ ] **4.3: Logging e Diário de Bordo**
  - [ ] Implementar um sistema de logging para registrar as ações do sistema.
  - [ ] Criar o arquivo `system_log.txt` com os registros das decisões autônomas.

## Fase 5: Interface do Usuário e Funcionalidades Adicionais

- [ ] **5.1: Melhorias na CLI**
  - [ ] Adicionar opções para configurar limites de busca, níveis de detalhe, etc.
  - [ ] Melhorar a apresentação dos resultados na CLI.

- [ ] **5.2: Agente de Feedback**
  - [ ] Implementar o `FeedbackAgent`.
  - [ ] Coletar feedback estruturado do usuário para refinar a memória dos agentes.

- [ ] **5.3: Exportação de Relatórios**
  - [ ] Implementar a exportação de relatórios para PDF, DOCX e Markdown.
