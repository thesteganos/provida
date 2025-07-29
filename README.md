# Provida

Provida é um sistema de inteligência artificial projetado para realizar pesquisas profundas e fornecer respostas rápidas com base em uma base de conhecimento existente.

## Visão Geral
Provida é um assistente de pesquisa avançado de IA especificamente projetado para cirurgiões bariátricos. Ele fornece respostas baseadas em evidências e realiza pesquisas profundas usando uma arquitetura multi-agente, integrando vários LLMs (família Gemini 2.5), grafos de conhecimento (Neo4j), bancos de dados vetoriais (ChromaDB) e ferramentas de pesquisa externas (Brave Search, PubMed). Todas as pesquisas são voltadas para cirurgia bariátrica e tratamento da obesidade, mas é possível liberar outros assuntos passando `allowed_topics` para a função de busca.

**Principais Funcionalidades:**
- **Modo de Consulta Rápida (RAG):** Respostas rápidas baseadas em conhecimento existente.
- **Modo de Pesquisa Profunda:** Pesquisas abrangentes e multietapas orquestradas pelo LangGraph.
- **Agentes Inteligentes:** Agentes especializados para planejamento, análise, síntese e verificação de fatos.
- **Gerenciamento de Dados:** Armazenamento seguro (MinIO S3) e representação estruturada de conhecimento (Neo4j, ChromaDB).
- **Configuração Flexível de LLM:** Alocamento dinâmico de modelos Gemini (Pro, Flash, Flash-Lite) para diferentes tarefas.

## Instalação

### Pré-requisitos
- Docker e Docker Compose (recomendado para configuração fácil de todos os serviços)
- Python 3.10 ou superior (se executar sem Docker)

### Passos

**1. Clone o repositório:**
```bash
git clone https://github.com/seu-repositorio/provida.git # Substitua pelo URL real do repositório
cd provida
```

**2. Configure as Variáveis de Ambiente:**
Copie o arquivo de exemplo de ambiente e preencha-o com suas credenciais. Isso é crucial para o aplicativo e os serviços Docker.
```bash
cp .env.example .env
```
Edite o arquivo `.env` recém-criado e preencha os valores de espaço reservado:

```plaintext
# Credenciais para o Google Gemini
GOOGLE_API_KEY=SUA_CHAVE_API_DO_GOOGLE_AQUI

# --- Credenciais para os Serviços Docker ---
# Essas senhas são usadas pelo docker-compose para inicializar os serviços.
NEO4J_PASSWORD=senha_super_segura_para_neo4j # Escolha uma senha forte
MINIO_ACCESS_KEY=minioadmin # Mantenha o padrão ou altere
MINIO_SECRET_KEY=minio_senha_super_segura # Escolha uma senha forte

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

# Chave de API do Brave Search (para pesquisas na web em geral)
BRAVE_API_KEY=SUA_CHAVE_API_DO_BRAVE_AQUI

# Chave de API e Email do Entrez PubMed (para pesquisas acadêmicas)
ENTREZ_EMAIL=seu_email@example.com
ENTREZ_API_KEY=SUA_CHAVE_API_DO_ENTREZ_AQUI
```

Essas chaves habilitam as ferramentas de pesquisa integradas. `BRAVE_API_KEY` é necessário para
pesquisas do Brave Search, enquanto `ENTREZ_EMAIL` e `ENTREZ_API_KEY` são usados para
pesquisas do PubMed. Sem esses valores, os recursos relacionados serão desabilitados.

**3. Inicie os Serviços com Docker Compose (Recomendado):**
Isso construirá a imagem do aplicativo e iniciará todos os serviços necessários (Neo4j, MinIO, ChromaDB).
```bash
docker-compose up -d
```

**4. (Opcional) Configuração Manual do Ambiente Python:**
Se preferir executar o aplicativo Python diretamente (por exemplo, para desenvolvimento sem serviços Docker):
```bash
python -m venv venv
source venv/bin/activate  # No Windows use `venv\Scripts\activate`
pip install -r requirements.txt
```

## Uso

O aplicativo `Provida` é principalmente interagido através de sua Interface de Linha de Comando (CLI).

**Para executar a CLI (a partir da raiz do projeto):**
```bash
python -m src.app.cli
```

### Modo de Consulta Rápida (`rapida`)
Obtenha respostas rápidas baseadas no banco de conhecimento existente.
```bash
python -m src.app.cli rapida "qual a dose recomendada de vitamina D para adultos?"
```

**Formatos de Saída:**
Por padrão, a saída é formatada para leitura. Você pode solicitar saída JSON para uso programático:
```bash
python -m src.app.cli rapida "efeitos colaterais da gastrectomia vertical" --output-format json
```

### Modo de Pesquisa Profunda (`profunda`)
Inicie um processo de pesquisa abrangente e multietapas sobre um tópico específico.
```bash
python -m src.app.cli profunda "novas abordagens cirúrgicas para obesidade mórbida"
```

**Formatos de Saída:**
Semelhante ao `rapida`, você pode obter saída JSON:
```bash
python -m src.app.cli profunda "impacto da cirurgia bariátrica na saúde metabólica" --output-format json
```

## Estrutura do Projeto

- **`src/app/`**: Contém a lógica principal da aplicação.
  - **`agents/`**: Agentes especializados em diferentes tarefas.
  - **`cli.py`**: Interface de linha de comando principal.
  - **`core/`**: Serviços principais como provedor de LLM, MinIO, ChromaDB, etc.
  - **`orchestrator_graph.py`**: Define o fluxo de trabalho de pesquisa usando LangGraph.
  - **`orchestrator.py`**: Executa o modo de pesquisa profunda e retorna o estado final.
  - **`rag.py`**: Implementação da lógica de Retrieval-Augmented Generation (RAG).
  - **`scheduler_service.py`**: Gerencia a execução de tarefas agendadas.
  - **`tools/`**: Integrações com serviços externos e funções utilitárias.

- **`tests/`**: Testes unitários e de integração para garantir a qualidade do código.

- **`config.yaml`**: Configurações centrais para o aplicativo, incluindo logging e dependências.

- **`docker-compose.yml`**: Configuração para iniciar os serviços necessários usando Docker.

## Contribuição

Contribuições são bem-vindas! Por favor, leia o [CONTRIBUTING.md](CONTRIBUTING.md) para mais detalhes.

## Licença

Este projeto está licenciado sob a [MIT License](LICENSE).