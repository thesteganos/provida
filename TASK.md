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
- [ ] **5.4: Configurações de Pesquisa**
  - [ ] Implementar configurações para ajustar o limite de buscas para o modo "Pesquisa Profunda".
- [ ] **5.5: Configurações de Automação**
  - [ ] Implementar configurações para ativar/desativar e configurar o agendamento da tarefa autônoma.
- [ ] **5.6: Configurações de Relatório**
  - [ ] Implementar configurações para selecionar o formato de exportação padrão (PDF, DOCX, Markdown).
- [ ] **5.7: Configurações de Modelos (LLM)**
  - [ ] Implementar uma interface para visualizar e alterar qual modelo está alocado para cada tarefa principal do sistema.
  - [ ] Implementar um campo para atualizar a chave de API de forma segura.

## Fase 6: Melhorias de Código e Testes

- [ ] **6.1: Estrutura de Código e Modularidade**
  - [ ] Garantir que nenhum arquivo ultrapasse 500 linhas de código.
  - [ ] Organizar o código em módulos separados por funcionalidade ou responsabilidade.
- [ ] **6.2: Testes e Confiabilidade**
  - [ ] Criar testes unitários para novas funcionalidades.
  - [ ] Atualizar testes existentes conforme necessário.
- [ ] **6.3: Estilo e Convenções**
  - [ ] Seguir PEP8, usar type hints e formatar com `black`.
  - [ ] Usar `pydantic` para validação de dados.
  - [ ] Escrever docstrings para todas as funções usando o estilo Google.
- [ ] **6.4: Documentação e Explicabilidade**
  - [ ] Atualizar `README.md` com novas funcionalidades, alterações de dependências ou etapas de setup.
  - [ ] Comentar código não óbvio e garantir que tudo seja compreensível para um desenvolvedor médio.
  - [ ] Adicionar comentários `# Reason:` para explicar a lógica complexa.

## Fase 7: Configuração e Instalação

- [ ] **7.1: Configuração de Variáveis de Ambiente**
  - [ ] Configurar as variáveis de ambiente necessárias (`GOOGLE_API_KEY`, `BRAVE_API_KEY`, `ENTREZ_EMAIL`, `ENTREZ_API_KEY`).
- [ ] **7.2: Instalação com Docker**
  - [ ] Garantir que a instalação via Docker funcione corretamente, incluindo a criação do bucket no MinIO.
- [ ] **7.3: Uso da Aplicação**
  - [ ] Documentar como usar a CLI do Pró-Vida para consultas rápidas e pesquisas profundas.
- [ ] **7.4: Configuração de Modelos de Linguagem (LLM)**
  - [ ] Implementar a leitura do `config.yaml` para alocação de modelos.
  - [ ] Permitir a seleção de modelos diferentes para cada agente/tarefa.
- [ ] **7.5: Detecção de Idioma e Tradução**
  - [ ] Implementar a detecção de idioma e tradução de textos não em português usando o modelo Gemini 2.5 Flash-Lite.
- [ ] **7.6: Interface do Usuário**
  - [ ] Criar um painel de controle para visualização de dados, exploração do grafo e acesso aos PDFs originais.
- [ ] **7.7: Autonomia Controlada**
  - [ ] Implementar processos de Bootstrapping, Atualização Diária e Revisão Trimestral usando uma combinação de modelos Flash e Pro.
