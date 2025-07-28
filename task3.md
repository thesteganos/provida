# Novas Tasks de Melhoria

## Correções de Código

1. **Remover Resíduos de Prompt**
   - Arquivos afetados: `test_cli.py`, `test_rag.py`, `tests/test_settings.py`, `tests/test_web_search.py`, `tests/test_web_search_performance.py`, `fact_checking_service.py`, `src/app/cli.py`, `src/main.py` e demais arquivos onde aparecem trechos como `root@...`.
   - Objetivo: eliminar linhas de terminal acidentalmente copiadas para o código, garantindo que o código termine corretamente e siga o padrão PEP8.

2. **Ajustar `BraveSearch`**
   - Corrigir o método `search` em `src/app/tools/brave_search.py`, adicionando bloco `try/except` corretamente indentado para captura de `httpx.RequestError`.
   - Garantir docstring em português e retorno consistente em caso de erro.

3. **Importação Inválida em `neo4j_manager.py`**
   - Substituir a referência a `app.models.config_models` por um modelo existente (`Neo4jDatabaseSettings` dentro de `src/app/config/settings.py` ou outra estrutura equivalente).
   - Atualizar eventuais usos decorrentes.

## Qualidade e Documentação

4. **Padronizar Docstrings**
   - Revisar módulos principais (`src/app/cli.py`, `src/app/tools/*.py`, `neo4j_manager.py`, `fact_checking_service.py`) adicionando docstrings descritivas em português conforme orientação do projeto.

5. **Preparar Ambiente de Testes**
   - Documentar no `README.md` ou em novo script de instalação o passo para instalar dependências (`pip install -r requirements.txt`) antes de executar `pytest -q`.
   - Garantir que todos os testes rodem sem erros de importação após a instalação.

6. **Consertar Scripts Truncados**
   - Ajustar `setup.sh` para encerrar corretamente o bloco `if` e remover o texto extra no final do arquivo.
   - Corrigir `src/run_scheduler.sh` garantindo que o comando `python3 scheduler.py` esteja completo e em nova linha.

7. **Remover Execução Direta em Testes**
   - Nos testes unitários, eliminar blocos `if __name__ == '__main__':` com `unittest.main()`.
   - Os testes devem ser executados exclusivamente via `pytest`.

8. **Sanitizar `check_config.py`**
   - Excluir o resíduo de prompt no final do arquivo e adicionar docstring explicativa em português.

9. **Avaliar Arquivo Vazio `src/app/main.py`**
   - Definir se o módulo será implementado ou removido para evitar confusão na estrutura.

10. **Adicionar Ferramenta de Lint**
    - Incluir `flake8` ou `ruff` nas dependências de desenvolvimento e referenciar no `CONTRIBUTING.md`.

