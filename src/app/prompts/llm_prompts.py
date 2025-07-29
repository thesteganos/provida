from app.models.feedback_models import FeedbackContext

FEEDBACK_AGENT_PROMPT = """Você é um Agente de Feedback. Sua tarefa é analisar o feedback do usuário e o contexto da interação para extrair informações estruturadas.

Contexto da Interação:
{context_json}

Feedback do Usuário:
{user_feedback}

Extraia as seguintes informações em formato JSON:
- 'sentiment': Sentimento geral do feedback (positivo, negativo, neutro). Use apenas 'positivo', 'negativo' ou 'neutro'.
- 'accuracy_rating': Avaliação da precisão da resposta (escala de 1 a 5, onde 5 é muito preciso). Use um número inteiro.
- 'suggestions': Sugestões de melhoria ou novas funcionalidades (lista de strings). Use um array de strings.
- 'relevant_query': A query original à qual o feedback se refere (se identificável). Use uma string ou null.
- 'relevant_agent': O agente principal ao qual o feedback se refere (se identificável, ex: 'RAG', 'Deep Research'). Use uma string ou null.

Formato de Saída (JSON):
{{
    "sentiment": "positivo",
    "accuracy_rating": 4,
    "suggestions": ["sugestao1", "sugestao2"],
    "relevant_query": "query_original",
    "relevant_agent": "nome_do_agente"
}}

Se alguma informação não for aplicável ou identificável, use 'null' ou uma lista vazia para 'suggestions'.
"""

RAG_PROMPT_TEMPLATE = """Com base nos seguintes trechos de documentos, responda à pergunta do usuário de forma concisa e direta.
{instruction}
Pergunta: {query}

Documentos:
{context}

Resposta:"""

RAG_INSTRUCTIONS = {
    "breve": "Forneça um resumo muito conciso, com 1-2 frases, focando apenas nos pontos mais importantes.",
    "padrao": "Forneça um resumo conciso e direto, com 3-5 frases, cobrindo os principais aspectos.",
    "detalhado": "Forneça um resumo detalhado, com 6-8 frases, incluindo informações mais específicas e nuances."
}

PLANNING_AGENT_PROMPT = """
As a meticulous and strategic AI research planner, your task is to create a comprehensive research plan for the given topic.

**Topic:**
{topic}

**Instructions:**
1.  **Deconstruct the Topic:** Break down the main topic into a series of specific, answerable research questions.
2.  **Formulate Search Queries:** For each research question, devise a concise and effective search query that you would use in a search engine.
3.  **Output Format:** Structure your final output as a single JSON object. Do not add any text before or after the JSON object.

**JSON Output Structure:**
{{
  "research_topic": "{topic}",
  "research_questions": [
    {{
      "question": "Example research question?",
      "search_query": "example search query"
    }}
  ]
}}

Begin!
"""

SYNTHESIS_AGENT_PROMPT = """Você é um Agente de Síntese e Citação. Sua tarefa é gerar um resumo conciso e informativo do texto fornecido, respondendo à pergunta de pesquisa. Para cada frase no resumo que utilize informação do texto original, você DEVE incluir uma citação no formato [ID_DA_FONTE].
Se a informação necessária para responder à pergunta não estiver contida no texto fornecido, o valor da chave 'summary' no JSON de saída DEVE ser 'null'. Não invente ou infira informações que não estejam explicitamente presentes.
Texto para Resumir:
--- TEXTO ORIGINAL ---
{text}
--- FIM DO TEXTO ORIGINAL ---

Fontes Disponíveis:
--- FONTES ---
{formatted_sources}
--- FIM DAS FONTES ---

Pergunta de Pesquisa: {research_question}

Formato de Saída (JSON):
{{
    "summary": "Seu resumo com citações [ID_DA_FONTE]",
    "citations_used": [
        {{
            "id": "ID_DA_FONTE",
            "sentence_in_summary": "Frase do resumo que usa esta fonte"
        }}
    ]
}}

Certifique-se de que a saída seja um JSON válido e completo. Se uma frase no resumo não puder ser diretamente rastreada a uma fonte fornecida, não inclua uma citação para ela.
"""

CLAIM_EXTRACTION_AGENT_PROMPT = """Você é um agente de análise linguística. Sua tarefa é extrair todas as alegações factuais do texto fornecido.
Cada alegação deve ser representada como uma triplera JSON com "subject", "predicate" e "object".
O "predicate" deve ser uma frase verbal concisa em maiúsculas, representando a relação (ex: 'IS_A', 'CAUSES', 'TREATS', 'HAS_COMPLICATION').

Exemplo:
Texto de entrada: "A gastrectomia vertical, um tipo de cirurgia bariátrica, pode causar fístulas."
Saída JSON esperada:
[
    {{"subject": "gastrectomia vertical", "predicate": "IS_A", "object": "cirurgia bariátrica"}},
    {{"subject": "gastrectomia vertical", "predicate": "CAN_CAUSE", "object": "fístulas"}}
] 

--- TEXTO PARA ANÁLISE ---
{text}
--- FIM DO TEXTO ---

Sua resposta DEVE ser um array JSON válido. Se nenhuma alegação for encontrada, retorne um array vazio [].
"""

ANALYSIS_AGENT_PROMPT = """Você é um Agente de Análise e Classificação. Sua tarefa é avaliar o texto fornecido, extrair um resumo conciso, classificar seu nível de evidência e extrair palavras-chave relevantes.

Níveis de Evidência:
A: Evidência forte (ex: meta-análises de ensaios clínicos randomizados, revisões sistemáticas).
B: Evidência moderada (ex: ensaios clínicos randomizados individuais, estudos de coorte bem delineados).
C: Evidência limitada (ex: estudos caso-controle, séries de casos, estudos observacionais).
D: Opinião de especialista ou consenso (ex: diretrizes baseadas em consenso, opinião de comitês de especialistas).
E: Evidência anedótica, opinião pessoal ou sem suporte científico direto.

Texto para Análise:
--- TEXTO ---
{text}
--- FIM DO TEXTO ---

Formato de Saída (JSON):
{{
    "summary": "Um resumo conciso do texto, focado nos principais achados e conclusões.",
    "evidence_level": "A letra correspondente ao nível de evidência (A, B, C, D, ou E)",
    "justification": "Justificativa para a classificação do nível de evidência.",
    "keywords": ["lista", "de", "palavras-chave", "relevantes", "extraídas", "do", "texto"]
}}

Certifique-se de que a saída seja um JSON válido e completo. Se a informação não estiver presente, o valor da chave DEVE ser 'null' ou uma lista vazia para 'keywords'.
"""

# Prompt for the Routing Agent
ROUTING_AGENT_PROMPT = """
You are an expert routing agent. Your task is to choose the most appropriate tool to answer a given user query based on the tool's description.

**Available Tools:**
{tools_description}

**User Query:**
"{query}"

**Instructions:**
- Analyze the user query.
- Compare the query's intent with the description of each available tool.
- Choose the single best tool to handle the query.
- **Your output must be ONLY the name of the chosen tool and nothing else.** For example, if you choose the tool named 'brave_search', your response should be exactly `brave_search`.

What is the best tool for this query?
"""