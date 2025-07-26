## **README.md**

# **Pró-Vida: Assistente de Pesquisa Autônomo**

### **Sobre o Projeto**

O "Pró-Vida" é um ecossistema de IA e um assistente de pesquisa autônomo projetado para cirurgiões bariátricos. Ele utiliza uma arquitetura de múltiplos agentes, orquestrada pelo LangGraph e potencializada pela família de modelos Gemini 2.5, para realizar pesquisas aprofundadas, analisar e classificar evidências científicas, e manter uma base de conhecimento que evolui continuamente.

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

### **Primeiros Passos**

#### **Pré-requisitos**

* Python 3.10 ou superior  
* Docker e Docker Compose  
* Conta na Google AI Platform com acesso aos modelos Gemini

#### **Instalação**

1. **Clone o repositório:**  
   git clone \<URL\_DO\_REPOSITORIO\>  
   cd PROJETO\_PRO-VIDA

2. **Crie e ative um ambiente virtual:**  
   python \-m venv venv  
   source venv/bin/activate  \# No Windows: venv\\Scripts\\activate

3. **Instale as dependências:**  
   pip install \-r requirements.txt

4. **Configure as variáveis de ambiente:**  
   * Copie o arquivo de exemplo: cp .env.example .env  
   * Edite o arquivo .env e adicione suas chaves de API e credenciais.  
5. **Inicie os serviços de backend (Neo4j, MinIO):**  
   docker-compose up \-d

### **Uso**

A aplicação é controlada via linha de comando.

* **Para uma Consulta Rápida:**  
  python main.py \--mode fast-query \--query "Quais as complicações da gastrectomia vertical?"

* **Para iniciar uma Pesquisa Profunda:**  
  python main.py \--mode deep-research \--topic "Impacto da apneia do sono nos resultados da cirurgia bariátrica"

## **ARCHITECTURE.md**

# **Arquitetura Técnica do Projeto Pró-Vida**

### **Diagrama de Componentes de Alto Nível**

Este diagrama mostra a interação entre os principais componentes do sistema.

graph TD  
    A\[Usuário (CLI)\] \--\> B{Orquestrador de Agentes (LangGraph)};  
    B \--\> C1\[Agente de Planejamento/Simulação\];  
    B \--\> C2\[Agente de Busca\];  
    B \--\> C3\[Agente de Análise/Classificação\];  
    B \--\> C4\[Agente de Síntese/Citação\];  
    B \--\> C5\[Agente Curador (Autônomo)\];  
    B \--\> C6\[Agente de Feedback\];

    subgraph "Camada de Dados"  
        D1\[MinIO S3 (Arquivos Brutos)\];  
        D2\[Vector DB (RAG)\];  
        D3\[Neo4j (Knowledge Graph)\];  
        D4\[Neo4j (Memória Agentica)\];  
    end

    C2 \--\> D1;  
    C2 \--\> D2;  
    C3 \--\> D3;  
    C4 \--\> D3;  
    C5 \--\> D3;  
      
    C1 \<--\> D4;  
    C2 \<--\> D4;  
    C3 \<--\> D4;  
    C4 \<--\> D4;  
    C5 \<--\> D4;  
    C6 \<--\> D4;

### **Fluxo de Dados \- Modo "Pesquisa Profunda"**

1. **Iniciação:** O Usuário executa main.py com o modo deep-research e um tópico.  
2. **Planejamento:** O Orquestrador aciona o Agente de Planejamento. O prompt é enviado ao LLM (Gemini 2.5 Pro) que retorna um plano JSON.  
3. **Simulação:** O Agente de Simulação analisa o plano e estima os recursos necessários, apresentando ao usuário.  
4. **Validação:** O Usuário aprova o plano na CLI.  
5. Loop de Execução (para cada pergunta do plano):  
   a. Busca: O Agente de Busca pesquisa nas fontes externas.  
   b. Armazenamento Bruto: Os PDFs encontrados são salvos no MinIO S3.  
   c. Tradução: Se necessário, o Agente de Tradução (Gemini 2.5 Flash-Lite) processa o texto.  
   d. Análise: O Agente de Análise gera o resumo e a classificação de evidência.  
   e. Armazenamento Processado: O Agente de Banco de Dados insere os dados no Vector DB e no Knowledge Graph.  
6. **Reflexão:** O Agente de Reflexão analisa o progresso e atualiza o plano.  
7. **Conclusão:** Quando o plano é concluído, o Agente de Síntese cria o relatório final.  
8. **Feedback:** O Agente de Feedback inicia um diálogo para coletar feedback estruturado e atualizar as memórias dos agentes.

## **PROMPTS.md**

# **Engenharia de Contexto e Prompts para o Sistema Pró-Vida**

Este arquivo define os templates de prompts mestres para cada tarefa de IA.

### **1\. Agente de Planejamento (Deep Research)**

* **Objetivo:** Decompor um tópico em um plano de pesquisa estruturado.  
* **Modelo:** planning\_agent (Gemini 2.5 Pro)  
* **Template:**  
  Você é um pesquisador médico sênior. Sua tarefa é criar um plano de pesquisa abrangente para o tema: "{tema\_principal}".  
  O plano deve ser uma lista de perguntas investigativas. O resultado DEVE ser um objeto JSON com a chave "plano\_de\_pesquisa", que é um array de strings.  
  Exemplo: {"plano\_de\_pesquisa": \["Qual a definição de X?", ...\]}

### **2\. Agente de Análise e Classificação**

* **Objetivo:** Analisar um artigo, extrair informações e classificar seu nível de evidência.  
* **Modelo:** analysis\_agent (Gemini 2.5 Pro)  
* **Template:**  
  Você é um analista científico. Analise o texto fornecido para responder à pergunta: "{pergunta\_do\_plano}".  
  O resultado DEVE ser um único objeto JSON com as chaves: "resumo", "tipo\_de\_estudo", "nivel\_de\_evidencia" (A, B, C, D, ou E), "palavras\_chave" (array de strings).  
  Se a informação não estiver presente, o valor da chave DEVE ser 'null'. Não invente informações.  
  \--- TEXTO DO ARTIGO \---  
  {texto\_do\_artigo}

### **3\. Agente de Simulação**

* **Objetivo:** Estimar os recursos para um plano de pesquisa.  
* **Modelo:** planning\_agent (Gemini 2.5 Pro)  
* **Template:**  
  Você é um planejador de projetos de IA. Dado o seguinte plano de pesquisa, estime o número de buscas externas necessárias e o número de chamadas de análise complexa (Pro) que serão realizadas.  
  O resultado DEVE ser um objeto JSON com as chaves: "buscas\_estimadas" (integer) e "analises\_pro\_estimadas" (integer).  
  \--- PLANO DE PESQUISA \---  
  {plano\_de\_pesquisa}

### **4\. Agente de Tradução**

* **Objetivo:** Traduzir um texto para o português.  
* **Modelo:** translation\_agent (Gemini 2.5 Flash-Lite)  
* **Template:**  
  Traduza o seguinte texto para o português do Brasil de forma precisa e mantendo o tom técnico.  
  \--- TEXTO ORIGINAL \---  
  {texto\_original}  
