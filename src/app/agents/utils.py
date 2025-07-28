import re
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def extract_json_from_response(text: str) -> Dict[str, Any]:
    """
    Extrai um bloco de código JSON de uma string de resposta de um LLM.

    Tenta encontrar um bloco de código JSON delimitado por ```json e ```.
    Se não encontrar, assume que a string inteira é uma tentativa de JSON.

    Args:
        text (str): A string de texto da qual extrair o JSON.

    Returns:
        Dict[str, Any]: O dicionário JSON extraído.

    Raises:
        ValueError: Se nenhum JSON válido puder ser decodificado do texto.
    """
    # Procura por um bloco de código JSON delimitado por ```json e ```
    # O padrão é flexível para espaços em branco e cobre o objeto JSON inteiro.
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        json_str = match.group(1)
    else:
        # Fallback: se nenhum bloco formatado for encontrado, tenta analisar a string inteira.
        # Isso pode ser útil se o LLM retornar JSON puro sem a formatação do bloco de código.
        json_str = text

    try:
        # Tenta carregar a string JSON em um dicionário Python
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"Falha ao decodificar JSON. Erro: {e}\nTexto recebido:\n---\n{text}\n---")
        # Lança um erro claro para o chamador tratar.
        raise ValueError("A resposta do LLM não continha um JSON válido.") from e
