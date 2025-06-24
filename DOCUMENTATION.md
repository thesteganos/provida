# Documentação do Usuário - PROVIDA

## 1. Visão Geral

PROVIDA é um Sistema de Apoio à Decisão Clínica (SADC) de última geração, projetado para auxiliar profissionais de saúde no manejo de sobrepeso, obesidade e comorbidades metabólicas. A aplicação utiliza uma arquitetura de Sistema Multi-Agente (MAS) orquestrada com LangGraph, fundamentada em uma base de conhecimento híbrida que combina Grafos de Conhecimento (Neo4j) e Geração Aumentada por Recuperação (RAG).

Esta documentação foca em como interagir com a API do sistema PROVIDA.

## 2. Funcionalidades Principais da API

A API do PROVIDA oferece três funcionalidades centrais:

*   **Processamento de Pacientes (`/process_patient`):** Recebe dados de um novo paciente (ou um ID de paciente existente), orquestra uma série de agentes de IA para realizar anamnese, diagnóstico, planejamento terapêutico e verificação, e retorna um plano terapêutico consolidado.
*   **Consulta à Base de Conhecimento (`/knowledge/query`):** Permite que usuários busquem informações e evidências dentro da base de conhecimento textual do sistema (artigos científicos, diretrizes, etc.) utilizando uma linguagem natural ou palavras-chave.
*   **Ingestão de Novos Documentos (`/knowledge/ingest`):** Permite que usuários contribuam com novos documentos (em formato PDF ou TXT) para enriquecer a base de conhecimento do sistema. Estes documentos são processados, indexados e ficam disponíveis para futuras consultas RAG.

## 3. Guia de Uso da API

A API está disponível em `http://127.0.0.1:8000` (após a inicialização do servidor Uvicorn, conforme descrito no `README.md`). A documentação interativa (Swagger UI) pode ser acessada em `http://127.0.0.1:8000/docs`.

### 3.1. Processar Dados do Paciente e Gerar Plano Terapêutico

*   **Endpoint:** `POST /process_patient`
*   **Descrição:** Envia dados de um paciente para serem processados pelo fluxo de agentes da PROVIDA, resultando em um plano terapêutico.
*   **Corpo da Requisição (`application/json`):**
    ```json
    {
      "patient_id": "opcional-uuid-paciente-existente",
      "patient_data": {
        "name": "João da Silva",
        "age": 45,
        "imc": 34.0,
        "hba1c": 6.8,
        "notes": "Paciente relata cansaço frequente e histórico familiar de diabetes."
      }
    }
    ```
    *   `patient_id` (string, opcional): Se fornecido, o sistema tentará usar dados existentes para este paciente. Se omitido ou novo, um ID será gerado.
    *   `patient_data` (objeto, obrigatório): Contém os dados do paciente.
        *   `name` (string, obrigatório): Nome completo do paciente.
        *   `age` (integer, obrigatório): Idade do paciente em anos.
        *   `imc` (float, obrigatório): Índice de Massa Corporal.
        *   `hba1c` (float, obrigatório): Valor da Hemoglobina Glicada.
        *   `notes` (string, obrigatório): Queixas, histórico ou outras notas relevantes.
*   **Resposta de Sucesso (200 OK):**
    ```json
    {
      "patient_id": "uuid-do-paciente-processado",
      "final_plan_for_clinician": "## Plano Terapêutico Sugerido para o Paciente: uuid-do-paciente-processado ##\n\n**Diagnóstico e Riscos Avaliados:**\n[Texto do diagnóstico gerado pela IA]\n\n**Plano Terapêutico Proposto:**\n[Texto do plano terapêutico gerado pela IA]\n\n**Resultado da Verificação de Qualidade:**\n  - Score de Confiança: [0.0-1.0]\n  - Notas do Verificador: [Notas da verificação]\n"
    }
    ```
*   **Respostas de Erro:**
    *   `422 Unprocessable Entity`: Erro de validação nos dados de entrada. O corpo da resposta conterá detalhes.
    *   `500 Internal Server Error`: Erro interno durante o processamento do fluxo de agentes.

### 3.2. Consultar a Base de Conhecimento (RAG)

*   **Endpoint:** `POST /knowledge/query`
*   **Descrição:** Realiza uma busca por similaridade na base de documentos indexados.
*   **Corpo da Requisição (`application/json`):**
    ```json
    {
      "query": "Qual o tratamento recomendado para obesidade grau I com metformina?"
    }
    ```
    *   `query` (string, obrigatório): A pergunta ou termos de busca.
*   **Resposta de Sucesso (200 OK):**
    ```json
    {
      "source_documents": [
        {
          "page_content": "Trecho do documento encontrado...",
          "metadata": {
            "source": "nome_do_arquivo.pdf",
            "page": 12
          }
        },
        {
          "page_content": "Outro trecho relevante...",
          "metadata": {
            "source": "artigo_cientifico.txt",
            "page": null
          }
        }
      ]
    }
    ```
    *   `source_documents` (array): Lista de trechos de documentos relevantes. Cada item contém:
        *   `page_content` (string): O conteúdo textual do trecho.
        *   `metadata` (objeto): Metadados do trecho, incluindo `source` (nome do arquivo original) e `page` (número da página, se aplicável).
*   **Respostas de Erro:**
    *   `422 Unprocessable Entity`: Erro de validação (ex: query vazia).
    *   `500 Internal Server Error`: Erro interno durante a busca.

### 3.3. Ingerir Novo Documento na Base de Conhecimento

*   **Endpoint:** `POST /knowledge/ingest`
*   **Descrição:** Faz upload de um novo documento (PDF ou TXT) para ser adicionado à base de conhecimento RAG.
*   **Corpo da Requisição (`multipart/form-data`):**
    *   `file`: O arquivo a ser enviado. Deve ser um `.pdf` ou `.txt`.
*   **Exemplo de Requisição (usando `curl`):**
    ```bash
    curl -X POST "http://127.0.0.1:8000/knowledge/ingest" \
         -H "accept: application/json" \
         -H "Content-Type: multipart/form-data" \
         -F "file=@/caminho/para/seu/documento.pdf"
    ```
*   **Resposta de Sucesso (200 OK):**
    ```json
    {
      "message": "Arquivo 'documento.pdf' ingerido com sucesso.",
      "detail": "Documento 'documento.pdf' ingerido e indexado com sucesso."
    }
    ```
    Ou, em caso de duplicata:
    ```json
    {
      "message": "Arquivo 'documento_duplicado.pdf' processado.",
      "detail": "DEDUPLICAÇÃO POR HASH: O conteúdo de 'documento_duplicado.pdf' já existe."
    }
    ```
*   **Respostas de Erro:**
    *   `400 Bad Request`: Formato de arquivo inválido (não é PDF ou TXT).
    *   `422 Unprocessable Entity`: Problema com o conteúdo do arquivo que impede o processamento (ex: PDF corrompido, erro na leitura).
    *   `500 Internal Server Error`: Erro interno durante o salvamento ou ingestão do arquivo.

## 4. Modelo de Dados Detalhado

Esta seção reitera os modelos de dados Pydantic usados pela API, que também podem ser inspecionados via Swagger UI (`/docs`).

*   **PatientInput:**
    *   `name: str`
    *   `age: int`
    *   `imc: float`
    *   `hba1c: float`
    *   `notes: str`

*   **ProcessRequest:**
    *   `patient_id: Optional[str]`
    *   `patient_data: PatientInput`

*   **ProcessResponse:**
    *   `patient_id: str`
    *   `final_plan_for_clinician: str`

*   **KnowledgeQuery:**
    *   `query: str`

*   **DocumentMetadata:**
    *   `source: str`
    *   `page: Optional[int]`

*   **DocumentSnippet:**
    *   `page_content: str`
    *   `metadata: DocumentMetadata`

*   **KnowledgeResponse:**
    *   `source_documents: list[DocumentSnippet]`

## 5. Solução de Problemas Comuns

*   **Erro `503 Service Unavailable` ou Falha na Conexão com Neo4j/Google API:**
    *   Verifique se a instância do Neo4j está rodando e acessível (confira `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD` no arquivo `.env`).
    *   Verifique sua chave da API do Google (`GOOGLE_API_KEY` no arquivo `.env`) e se há conexão com a internet.
    *   Consulte os logs da aplicação FastAPI e do `research_worker.py` para mensagens de erro detalhadas.

*   **Ingestão de Documentos Falha Silenciosamente ou Documentos Não Aparecem na Busca:**
    *   Verifique os logs do servidor FastAPI ao realizar a chamada para `/knowledge/ingest`.
    *   O `research_worker.py` também possui logs detalhados sobre o processo de download e ingestão.
    *   Certifique-se de que o formato do arquivo é PDF ou TXT.
    *   Arquivos podem ser rejeitados por deduplicação (hash ou semântica). A resposta da API ou os logs devem indicar isso.

*   **Resultados da Busca RAG (`/knowledge/query`) Não São Relevantes:**
    *   A qualidade da busca RAG depende da qualidade e quantidade dos documentos na base. Considere adicionar mais documentos relevantes ou refinar os existentes.
    *   A formulação da query também impacta os resultados. Tente diferentes formas de perguntar.

*   **"OutputFixingParser" nos Logs dos Agentes:**
    *   Isso indica que o LLM de um agente não retornou a saída no formato JSON esperado inicialmente, e o sistema tentou corrigi-la. Se ocorrer com frequência, pode ser necessário ajustar os prompts dos agentes (em `prompts.py`) ou a temperatura do modelo LLM (em `config.yaml`).

*   **Performance Lenta:**
    *   O processamento de pacientes envolve múltiplas chamadas a LLMs, o que pode levar algum tempo.
    *   A ingestão de documentos grandes também pode ser demorada.
    *   Verifique o uso de recursos do sistema (CPU, memória) onde a aplicação e o Neo4j estão rodando.

Para problemas mais complexos, consulte os logs detalhados da aplicação e, se necessário, o código-fonte para entender o fluxo de dados e as operações realizadas.
