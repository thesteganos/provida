# **Pró-Vida: Assistente de Pesquisa Autônomo**

## **Sobre o Projeto**

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

## **Primeiros Passos (Instalação e Uso)**

#### **Pré-requisitos**

* Docker e Docker Compose
* Conta na Google AI Platform com acesso aos modelos Gemini

#### **Instalação com Docker (Método Recomendado)**

O método recomendado para executar o projeto é usando Docker, que garante um ambiente consistente e isolado para todos os serviços.

1. **Clone o repositório:**
   ```bash
   git clone <URL_DO_REPOSITORIO>
   cd provida
   ```

2. **Configure as variáveis de ambiente:**
   - Copie o arquivo de exemplo: `cp .env.example .env`.
   - Edite o arquivo `.env` e adicione suas chaves de API.
     - `GOOGLE_API_KEY`: Obrigatória para a comunicação com os modelos Gemini.
     - `BRAVE_API_KEY`: Necessária para a ferramenta de busca na web.
     - `ENTREZ_EMAIL`: Obrigatória para usar a API do PubMed.
     - `ENTREZ_API_KEY`: Opcional, mas recomendada para a API do PubMed.
   ```bash
   cp .env.example .env
   ```

3. **Inicie todos os serviços:**
   - Este comando irá construir a imagem da aplicação e iniciar todos os contêineres (Aplicação, Neo4j, MinIO, ChromaDB) em segundo plano. O script `setup.sh` criará o bucket no MinIO automaticamente.
   ```bash
   docker-compose up --build -d
   ```

### **Uso**

A aplicação é controlada via linha de comando, executada de dentro do contêiner da aplicação.

1. **Acesse o shell do contêiner:**
   ```bash
   docker-compose exec provida-app bash
   ```

2. **Execute os comandos:**
   - Uma vez dentro do contêiner, você pode usar a CLI do Pró-Vida.

   * **Para uma Consulta Rápida:**
     ```bash
     python src/app/cli.py rapida "Quais as complicações da gastrectomia vertical?"
     ```

   * **Para iniciar uma Pesquisa Profunda:**
     ```bash
     python src/app/cli.py profunda "Impacto da apneia do sono nos resultados da cirurgia bariátrica"
     ```
