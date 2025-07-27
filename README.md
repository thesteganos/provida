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

**Pré-requisitos para Docker:**

* **Docker:** Versão 20.10.0 ou superior.
* **Docker Compose:** Versão 1.29.0 ou superior.

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

4. **Verifique o status dos contêineres:**
   - Após iniciar os serviços, você pode verificar o status dos contêineres usando o comando:
   ```bash
   docker-compose ps
   ```
   - Certifique-se de que todos os contêineres estejam em execução sem erros.

5. **Acessar os logs dos contêineres:**
   - Se houver problemas durante a inicialização, você pode verificar os logs dos contêineres usando:
   ```bash
   docker-compose logs -f
   ```
   - Isso ajudará a identificar e resolver quaisquer problemas de configuração ou inicialização.

### **Configuração de Variáveis de Ambiente**

Antes de executar a aplicação, é necessário configurar as variáveis de ambiente. Para isso, siga os passos abaixo:

1. **Crie um arquivo `.env`**:
   - Copie o arquivo `env_example_updates.md` para `.env`:
     ```bash
     cp .env.example .env
     ```

2. **Preencha as variáveis de ambiente**:
   - Abra o arquivo `.env` em um editor de texto e preencha as variáveis conforme as instruções abaixo:
     ```env
     # Exemplo de arquivo de variáveis de ambiente.
     # Copie este arquivo para .env e preencha com suas credenciais.
     # NÃO COMITE ESTE ARQUIVO PARA O CONTROLE DE VERSÃO.
     # Este arquivo contém informações sensíveis e deve ser mantido seguro.

     # Chave de API para os modelos do Google Gemini
     GOOGLE_API_KEY=""

     # Credenciais para o banco de dados Neo4j
     NEO4J_URI=""
     NEO4J_USER=""
     NEO4J_PASSWORD=""

     # Credenciais para o MinIO S3
     MINIO_ENDPOINT=""
     MINIO_ADMIN_USER=""
     MINIO_ADMIN_PASSWORD=""

     # Configuração do Vector DB (ChromaDB)
     VECTOR_DB_PATH=""

     # Chave de API para Brave Search (para pesquisa web geral)
     BRAVE_API_KEY=""

     # Chave de API para Entrez PubMed (para pesquisa acadêmica)
     ENTREZ_API_KEY=""
     ENTREZ_EMAIL="" # Endereço de e-mail necessário para algumas APIs Entrez

     # Configurações do ChromaDB (sobrescrevem os padrões se definidas)
     DATABASE__CHROMA__HOST=""
     DATABASE__CHROMA__PORT=""
     DATABASE__CHROMA__COLLECTION=""

     # Exemplo de como sobrescrever um modelo específico
     MODELS__RAG_AGENT=""

     # Configurações de Pesquisa (Google Custom Search API)
     SEARCH_API_KEY=""
     SEARCH_ENDPOINT=""
     ```

3. **Segurança**:
   - **NÃO** comite o arquivo `.env` para o controle de versão. Certifique-se de que ele está listado no arquivo `.gitignore`.
   - Mantenha o arquivo `.env` seguro e não compartilhe suas credenciais com terceiros.

### **Uso**

A aplicação é controlada via linha de comando, executada de dentro do contêiner da aplicação.

1. **Acesse o shell do contêiner:**
   ```bash
   docker-compose exec provida-app bash
   ```

2. **Execute os comandos:**
   - Uma vez dentro do contêiner, você pode usar a CLI do Pró-Vida.

   * **Para uma Consulta Rápida (RAG):**
     ```bash
     python src/app/cli.py rapida "Quais as complicações da gastrectomia vertical?"
     ```
     - Este comando retorna respostas imediatas baseadas em uma pesquisa rápida.

   * **Para iniciar uma Pesquisa Profunda:**
     ```bash
     python src/app/cli.py profunda "Impacto da apneia do sono nos resultados da cirurgia bariátrica"
     ```
     - Este comando realiza uma pesquisa mais aprofundada e retorna resultados mais detalhados.

   * **Para listar todos os comandos disponíveis:**
     ```bash
     python src/app/cli.py --help
     ```
     - Este comando exibe uma lista de todos os comandos disponíveis na CLI, juntamente com suas descrições e opções.

   * **Para obter ajuda sobre um comando específico:**
     ```bash
     python src/app/cli.py <comando> --help
     ```
     - Substitua `<comando>` pelo nome do comando sobre o qual você deseja obter ajuda.
     - Por exemplo, para obter ajuda sobre o comando `rapida`:
       ```bash
       python src/app/cli.py rapida --help
       ```

   * **Para atualizar a base de conhecimento:**
     ```bash
     python src/app/cli.py atualizar
     ```
     - Este comando atualiza a base de conhecimento do assistente com as informações mais recentes.

   * **Para curar a base de conhecimento:**
     ```bash
     python src/app/cli.py curar
     ```
     - Este comando realiza a curadoria da base de conhecimento, removendo informações obsoletas ou irrelevantes.

   * **Para gerar um relatório:**
     ```bash
     python src/app/cli.py relatorio
     ```
     - Este comando gera um relatório detalhado com base nos dados armazenados no banco de dados.

   * **Para configurar modelos de linguagem (LLM):**
     ```bash
     python src/app/cli.py configurar-modelos
     ```
     - Este comando permite configurar e ajustar os modelos de linguagem utilizados pelo assistente.

   * **Para detectar idioma e traduzir conteúdo:**
     ```bash
     python src/app/cli.py traduzir "Texto em inglês"
     ```
     - Este comando detecta o idioma do texto fornecido e o traduz para o idioma configurado.

   * **Para interagir com a interface do usuário:**
     ```bash
     python src/app/cli.py interface
     ```
     - Este comando inicia a interface do usuário, permitindo interações mais amigáveis e intuitivas.

   * **Para controlar a autonomia do assistente:**
     ```bash
     python src/app/cli.py autonomia
     ```
     - Este comando permite ajustar os níveis de autonomia do assistente, definindo quais tarefas ele pode realizar automaticamente.

3. **Exemplos de uso:**
   - **Exemplo 1:** Realizar uma consulta rápida sobre complicações da gastrectomia vertical.
     ```bash
     python src/app/cli.py rapida "Quais as complicações da gastrectomia vertical?"
     ```
   - **Exemplo 2:** Iniciar uma pesquisa profunda sobre o impacto da apneia do sono nos resultados da cirurgia bariátrica.
     ```bash
     python src/app/cli.py profunda "Impacto da apneia do sono nos resultados da cirurgia bariátrica"
     ```
   - **Exemplo 3:** Atualizar a base de conhecimento.
     ```bash
     python src/app/cli.py atualizar
     ```
   - **Exemplo 4:** Gerar um relatório detalhado.
     ```bash
     python src/app/cli.py relatorio
     ```
   - **Exemplo 5:** Configurar modelos de linguagem.
     ```bash
     python src/app/cli.py configurar-modelos
     ```
   - **Exemplo 6:** Traduzir um texto.
     ```bash
     python src/app/cli.py traduzir "Texto em inglês"
     ```
   - **Exemplo 7:** Iniciar a interface do usuário.
     ```bash
     python src/app/cli.py interface
     ```
   - **Exemplo 8:** Controlar a autonomia do assistente.
     ```bash
     python src/app/cli.py autonomia
     ```

### **Configuração de Modelos de Linguagem (LLM)**

A configuração dos modelos de linguagem (LLM) é crucial para personalizar o comportamento e a capacidade do assistente. Você pode configurar diferentes modelos e ajustar suas configurações através do arquivo de configuração central.

1. **Localização do Arquivo de Configuração:**
   - O arquivo de configuração central está localizado em `config/models.yaml`.

2. **Estrutura do Arquivo de Configuração:**
   - O arquivo `models.yaml` contém uma lista de modelos de linguagem disponíveis e suas configurações.
   - Cada modelo é definido com um nome, tipo, chave de API e outras configurações específicas.
   - Exemplo de estrutura:
     ```yaml
     models:
       - name: "gemini-2.5"
         type: "google"
         api_key: "${GOOGLE_API_KEY}"
         endpoint: "https://api.googleapis.com/v1/models/gemini-2.5:generateContent"
         parameters:
           max_tokens: 1024
           temperature: 0.7
       - name: "openai-gpt-4"
         type: "openai"
         api_key: "${OPENAI_API_KEY}"
         endpoint: "https://api.openai.com/v1/completions"
         parameters:
           max_tokens: 512
           temperature: 0.5
     ```

3. **Configuração de Modelos Específicos:**
   - Para configurar um modelo específico, adicione ou edite as entradas no arquivo `models.yaml`.
   - Certifique-se de fornecer todas as informações necessárias, como a chave de API e o endpoint.
   - Exemplo de configuração para o modelo Gemini 2.5:
     ```yaml
     models:
       - name: "gemini-2.5"
         type: "google"
         api_key: "${GOOGLE_API_KEY}"
         endpoint: "https://api.googleapis.com/v1/models/gemini-2.5:generateContent"
         parameters:
           max_tokens: 1024
           temperature: 0.7
     ```

4. **Seleção de Modelos na CLI:**
   - Você pode selecionar um modelo específico ao executar comandos na CLI usando a opção `--model`.
   - Exemplo de seleção do modelo Gemini 2.5:
     ```bash
     python src/app/cli.py rapida "Quais as complicações da gastrectomia vertical?" --model gemini-2.5
     ```
   - Exemplo de seleção do modelo OpenAI GPT-4:
     ```bash
     python src/app/cli.py profunda "Impacto da apneia do sono nos resultados da cirurgia bariátrica" --model openai-gpt-4
     ```

5. **Exemplos de Configuração:**
   - **Exemplo 1:** Configurar o modelo Gemini 2.5 com parâmetros personalizados.
     ```yaml
     models:
       - name: "gemini-2.5"
         type: "google"
         api_key: "${GOOGLE_API_KEY}"
         endpoint: "https://api.googleapis.com/v1/models/gemini-2.5:generateContent"
         parameters:
           max_tokens: 1500
           temperature: 0.6
     ```
   - **Exemplo 2:** Configurar o modelo OpenAI GPT-4 com parâmetros personalizados.
     ```yaml
     models:
       - name: "openai-gpt-4"
         type: "openai"
         api_key: "${OPENAI_API_KEY}"
         endpoint: "https://api.openai.com/v1/completions"
         parameters:
           max_tokens: 768
           temperature: 0.4
     ```

6. **Validação de Configuração:**
   - Após fazer as alterações no arquivo `models.yaml`, é recomendável validar a configuração para garantir que todos os modelos estejam corretamente configurados.
   - Você pode usar o comando `configurar-modelos` para validar e aplicar as configurações:
     ```bash
     python src/app/cli.py configurar-modelos
     ```
   - Este comando verificará a configuração e exibirá quaisquer erros ou avisos.

7. **Segurança:**
   - **NÃO** comite o arquivo `models.yaml` para o controle de versão se ele contiver chaves de API ou informações sensíveis.
   - Mantenha o arquivo `models.yaml` seguro e não compartilhe suas credenciais com terceiros.
   - Considere usar variáveis de ambiente para armazenar chaves de API e outros dados sensíveis.

8. **Atualização de Modelos:**
   - Para atualizar os modelos disponíveis, você pode adicionar novas entradas no arquivo `models.yaml` ou modificar as existentes.
   - Após fazer as alterações, use o comando `configurar-modelos` para aplicar as atualizações:
     ```bash
     python src/app/cli.py configurar-modelos
     ```
   - Este comando atualizará a lista de modelos disponíveis e aplicará as novas configurações.

### **Detecção de Idioma e Tradução**

A detecção de idioma e tradução são funcionalidades essenciais para garantir que o assistente possa lidar com conteúdo em diferentes idiomas, fornecendo respostas precisas e relevantes independentemente da língua do usuário.

1. **Funcionalidades:**
   - **Detecção de Idioma:** Identifica automaticamente o idioma do texto fornecido pelo usuário.
   - **Tradução:** Traduz o texto do idioma detectado para o idioma configurado no sistema.

2. **Configuração:**
   - **Chaves de API:** Para utilizar as funcionalidades de detecção de idioma e tradução, é necessário configurar as chaves de API dos provedores de serviços de tradução.
   - **Provedores Suportados:** Atualmente, o sistema suporta os seguintes provedores:
     - **Google Cloud Translation API**
     - **DeepL API**
     - **Microsoft Translator Text API**

3. **Exemplos de Configuração:**
   - **Exemplo 1:** Configurar o Google Cloud Translation API.
     ```yaml
     translation:
       provider: "google"
       api_key: "${GOOGLE_TRANSLATION_API_KEY}"
     ```
   - **Exemplo 2:** Configurar o DeepL API.
     ```yaml
     translation:
       provider: "deepl"
       api_key: "${DEEPL_API_KEY}"
     ```
   - **Exemplo 3:** Configurar o Microsoft Translator Text API.
     ```yaml
     translation:
       provider: "microsoft"
       api_key: "${MICROSOFT_TRANSLATOR_API_KEY}"
     ```

4. **Uso:**
   - **Comando de Tradução:**
     ```bash
     python src/app/cli.py traduzir "Texto em inglês"
     ```
   - **Comando de Detecção de Idioma:**
     ```bash
     python src/app/cli.py detectar-idioma "Texto em inglês"
     ```

5. **Validação de Configuração:**
   - Após fazer as alterações no arquivo de configuração, é recomendável validar a configuração para garantir que as chaves de API estejam corretamente configuradas.
   - Você pode usar o comando `configurar-traducao` para validar e aplicar as configurações:
     ```bash
     python src/app/cli.py configurar-traducao
     ```
   - Este comando verificará a configuração e exibirá quaisquer erros ou avisos.

6. **Segurança:**
   - **NÃO** comite o arquivo `models.yaml` para o controle de versão se ele contiver chaves de API ou informações sensíveis.
   - Mantenha o arquivo `models.yaml` seguro e não compartilhe suas credenciais com terceiros.
   - Considere usar variáveis de ambiente para armazenar chaves de API e outros dados sensíveis.
