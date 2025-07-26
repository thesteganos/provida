# **Projeto Pró-Vida: Assistente de Pesquisa Autônomo para Cirurgia Bariátrica**

## **1\. Visão Geral**

O "Pró-Vida" é um ecossistema de IA projetado para ser o assistente de pesquisa definitivo para um cirurgião bariátrico. O sistema utiliza uma arquitetura de LLMs flexível e com alocação estratégica, baseada inicialmente na família de modelos **Gemini 2.5**, opera em dois modos distintos ("Consulta Rápida" e "Pesquisa Profunda"), realiza investigações exaustivas, classifica a informação por nível de evidência, fornece citações no nível da frase para verificação imediata, e executa tarefas de atualização de conhecimento de forma autônoma e agendada. Todo o sistema é construído sobre princípios de controle do usuário, transparência, segurança e aprendizado contínuo.

## **2\. Princípios Fundamentais do Sistema**

* **Controle do Usuário:** O usuário final tem controle granular sobre as operações, incluindo limites de pesquisa, agendamento de tarefas e a seleção dos modelos de IA.  
* **Transparência e Verificabilidade:** Cada informação sintetizada é diretamente rastreável à sua fonte original através de citações inline e um diário de bordo detalhado.  
* **Apresentação Imparcial de Conflitos:** O sistema não resolve conflitos de forma autônoma. Ele apresenta todos os dados encontrados, mesmo que contraditórios, e os organiza por nível de evidência, capacitando o usuário a fazer seu próprio julgamento clínico. A obsolescência do conhecimento não é tratada automaticamente; em vez disso, o sistema foca em apresentar a totalidade das informações encontradas.  
* **Aprendizado Contínuo:** O sistema evolui através de memórias agenticas e processos de curadoria de conhecimento, aprimorados por um ciclo de feedback estruturado.  
* **Segurança e Flexibilidade:** Chaves de API são gerenciadas de forma segura e a arquitetura permite a troca de modelos de IA.

## **3\. Modos de Operação**

O sistema oferece dois modos de interação principais:

* **3.1. Modo Consulta Rápida (RAG):** Para perguntas diretas. O sistema responde imediatamente usando a base de conhecimento já existente.  
* **3.2. Modo Pesquisa Profunda (Deep Research):** Para investigações complexas. Inicia o ciclo completo de pesquisa.

## **4\. Agentes e Suas Funções Avançadas**

A equipe de agentes, orquestrada pelo LangGraph, possui funções especializadas:

* **Agente de Planejamento e Simulação:** Cria o plano de pesquisa e **estima os recursos necessários** (nº de buscas, chamadas de API) para a sua execução.  
* **Agente de Análise e Classificação:** Avalia e **classifica a informação segundo os níveis de evidência (A, B, C, D, E)**.  
* **Agente de Síntese e Citação:** Gera resumos e relatórios com **citações no nível da frase**.  
* **Agente Curador de Conhecimento (Autônomo):** Executa as tarefas agendadas de manutenção e evolução do conhecimento.  
* **Agente de Feedback:** Coleta e processa o feedback estruturado do usuário para atualizar as memórias dos outros agentes.

## **5\. Workflow Principal: Ciclo de Pesquisa Profunda**

Este ciclo é o coração do sistema e segue um fluxo rigoroso:

1. **Fase de Planejamento:** O Agente de Planejamento decompõe o tópico em um plano de pesquisa detalhado.  
2. **Fase de Simulação e Confirmação:** O agente apresenta o plano e uma **estimativa de custo/tempo**. O usuário deve confirmar para prosseguir.  
3. **Fase de Validação do Plano:** O usuário aprova ou modifica o plano.  
4. **Loop de Execução e Coleta:** O sistema itera sobre cada pergunta do plano, realizando a busca, download para o MinIO, tradução (se necessário), e armazenamento. O ciclo respeita o **limite de buscas configurado (padrão: 100\)**.  
5. **Fase de Análise e Síntese:** Os dados coletados são processados, classificados por nível de evidência e integrados aos bancos de dados.  
6. **Fase de Reflexão e Análise de Lacunas:** O sistema analisa o progresso e atualiza dinamicamente o plano de pesquisa.  
7. **Fase de Conclusão e Relatório:** Ao final do ciclo, o Agente de Síntese gera um **relatório final com o máximo nível de detalhe possível**.  
8. **Fase de Feedback Estruturado:** Após a entrega do relatório, o Agente de Feedback inicia um diálogo para coletar dados que serão usados para refinar a memória dos agentes.

## **6\. Arquitetura de Dados e Tecnológica**

A arquitetura quádrupla (MinIO, Neo4j Conhecimento, Vector DB, Neo4j Memória) e a stack tecnológica (Python, LangGraph, Gemini 2.5, Docker) estão mantidas.

## **7\. Processos de Longo Prazo e Manutenção (Autonomia Controlada)**

O Agente Curador gerencia a evolução da base de conhecimento com as seguintes diretivas:

* **7.1. Bootstrapping do Conhecimento:** Carga inicial de artigos seminais.  
* **7.2. Atualização Diária Autônoma:**  
  * **Horário:** Configurável (padrão: 05:00-06:00).  
  * **Protocolo de Decisão:** Durante a rotina autônoma, se o agente encontrar uma evidência de alto nível (ex: Nível A) que contradiz uma de baixo nível (ex: Nível C), ele **realizará a atualização no grafo de conhecimento de forma autônoma**. Esta ação será registrada com destaque no "Diário de Bordo". Em casos de conflito entre evidências de mesmo nível, a informação será apenas adicionada e marcada para intervenção manual do usuário.  
* **7.3. Revisão Trimestral de Conflitos:** A cada 3 meses, o agente busca ativamente por novas publicações que possam resolver os conflitos marcados no grafo.

## **8\. Interface do Usuário e Controles Configuráveis**

A interface (inicialmente CLI, com plano para web) será o centro de controle, oferecendo:

* Visualização de dados, exploração do grafo e acesso aos PDFs originais.  
* **Configurações de Pesquisa:**  
  * Ajuste do limite de buscas.  
  * **Seleção do nível de detalhe para resumos em "Consultas Rápidas"** (Breve, Padrão, Detalhado).  
* **Configurações de Automação:**  
  * Controle total sobre o agendamento da tarefa de curadoria.  
* **Configurações de Relatório:**  
  * Seleção do formato de exportação (PDF, DOCX, Markdown).  
* **Configurações de Modelos (LLM):**  
  * Interface para alterar a alocação de modelos e atualizar a chave de API.

## **9\. Logs e Transparência (Diário de Bordo)**

* Um arquivo de log (system\_log.txt), legível por humanos, será mantido.  
* Ele registrará todas as ações significativas do sistema, incluindo **todas as decisões autônomas tomadas pelo Agente Curador**.

## **10\. Engenharia de Contexto e Guardrails para o gemini-cli**

Esta seção define as regras mandatórias para a construção de todos os prompts enviados aos modelos Gemini, garantindo respostas previsíveis, seguras e estruturadas.

### **10.1. Prompts Positivos (O que SEMPRE deve ser feito)**

* **1\. Atribuir uma Persona (Role-playing):** Todo prompt deve começar atribuindo um papel específico ao modelo. Ex: Você é um pesquisador médico sênior e um especialista em análise de dados científicos. Isso prepara o modelo para o tom, vocabulário e estilo de raciocínio corretos.  
* **2\. Exigir Formato de Saída Estruturado (JSON):** Toda solicitação que espera um retorno de dados para processamento programático DEVE exigir a saída em um formato JSON estrito. O prompt deve especificar as chaves, os tipos de dados (string, array, etc.) e a estrutura geral.  
* **3\. Fornecer Exemplos (Few-shot Prompting):** Para tarefas complexas ou que exigem um formato de saída muito específico, o prompt deve incluir um ou dois exemplos claros de entrada e da saída esperada.  
* **4\. Usar Delimitadores Claros:** O contexto fornecido ao modelo (como o texto de um artigo) deve ser encapsulado em delimitadores claros e únicos para evitar ambiguidades. Ex: \--- TEXTO DO ARTIGO PARA ANÁLISE \--- {texto\_do\_artigo} \--- FIM DO TEXTO \---.  
* **5\. Ser Explícito e Direto na Tarefa:** A instrução deve ser inequívoca. Em vez de "resuma o texto", use "Crie um resumo conciso de 3 a 5 frases que responda diretamente à seguinte pergunta de pesquisa: ...".

### **10.2. Prompts Negativos (O que NUNCA deve ser feito)**

* **1\. Nunca Fazer Perguntas Abertas:** Evitar prompts que permitam respostas narrativas e não estruturadas, como Fale-me sobre X. Toda pergunta deve ter como objetivo preencher uma estrutura de dados pré-definida.  
* **2\. Nunca Permitir Alucinações ou Invenções:** Todo prompt que envolve extração de informação de um texto fonte deve incluir uma instrução de segurança explícita. Ex: Se a informação necessária para responder à pergunta não estiver contida no texto fornecido, o valor da chave correspondente no JSON de saída DEVE ser 'null'. Não invente ou infira informações que não estejam explicitamente presentes.  
* **3\. Nunca Pedir Opiniões ou Conselhos Médicos:** O sistema é uma ferramenta de processamento de informação, não um consultor médico. Os prompts devem focar em tarefas objetivas: extrair, resumir, classificar, traduzir e conectar fatos. Perguntas como Qual o melhor tratamento para X? são estritamente proibidas. A pergunta correta seria Quais tratamentos para X são mencionados no texto e qual o nível de evidência associado a cada um?.  
* **4\. Nunca Assumir Estado ou Memória da Conversa:** Cada chamada à API do Gemini deve ser tratada como completamente independente (stateless). Todo o contexto necessário para a tarefa (texto do artigo, pergunta de pesquisa, exemplos) deve ser fornecido em cada prompt individual. A gestão do estado da conversa é responsabilidade do orquestrador (LangGraph), não do LLM.