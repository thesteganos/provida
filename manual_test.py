import asyncio
import logging
import os
import pprint
from dotenv import load_dotenv

from src.app.orchestrator import run_deep_research
from src.app.config.logging_config import setup_logging

async def main():
    """
    Ponto de entrada para o teste manual do fluxo de pesquisa profunda.
    """
    # Carrega as variáveis de ambiente de um arquivo .env na raiz do projeto.
    # Crie um arquivo .env e adicione sua GOOGLE_API_KEY nele.
    # Exemplo de .env:
    # GOOGLE_API_KEY=sua_chave_api_aqui
    load_dotenv()

    # Verifica se a chave da API do Google está configurada.
    if not os.getenv("GOOGLE_API_KEY"):
        logging.error("A variável de ambiente GOOGLE_API_KEY não está definida.")
        logging.error("Por favor, crie um arquivo .env e adicione GOOGLE_API_KEY=sua_chave.")
        return

    # Configura o sistema de logging para exibir a saída do processo.
    setup_logging()
    logger = logging.getLogger(__name__)

    # Tópico de pesquisa para o teste.
    # test_topic = "Quais são os efeitos colaterais da gastrectomia vertical?"
    test_topic = "Impacto da inteligência artificial na detecção precoce de doenças."

    logger.info(f"--- Iniciando teste de pesquisa profunda para o tópico: '{test_topic}' ---")

    try:
        # Executa o fluxo de pesquisa.
        final_state = await run_deep_research(topic=test_topic)

        logger.info("--- Teste de pesquisa profunda concluído ---")

        # Imprime o estado final de forma legível.
        print("\n" + "="*50)
        print("            ESTADO FINAL DO GRAFO")
        print("="*50 + "\n")
        pprint.pprint(final_state)
        print("\n" + "="*50 + "\n")

    except Exception as e:
        logger.error(f"Ocorreu um erro durante o teste de pesquisa profunda: {e}", exc_info=True)

if __name__ == "__main__":
    # Executa a função main assíncrona.
    asyncio.run(main())
