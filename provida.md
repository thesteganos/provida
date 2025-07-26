# **Projeto Pró-Vida: Assistente de Pesquisa Autônomo para Cirurgia Bariátrica**

## **1\. Visão Geral**

O "Pró-Vida" é um ecossistema de IA projetado para ser o assistente de pesquisa definitivo para um cirurgião bariátrico. O sistema utiliza uma arquitetura de LLMs flexível e com alocação estratégica, baseada inicialmente na família de modelos **Gemini 2.5**, opera em dois modos distintos ("Consulta Rápida" e "Pesquisa Profunda"), realiza investigações exaustivas, classifica a informação por nível de evidência, fornece citações no nível da frase para verificação imediata, e executa tarefas de atualização de conhecimento de forma autônoma e agendada. Todo o sistema é construído sobre princípios de controle do usuário, transparência, segurança e aprendizado contínuo.

## **2\. Princípios Fundamentais do Sistema**

* **Controle do Usuário:** O usuário final tem controle granular sobre as operações, incluindo limites de pesquisa, agendamento de tarefas e a seleção dos modelos de IA.  
* **Transparência e Verificabilidade:** Cada informação é rastreável à sua fonte original através de citações inline.  
* **Neutralidade na Apresentação:** O sistema apresenta dados conflitantes e os organiza por nível de evidência.  
* **Aprendizado Contínuo:** O sistema evolui através de memórias agenticas e processos de curadoria de conhecimento.  
* **Segurança e Flexibilidade:** Chaves de API são gerenciadas de forma segura e a arquitetura permite a troca de modelos de IA.

## **3\. Estratégia de Modelos de Linguagem (LLM) e Configuração**

### **3.1. Gerenciamento Seguro da Chave de API**

A chave de API do Google será carregada a partir de variáveis de ambiente e nunca será escrita diretamente no código. O placeholder para a chave é SUA\_GOOGLE\_API\_KEY.

### **3.2. Arquitetura Flexível de LLMs**

O sistema não terá nomes de modelos "hardcoded". Um arquivo de configuração central definirá qual modelo usar para cada tarefa, permitindo a fácil alteração de modelos ou até mesmo de provedores de LLM.

### **3.3. Modelos Iniciais e Alocação Estratégica**

A estratégia inicial utilizará a família de modelos Gemini 2.5, planejando para a tecnologia mais avançada disponível no momento do desenvolvimento.

| Agente / Tarefa | Modelo Recomendado | Justificativa |
| :---- | :---- | :---- |
| **Planejamento da Pesquisa Profunda** | **Gemini 2.5 Pro** | Requer máximo raciocínio para criar um plano de pesquisa coerente. |
| **Análise e Classificação (Nível de Evidência)** | **Gemini 2.5 Pro** | Tarefa complexa que exige análise crítica do texto acadêmico. |
| **Síntese Final e Relatório com Citações** | **Gemini 2.5 Pro** | Geração de texto de alta qualidade, coeso e com citações precisas. |
| **Modo Consulta Rápida (RAG)** | **Gemini 2.5 Flash** | Precisa de velocidade e boa capacidade de resumir o conhecimento existente. |
| **Interações Gerais de Chat** | **Gemini 2.5 Flash** | Respostas rápidas e fluidas para a conversação. |
| **Tradução de Textos** | **Gemini 2.5 Flash-Lite** | **Tarefa de tradução de alta frequência e baixo custo.** |
| **Extração de Keywords/Entidades Simples** | **Gemini 2.5 Flash-Lite** | Tarefa de baixo custo e alto volume, ideal para um modelo leve. |

## **4\. Modos de Operação**

* **4.1. Modo Consulta Rápida (RAG):** Usa o modelo **Gemini 2.5 Flash** para respostas rápidas.  
* **4.2. Modo Pesquisa Profunda (Deep Research):** Utiliza os modelos **Pro** e **Flash** conforme a fase do ciclo. Limite padrão de 100 buscas, configurável.

## **5\. Agentes e Suas Funções Avançadas**

Os agentes executarão suas tarefas utilizando o modelo de LLM designado no arquivo de configuração.

## **6\. Workflow Principal: Ciclo de Pesquisa Profunda**

O ciclo permanece como definido, com a seguinte adição ao fluxo de processamento de dados:

* **Fase de Preparação de Dados (dentro do ciclo):**  
  1. Após o Agente de Busca coletar um artigo e extrair seu texto, o sistema detecta o idioma.  
  2. **Se o idioma não for o português, o texto é enviado para o modelo Gemini 2.5 Flash-Lite para tradução.**  
  3. O texto traduzido (ou o original, se já em português) é então encaminhado ao Agente de Análise e Classificação para a próxima etapa.

## **7\. Arquitetura de Dados Quádrupla**

A arquitetura de 4 camadas (MinIO, Neo4j Conhecimento, Vector DB, Neo4j Memória) está mantida.

## **8\. Processos de Longo Prazo e Manutenção (Autonomia Controlada)**

Os processos de Bootstrapping, Atualização Diária e Revisão Trimestral estão mantidos e usarão uma combinação de modelos **Flash** (para buscas) e **Pro** (para análise final) para eficiência.

## **9\. Interface do Usuário e Controles Configuráveis**

O painel de controle será o centro de gerenciamento, oferecendo:

* Visualização de dados, exploração do grafo e acesso aos PDFs originais.  
* **Configurações de Pesquisa:**  
  * Ajuste do limite de buscas para o modo "Pesquisa Profunda".  
* **Configurações de Automação:**  
  * Ativar/desativar e configurar o agendamento da tarefa autônoma.  
* **Configurações de Relatório:**  
  * Seleção do formato de exportação padrão (PDF, DOCX, Markdown).  
* **Configurações de Modelos (LLM):**  
  * Uma interface para visualizar e **alterar qual modelo está alocado para cada tarefa principal do sistema**.  
  * Um campo para **atualizar a chave de API** de forma segura.