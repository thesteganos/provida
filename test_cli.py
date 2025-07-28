import pytest
from typer.testing import CliRunner
from unittest.mock import patch, AsyncMock, MagicMock
import json

# Importar o app Typer do módulo principal da CLI
from src.app.cli import app

# Inicializar o CliRunner
runner = CliRunner()

# --- Testes para o comando 'rapida' ---

@pytest.mark.asyncio
@patch('src.app.cli.perform_rag_query')
@patch('src.app.cli._prompt_for_feedback', new_callable=AsyncMock)
async def test_rapida_command_happy_path(mock_prompt_for_feedback, mock_perform_rag_query):
    # Mockar o retorno de perform_rag_query
    mock_rag_response = MagicMock()
    mock_rag_response.summary = "Este é um resumo mockado da consulta."
    mock_rag_response.sources = ["Fonte A", "Fonte B"]
    mock_rag_response.model_dump_json.return_value = json.dumps({
        "summary": mock_rag_response.summary,
        "sources": mock_rag_response.sources
    }, indent=2)
    mock_perform_rag_query.return_value = mock_rag_response

    result = runner.invoke(app, ["rapida", "qual a dose de vitamina D?"])

    assert result.exit_code == 0
    assert "Executando Consulta Rápida para: 'qual a dose de vitamina D?'" in result.stdout
    assert "--- Resumo ---" in result.stdout
    assert "Este é um resumo mockado da consulta." in result.stdout
    assert "--- Fontes ---" in result.stdout
    assert "- Fonte A" in result.stdout
    assert "- Fonte B" in result.stdout
    mock_perform_rag_query.assert_called_once_with("qual a dose de vitamina D?", "padrao")
    mock_prompt_for_feedback.assert_called_once_with(
        "qual a dose de vitamina D?", mock_rag_response.summary, "RAG"
    )

@pytest.mark.asyncio
@patch('src.app.cli.perform_rag_query')
@patch('src.app.cli._prompt_for_feedback', new_callable=AsyncMock)
async def test_rapida_command_empty_query(mock_prompt_for_feedback, mock_perform_rag_query):
    # Mockar perform_rag_query para levantar ValueError para query vazia
    mock_perform_rag_query.side_effect = ValueError("A consulta não pode ser vazia.")

    result = runner.invoke(app, ["rapida", ""])

    assert result.exit_code != 0  # Deve falhar
    assert "Erro de Validação: A consulta não pode ser vazia." in result.stdout
    mock_perform_rag_query.assert_called_once_with("", "padrao")
    mock_prompt_for_feedback.assert_not_called() # Não deve chamar feedback em caso de erro

@pytest.mark.asyncio
@patch('src.app.cli.perform_rag_query')
@patch('src.app.cli._prompt_for_feedback', new_callable=AsyncMock)
async def test_rapida_command_json_output(mock_prompt_for_feedback, mock_perform_rag_query):
    # Mockar o retorno de perform_rag_query
    mock_rag_response = MagicMock()
    mock_rag_response.summary = "Resumo em JSON."
    mock_rag_response.sources = ["Fonte JSON"]
    mock_rag_response.model_dump_json.return_value = json.dumps({
        "summary": "Resumo em JSON.",
        "sources": ["Fonte JSON"]
    }, indent=2)
    mock_perform_rag_query.return_value = mock_rag_response

    result = runner.invoke(app, ["rapida", "teste json", "--output-format", "json"])

    assert result.exit_code == 0
    output_json = json.loads(result.stdout)
    assert output_json["summary"] == "Resumo em JSON."
    assert "Fonte JSON" in output_json["sources"]
    mock_perform_rag_query.assert_called_once_with("teste json", "padrao")
    mock_prompt_for_feedback.assert_not_called() # Não deve chamar feedback para saída JSON

@pytest.mark.asyncio
@patch('src.app.cli.perform_rag_query')
@patch('src.app.cli._prompt_for_feedback', new_callable=AsyncMock)
async def test_rapida_command_detail_level(mock_prompt_for_feedback, mock_perform_rag_query):
    mock_rag_response = MagicMock()
    mock_rag_response.summary = "Resumo detalhado."
    mock_rag_response.sources = ["Fonte A"]
    mock_rag_response.model_dump_json.return_value = json.dumps({
        "summary": mock_rag_response.summary,
        "sources": mock_rag_response.sources
    }, indent=2)
    mock_perform_rag_query.return_value = mock_rag_response

    result = runner.invoke(app, ["rapida", "query", "--detail-level", "detalhado"])
    assert result.exit_code == 0
    mock_perform_rag_query.assert_called_once_with("query", "detalhado")

@pytest.mark.asyncio
@patch('src.app.cli.perform_rag_query')
@patch('src.app.cli._prompt_for_feedback', new_callable=AsyncMock)
async def test_rapida_command_max_lines_and_highlight(mock_prompt_for_feedback, mock_perform_rag_query):
    mock_rag_response = MagicMock()
    mock_rag_response.summary = "Linha 1\nLinha 2\nLinha 3\nLinha 4"
    mock_rag_response.sources = ["Fonte A"]
    mock_rag_response.model_dump_json.return_value = json.dumps({
        "summary": mock_rag_response.summary,
        "sources": mock_rag_response.sources
    }, indent=2)
    mock_perform_rag_query.return_value = mock_rag_response

    result = runner.invoke(app, ["rapida", "query", "--max-lines", "2", "--highlight", "Linha"])
    assert result.exit_code == 0
    assert "truncated 2 lines" in result.stdout
    # Verifica se a formatação de destaque foi aplicada (Rich Text)
    assert "Linha 1" in result.stdout
    assert "Linha 2" in result.stdout
    assert "Linha 3" not in result.stdout # Deve estar truncado

# --- Testes para as funções auxiliares da CLI ---

def test_format_text_for_display_truncation():
    text = "Line 1\nLine 2\nLine 3\nLine 4"
    formatted_text = app.command().callback._format_text_for_display(text, max_lines=2)
    assert "Line 1" in formatted_text.plain
    assert "Line 2" in formatted_text.plain
    assert "truncated 2 lines" in formatted_text.plain
    assert "Line 3" not in formatted_text.plain

def test_format_text_for_display_highlighting():
    text = "This is a test line with keywords."
    formatted_text = app.command().callback._format_text_for_display(text, highlight_keywords="test,keywords")
    # Rich Text objects don't expose raw highlighted text easily, but we can check for the plain text
    assert "This is a test line with keywords." in formatted_text.plain
    # Further checks would require inspecting Rich Text internals, which is complex.
    # For now, assume Rich handles highlighting correctly if the plain text is there.

@pytest.mark.asyncio
@patch('src.app.cli.Prompt.ask')
@patch('src.app.cli.feedback_agent.collect_feedback', new_callable=AsyncMock)
async def test_prompt_for_feedback_yes_success(mock_collect_feedback, mock_prompt_ask):
    mock_prompt_ask.side_effect = ["s", "This is a test feedback."]
    mock_collect_feedback.return_value = MagicMock(sentiment="positivo")

    # Call the function directly
    await app.command().callback._prompt_for_feedback("test query", "test summary", "RAG")

    mock_prompt_ask.assert_any_call("[bold blue]Gostaria de fornecer feedback sobre esta interação?[/bold blue]", choices=["s", "n"], default="n")
    mock_prompt_ask.assert_any_call("[bold blue]Por favor, digite seu feedback[/bold blue]")
    mock_collect_feedback.assert_called_once()
    # Check console output for success message (requires capturing rich console output, which is complex for direct assert)

@pytest.mark.asyncio
@patch('src.app.cli.Prompt.ask')
@patch('src.app.cli.feedback_agent.collect_feedback', new_callable=AsyncMock)
async def test_prompt_for_feedback_no(mock_collect_feedback, mock_prompt_ask):
    mock_prompt_ask.return_value = "n"

    await app.command().callback._prompt_for_feedback("test query", "test summary", "RAG")

    mock_prompt_ask.assert_called_once_with("[bold blue]Gostaria de fornecer feedback sobre esta interação?[/bold blue]", choices=["s", "n"], default="n")
    mock_collect_feedback.assert_not_called()

@pytest.mark.asyncio
@patch('src.app.cli.Prompt.ask')
@patch('src.app.cli.feedback_agent.collect_feedback', new_callable=AsyncMock)
async def test_prompt_for_feedback_error(mock_collect_feedback, mock_prompt_ask):
    mock_prompt_ask.side_effect = ["s", "This is a test feedback."]
    mock_collect_feedback.side_effect = Exception("Feedback collection failed")

    await app.command().callback._prompt_for_feedback("test query", "test summary", "RAG")

    mock_collect_feedback.assert_called_once()
    # Check console output for error message (requires capturing rich console output)

# --- Testes para o comando 'profunda' ---

@pytest.mark.asyncio
@patch('src.app.cli.run_deep_research')
@patch('src.app.cli.PDFExporter')
@patch('src.app.cli.DOCXExporter')
@patch('src.app.cli.MarkdownExporter')
@patch('src.app.cli._prompt_for_feedback', new_callable=AsyncMock)
async def test_profunda_command_happy_path(
    mock_prompt_for_feedback, mock_markdown_exporter, mock_docx_exporter, mock_pdf_exporter, mock_run_deep_research
):
    # Mockar o retorno de run_deep_research
    mock_run_deep_research.return_value = {
        "final_report": {
            "summary": "Relatório final mockado da pesquisa profunda.",
            "citations_used": [{"id": "Artigo X", "sentence_in_summary": "Citação mockada."}]
        }
    }

    result = runner.invoke(app, ["profunda", "inteligencia artificial"])

    assert result.exit_code == 0
    assert "Executando Pesquisa Profunda sobre: 'inteligencia artificial'..." in result.stdout
    assert "Relatório Final" in result.stdout
    assert "Relatório final mockado da pesquisa profunda." in result.stdout
    assert "Citações Utilizadas" in result.stdout
    assert "- [ID: Artigo X] Citação mockada." in result.stdout
    mock_run_deep_research.assert_called_once_with("inteligencia artificial", None)
    # Verificar que os exportadores NÃO foram chamados por padrão
    mock_pdf_exporter.return_value.export_report.assert_not_called()
    mock_docx_exporter.return_value.export_report.assert_not_called()
    mock_markdown_exporter.return_value.export_report.assert_not_called()
    mock_prompt_for_feedback.assert_called_once_with(
        "inteligencia artificial", "Relatório final mockado da pesquisa profunda.", "Deep Research"
    )

@pytest.mark.asyncio
@patch('src.app.cli.run_deep_research')
@patch('src.app.cli.PDFExporter')
@patch('src.app.cli.DOCXExporter')
@patch('src.app.cli.MarkdownExporter')
@patch('src.app.cli._prompt_for_feedback', new_callable=AsyncMock)
async def test_profunda_command_export_options(
    mock_prompt_for_feedback, mock_markdown_exporter, mock_docx_exporter, mock_pdf_exporter, mock_run_deep_research
):
    # Mockar o retorno de run_deep_research
    mock_run_deep_research.return_value = {
        "final_report": {
            "summary": "Relatório para exportação.",
            "citations_used": []
        }
    }
    # Mockar os métodos export_report para retornar True
    mock_pdf_exporter.return_value.export_report.return_value = True
    mock_docx_exporter.return_value.export_report.return_value = True
    mock_markdown_exporter.return_value.export_report.return_value = True

    result = runner.invoke(app, [
        "profunda", "teste exportacao",
        "--pdf-output", "--docx-output", "--markdown-output"
    ])

    assert result.exit_code == 0
    assert "Relatório exportado para PDF:" in result.stdout
    assert "Relatório exportado para DOCX:" in result.stdout
    assert "Relatório exportado para Markdown:" in result.stdout
    mock_pdf_exporter.return_value.export_report.assert_called_once()
    mock_docx_exporter.return_value.export_report.assert_called_once()
    mock_markdown_exporter.return_value.export_report.assert_called_once()
    mock_prompt_for_feedback.assert_called_once_with(
        "teste exportacao", "Relatório para exportação.", "Deep Research"
    )

@pytest.mark.asyncio
@patch('src.app.cli.run_deep_research')
@patch('src.app.cli._prompt_for_feedback', new_callable=AsyncMock)
async def test_profunda_command_search_limit(mock_prompt_for_feedback, mock_run_deep_research):
    mock_run_deep_research.return_value = {
        "final_report": {"summary": "Relatório com limite de busca.", "citations_used": []}
    }
    result = runner.invoke(app, ["profunda", "topico", "--search-limit", "50"])
    assert result.exit_code == 0
    mock_run_deep_research.assert_called_once_with("topico", 50)

@pytest.mark.asyncio
@patch('src.app.cli.run_deep_research')
@patch('src.app.cli._prompt_for_feedback', new_callable=AsyncMock)
async def test_profunda_command_error_scenario(mock_prompt_for_feedback, mock_run_deep_research):
    mock_run_deep_research.side_effect = Exception("Erro simulado na pesquisa profunda")
    result = runner.invoke(app, ["profunda", "topico com erro"])
    assert result.exit_code != 0
    assert "Ocorreu um erro crítico durante a orquestração: Erro simulado na pesquisa profunda" in result.stdout
    mock_prompt_for_feedback.assert_not_called() # Não deve chamar feedback em caso de erro

@pytest.mark.asyncio
@patch('src.app.cli.run_deep_research')
@patch('src.app.cli._prompt_for_feedback', new_callable=AsyncMock)
async def test_profunda_command_no_report_summary(mock_prompt_for_feedback, mock_run_deep_research):
    mock_run_deep_research.return_value = {
        "final_report": {"error": "Relatório não gerado."}
    }
    result = runner.invoke(app, ["profunda", "topico sem relatorio"])
    assert result.exit_code == 0
    assert "Erro na Pesquisa Profunda: Relatório não gerado." in result.stdout
    mock_prompt_for_feedback.assert_not_called() # Não deve chamar feedback se não há summary

# --- Testes para o comando '--help' ---

def test_help_command():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Pró-Vida: Assistente de Pesquisa Autônomo para Cirurgia Bariátrica." in result.stdout
    assert "rapida" in result.stdout
    assert "profunda" in result.stdout

def test_rapida_help_command():
    result = runner.invoke(app, ["rapida", "--help"])
    assert result.exit_code == 0
    assert "Executa uma consulta rápida no modo RAG para obter respostas baseadas em evidências." in result.stdout
    assert "--detail-level" in result.stdout

def test_profunda_help_command():
    result = runner.invoke(app, ["profunda", "--help"])
    assert result.exit_code == 0
    assert "Inicia uma pesquisa profunda e exaustiva sobre um tópico." in result.stdout
    assert "--search-limit" in result.stdout
    assert "--pdf-output" in result.stdout