# **Pró-Vida: Assistente de Pesquisa Autônomo**

### **Sobre o Projeto**

O "Pró-Vida" é um ecossistema de IA e um assistente de pesquisa autônomo projetado para cirurgiões bariátricos. Ele utiliza uma arquitetura de múltiplos agentes, orquestrada pelo LangGraph e potencializada pela família de modelos Gemini 2.5, para realizar pesquisas aprofundadas, analisar e classificar evidências científicas, e manter uma base de conhecimento que evolui continuamente.

Para uma visão completa do escopo do projeto, consulte o arquivo [PROJETO_PRO-VIDA_ESCOPO_FINAL.md](PROJETO_PRO-VIDA_ESCOPO_FINAL.md).

### **Features**

* **Modos de Operação Duplos:** "Consulta Rápida" (RAG) para respostas imediatas e "Pesquisa Profunda" para investigações exaustivas.
* **Arquitetura Multiagente:** Agentes especializados para busca, análise, tradução, resumo e curadoria de dados.
* **Engenharia de Contexto:** Prompts robustos e detalhados para garantir respostas precisas e estruturadas.
* **Memória Agentica Persistente:** Cada agente aprende e evolui com o tempo, armazenando suas experiências em um banco de dados de grafo Neo4j dedicado.
* **Arquitetura de Dados Quádrupla:** Utiliza MinIO S3, Vector DB, Neo4j para conhecimento e Neo4j para memória.
* **Autonomia Configurável:** Tarefas de atualização e curadoria de conhecimento podem ser agendadas e personalizadas pelo usuário.
* **Configuração Flexível de LLMs:** Permite a troca de modelos e provedores de IA através de um arquivo de configuração central.

### **Arquitetura Tecnológica**

* **Backend/Lógica de IA:** Python 3.10+
* **Framework de Agentes:** Google ADK, LangGraph
* **LLMs:** Família Google Gemini 2.5 (configurável)
* **Bancos de Dados:** Neo4j, ChromaDB (ou similar), MinIO S3
* **Interface:** Aplicação de Linha de Comando (CLI)

Para mais detalhes sobre a arquitetura, consulte o [Documento de Arquitetura](Documentos%20de%20Suporte%20.md#architecture.md).

### **Primeiros Passos**

#### **Pré-requisitos**

* Python 3.10 ou superior
* Docker e Docker Compose
* Conta na Google AI Platform com acesso aos modelos Gemini

#### **Instalação**

1. **Clone o repositório:**
   ```bash
   git clone <URL_DO_REPOSITORIO>
   cd PROJETO_PRO-VIDA
   ```

2. **Crie e ative um ambiente virtual:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # No Windows: venv\Scripts\activate
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure as variáveis de ambiente:**
   - Copie o arquivo de exemplo: `cp .env.example .env`
   - Edite o arquivo `.env` e adicione suas chaves de API e credenciais.

   O arquivo `config.yaml` suporta variáveis no formato `${VAR}`. Ao carregar as
   configurações, esses padrões são substituídos pelos valores das variáveis de
   ambiente correspondentes. Por exemplo, defina `NEO4J_PASSWORD` no `.env` para
   preencher `services.neo4j_knowledge.password`.

5. **Inicie os serviços de backend (Neo4j, MinIO):**
   ```bash
   docker-compose up -d
   ```

### **Uso**

A aplicação é controlada via linha de comando.

* **Para uma Consulta Rápida:**
  ```bash
  python src/main.py --mode fast-query --query "Quais as complicações da gastrectomia vertical?"
  ```

* **Para iniciar uma Pesquisa Profunda:**
  ```bash
  python src/main.py --mode deep-research --topic "Impacto da apneia do sono nos resultados da cirurgia bariátrica"
  ```

### **Engenharia de Prompts**

A qualidade das respostas do sistema depende diretamente da qualidade dos prompts. Para mais detalhes sobre a engenharia de prompts utilizada, consulte o [Documento de Prompts](Documentos%20de%20Suporte%20.md#prompts.md).

