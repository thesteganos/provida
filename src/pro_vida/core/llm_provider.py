import os
import google.generativeai as genai
from pro_vida.config.settings import settings

# Configura a API key do Google a partir de variáveis de ambiente
# A aplicação principal deverá garantir que python-dotenv seja carregado
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("A variável de ambiente GOOGLE_API_KEY não está definida.")

genai.configure(api_key=api_key)

def get_llm_model(model_name: str):
    """
    Retorna uma instância de um modelo generativo do Google.

    Args:
        model_name (str): O nome do modelo a ser carregado (ex: 'gemini-1.5-pro').

    Returns:
        Um objeto GenerativeModel.
    """
    # Valida se o modelo solicitado está na lista de modelos do config
    if model_name not in settings['models'].values():
        raise ValueError(f"Modelo '{model_name}' não está definido no config.yaml")

    # Isso pode ser expandido para carregar configurações de segurança, etc.
    model = genai.GenerativeModel(model_name)
    return model

def get_model_for_agent(agent_name: str):
    """
    Retorna o modelo de LLM configurado para um agente específico.

    Args:
        agent_name (str): O nome do agente (ex: 'planning_agent').

    Returns:
        Um objeto GenerativeModel.
    """
    model_name = settings['models'].get(agent_name)
    if not model_name:
        raise ValueError(f"Nenhum modelo configurado para o agente '{agent_name}' no config.yaml")

    return get_llm_model(model_name)