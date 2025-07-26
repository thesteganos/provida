# Projeto Pró-Vida: Assistente de Pesquisa para Cirurgia Bariátrica

Este repositório contém o código e a documentação para o **Projeto Pró-Vida**, um ecossistema de IA projetado para ser o assistente de pesquisa definitivo para um cirurgião bariátrico. O desenvolvimento é guiado por princípios de **Engenharia de Contexto** para garantir que os agentes de IA possam implementar funcionalidades de forma autônoma e eficaz.

## 📌 Visão Geral do Projeto

O Pró-Vida utiliza uma arquitetura de LLMs flexível, centrada na família de modelos Gemini, para oferecer dois modos principais de operação: "Consulta Rápida" (RAG) e "Pesquisa Profunda". A visão completa, arquitetura e requisitos estão detalhados em `provida.md`.

## 🤖 A Abordagem de Engenharia de Contexto

Este projeto não é apenas sobre código, mas sobre como instruir agentes de IA para escrever esse código. Utilizamos uma metodologia estruturada:

1.  **Visão do Projeto (`provida.md`)**: Um documento central que define o "porquê" e o "o quê" do projeto.
2.  **Modelo de PRP (`PRPs/templates/prp_base.md`)**: Um modelo detalhado para criar "Planos de Pesquisa de Projeto" (PRPs). Este modelo força a inclusão de todo o contexto necessário para o sucesso do agente de IA.
3.  **PRPs Detalhados (`INITIAL.md`)**: Cada nova funcionalidade começa com um PRP detalhado, que serve como um blueprint completo para o agente de IA. `INITIAL.md` é o nosso primeiro exemplo, focando na criação do CLI.

Este processo garante que o desenvolvimento seja consistente, previsível e alinhado com os objetivos do projeto.

## 🚀 Como Começar

### Pré-requisitos
- Python 3.10+
- Acesso à API do Google Gemini

### Instalação
1.  **Clone o repositório:**
    ```bash
    git clone <URL do seu repositório>
    cd <nome do repositório>
    ```

2.  **Crie e configure o ambiente:**
    - Crie um arquivo `.env` a partir do `.env.example` (se houver um) ou crie um novo.
    - Adicione sua chave da API do Google ao arquivo `.env`:
      ```
      GOOGLE_API_KEY="sua_chave_aqui"
      ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

##  workflow de Desenvolvimento

O desenvolvimento no Pró-Vida é feito através da execução de PRPs por um agente de IA (como o `gemini-cli`).

1.  **Revisar o PRP**: Antes da execução, revise o PRP para a funcionalidade desejada (e.g., `INITIAL.md`).
2.  **Executar o PRP**: Use uma ferramenta como o Gemini CLI para executar o plano. O agente de IA irá ler o PRP e começar a implementação.
    ```bash
    gemini-cli execute-prp INITIAL.md
    ```
3.  **Validar**: O agente irá rodar os loops de validação (linting, testes) definidos no PRP para garantir que o código está correto.

## 📂 Estrutura do Projeto

```
.
├── .gemini/              # Configurações e comandos para o Gemini CLI
├── PRPs/                 # Planos de Pesquisa de Projeto
│   ├── templates/
│   │   └── prp_base.md   # O modelo mestre para PRPs
│   └── ...               # Outros PRPs para funcionalidades futuras
├── src/                  # Código-fonte do projeto Pró-Vida
├── tests/                # Testes de unidade e integração
├── .env                  # Arquivo para suas chaves de API (não versionado)
├── GEMINI.md             # Regras globais para o assistente de IA
├── INITIAL.md            # O primeiro e mais detalhado PRP para iniciar o projeto
├── provida.md            # O documento de visão e arquitetura do projeto
└── README.md             # Este arquivo
```