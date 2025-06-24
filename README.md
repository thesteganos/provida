# PROVIDA: Ecossistema de IA para Gestão Metabólica

**PROVIDA** é um Sistema de Apoio à Decisão Clínica (SADC) de última geração, projetado para auxiliar profissionais de saúde no manejo de sobrepeso, obesidade e comorbidades metabólicas. A aplicação utiliza uma arquitetura de Sistema Multi-Agente (MAS) orquestrada com LangGraph, fundamentada em uma base de conhecimento híbrida que combina Grafos de Conhecimento (Neo4j) e Geração Aumentada por Recuperação (RAG).

O sistema é proativo e auto-evolutivo, com um agente de pesquisa autônomo que busca e ingere novas evidências científicas, e um fluxo de trabalho que permite aos clínicos atuarem como curadores ativos do conhecimento da IA.

## ✨ Funcionalidades Principais

-   **Arquitetura Multi-Agente:** Agentes especializados para anamnese, diagnóstico, planejamento terapêutico, verificação de qualidade e pesquisa.
-   **Base de Conhecimento Híbrida:** Integra dados estruturados (Neo4j) com conhecimento textual de diretrizes e artigos científicos (RAG com FAISS).
-   **Raciocínio Baseado em Evidências:** Cada recomendação gerada é fundamentada em fontes de conhecimento verificáveis para mitigar alucinações.
-   **Fluxo de Trabalho com Auto-Correção:** Um ciclo de verificação e replanejamento garante a qualidade e a segurança dos planos terapêuticos.
-   **Configuração Centralizada:** Um arquivo `config.yaml` permite a fácil troca de modelos de LLM, embeddings e outros hiperparâmetros sem alterar o código.
-   **Portal de Conhecimento do Clínico:** Endpoints de API para que os profissionais possam pesquisar a base de conhecimento e fazer upload de novos documentos.
-   **Agente de Pesquisa Autônomo:** Um worker agendado que busca proativamente por novos artigos no PubMed com base em temas de interesse, mantendo o sistema sempre atualizado.
-   **Deduplicação Inteligente:** Um sistema de duas camadas (hash de conteúdo + similaridade semântica) previne a ingestão de conhecimento redundante.

## 🛠️ Pilha de Tecnologia

-   **Orquestração de Agentes:** LangChain & LangGraph
-   **Modelos de Linguagem:** Google Gemini (configurável)
-   **Embeddings:** Sentence-Transformers (local) ou APIs (configurável)
-   **Grafo de Conhecimento:** Neo4j
-   **Banco de Dados Vetorial (RAG):** FAISS
-   **API:** FastAPI
-   **Agendamento de Tarefas:** Schedule

## 🚀 Guia de Instalação e Execução

### Pré-requisitos

-   Python 3.9+
-   Uma instância do [Neo4j](https://neo4j.com/download/) rodando.
-   Git

### 1. Clonar o Repositório

```bash
git clone https://github.com/SEU_USUARIO/provida-app.git
cd provida-app
```

### 2. Configurar o Ambiente

Primeiro, instale todas as dependências necessárias:

```bash
pip install -r requirements.txt```

Em seguida, configure suas credenciais. Renomeie o arquivo `.env.example` para `.env` (se você criar um) ou crie um novo arquivo `.env` e preencha com suas chaves:

```ini
# .env
GOOGLE_API_KEY="SUA_CHAVE_API_DO_GOOGLE_AI_STUDIO"
NEO4J_URI="bolt://localhost:7687"
NEO4J_USERNAME="neo4j"
NEO4J_PASSWORD="SUA_SENHA_NEO4J"
```

### 3. Configurar a Aplicação

Abra o arquivo `config.yaml` para ajustar os modelos, temas de interesse e outros parâmetros conforme sua necessidade.

### 4. Inicializar a Base de Conhecimento

Antes de rodar a aplicação pela primeira vez, você precisa popular o Grafo de Conhecimento com os dados médicos iniciais.

```bash
python populate_db.py --populate
```

O banco de dados vetorial para RAG será criado automaticamente na primeira vez que a aplicação principal (`main.py`) ou o worker (`research_worker.py`) for iniciado, com base nos arquivos encontrados no diretório `knowledge_sources/`.

### 5. Executar a Aplicação

A aplicação consiste em dois processos principais que devem ser executados em terminais separados:

**Terminal 1: Iniciar a API Principal**

```bash
uvicorn main:app --reload
```

A API estará disponível em `http://127.0.0.1:8000`. A documentação interativa (Swagger UI) pode ser acessada em `http://127.0.0.1:8000/docs`.

**Terminal 2: Iniciar o Agente de Pesquisa Autônomo**

```bash
python research_worker.py
```

Este agente realizará uma busca inicial e depois entrará em um ciclo agendado conforme definido no `config.yaml`.

### 🚨 Resetando o Ambiente

Se precisar limpar todos os dados (Neo4j, FAISS, logs) para começar do zero, use o script de reset. **Atenção: esta ação é irreversível.**

```bash
python reset_environment.py --yes-i-am-sure
```

Após o reset, lembre-se de repopular o KG com `python populate_db.py --populate`.

## 🤝 Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir uma *issue* para relatar bugs ou sugerir novas funcionalidades. Para contribuir com código, por favor, abra um *Pull Request*.
