# Provida Project

## Overview
Provida is an advanced AI research assistant specifically designed for bariatric surgeons. It provides evidence-based answers and conducts deep research using a multi-agent architecture, integrating various LLMs (Gemini 2.5 family), knowledge graphs (Neo4j), vector databases (ChromaDB), and external search tools (Brave Search, PubMed). All searches são voltadas à cirurgia bariátrica e ao tratamento da obesidade, mas é possível liberar outros assuntos passando `allowed_topics` para a função de busca.

**Key Features:**
- **Rapid Query (RAG Mode):** Quick, evidence-based answers from existing knowledge.
- **Deep Research Mode:** Comprehensive, multi-step investigations orchestrated by LangGraph.
- **Intelligent Agents:** Specialized agents for planning, analysis, synthesis, and fact-checking.
- **Data Management:** Secure storage (MinIO S3) and structured knowledge representation (Neo4j, ChromaDB).
- **Flexible LLM Configuration:** Dynamic allocation of Gemini models (Pro, Flash, Flash-Lite) for different tasks.

## Installation

### Prerequisites
- Docker and Docker Compose (recommended for easy setup of all services)
- Python 3.10 or higher (if running without Docker)

### Steps

**1. Clone the repository:**
```bash
git clone https://github.com/your-repo/provida.git # Replace with actual repo URL
cd provida
```

**2. Setup Environment Variables:**
Copy the example environment file and populate it with your credentials. This is crucial for the application and Docker services.
```bash
cp .env.example .env
```
Edit the newly created `.env` file and fill in the placeholder values:

```plaintext
# Credenciais para o Google Gemini
GOOGLE_API_KEY=SUA_CHAVE_API_DO_GOOGLE_AQUI

# --- Credenciais para os Serviços Docker ---
# Estas senhas são usadas pelo docker-compose para inicializar os serviços.
NEO4J_PASSWORD=senha_super_segura_para_neo4j # Choose a strong password
MINIO_ACCESS_KEY=minioadmin # Keep default or change
MINIO_SECRET_KEY=minio_senha_super_segura # Choose a strong password

# --- Configurações da Aplicação (lidas pelo Pydantic) ---
# Use o delimitador duplo underscore (__) para estruturas aninhadas.
# Os valores de URI, host, etc., já estão configurados no docker-compose.yml para apontar para os serviços corretos.

# Configurações do Neo4j para o Grafo de Conhecimento
DATABASE__NEO4J_KNOWLEDGE__URI=bolt://neo4j:7687
DATABASE__NEO4J_KNOWLEDGE__USER=neo4j
DATABASE__NEO4J_KNOWLEDGE__PASSWORD=${NEO4J_PASSWORD}
DATABASE__NEO4J_KNOWLEDGE__DATABASE=provida-knowledge

# Configurações do Neo4j para a Memória dos Agentes
DATABASE__NEO4J_MEMORY_AGENTS__URI=bolt://neo4j:7687
DATABASE__NEO4J_MEMORY_AGENTS__USER=neo4j
DATABASE__NEO4J_MEMORY_AGENTS__PASSWORD=${NEO4J_PASSWORD}
DATABASE__NEO4J_MEMORY_AGENTS__DATABASE=provida-memory

# Brave Search API Key (for general web search)
BRAVE_API_KEY=SUA_CHAVE_API_DO_BRAVE_AQUI

# Entrez PubMed API Key and Email (for academic search)
ENTREZ_EMAIL=seu_email@example.com
ENTREZ_API_KEY=SUA_CHAVE_API_DO_ENTREZ_AQUI
```

These keys enable the integrated search tools. `BRAVE_API_KEY` is required for
Brave Search queries, while `ENTREZ_EMAIL` and `ENTREZ_API_KEY` are used for
PubMed searches. Without these values the related features will be disabled.

**3. Start Services with Docker Compose (Recommended):**
This will build the application image and start all required services (Neo4j, MinIO, ChromaDB).
```bash
docker-compose up -d
```

**4. (Optional) Manual Python Environment Setup:**
If you prefer to run the Python application directly (e.g., for development without Docker services):
```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
```

## Usage

The `Provida` application is primarily interacted with via its Command Line Interface (CLI).

**To run the CLI (from the project root):**
```bash
python -m src.app.cli
```

### Rapid Query Mode (`rapida`)
Get quick, evidence-based answers from the existing knowledge base.

```bash
python -m src.app.cli rapida "qual a dose recomendada de vitamina D para adultos?"
```

**Output Formats:**
By default, output is formatted for readability. You can request JSON output for programmatic use:
```bash
python -m src.app.cli rapida "efeitos colaterais da gastrectomia vertical" --output-format json
```

### Deep Research Mode (`profunda`)
Initiate a comprehensive, multi-step research process on a given topic.

```bash
python -m src.app.cli profunda "novas abordagens cirúrgicas para obesidade mórbida"
```

**Output Formats:**
Similar to `rapida`, you can get JSON output:
```bash
python -m src.app.cli profunda "impacto da cirurgia bariátrica na saúde metabólica" --output-format json
```

## Project Structure

- `src/app/agents/`: Specialized AI agents (planning, analysis, synthesis, memory, etc.).
- `src/app/tools/`: External integrations (Brave Search, PubMed) and utility functions.
- `src/app/core/`: Core infrastructure services (LLM provider, MinIO, ChromaDB).
- `src/app/cli.py`: The main Command Line Interface entry point.
- `src/app/rag.py`: Implementation of the Retrieval-Augmented Generation (RAG) logic.
- `src/app/orchestrator_graph.py`: Defines the deep research workflow using LangGraph.
- `config.yaml`: Centralized configuration for LLM models and services.
- `tests/`: Unit and integration tests for various modules.
- `use-cases/`: Contains context engineering templates for other projects (not part of the core Provida application).
- `docs/`: Additional documentation such as [`rules.md`](docs/rules.md) and search tool information.

## Dependencies
All project dependencies are listed in `requirements.txt`.

## Contributing
Contributions are welcome! Please read the [CONTRIBUTING.md](CONTRIBUTING.md) file for guidelines on how to contribute to the project.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.