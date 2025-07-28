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
async def test_rapida_command_happy_path(mock_perform_rag_query):
    # Mockar o retorno de perform_rag_query
    mock_rag_response = MagicMock()
    mock_rag_response.summary = "Este é um resumo mockado da consulta."
    mock_rag_response.sources = ["Fonte A", "Fonte B"]
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

@pytest.mark.asyncio
@patch('src.app.cli.perform_rag_query')
async def test_rapida_command_empty_query(mock_perform_rag_query):
    # Mockar perform_rag_query para levantar ValueError para query vazia
    mock_perform_rag_query.side_effect = ValueError("A consulta não pode ser vazia.")

    result = runner.invoke(app, ["rapida", ""])

    assert result.exit_code != 0  # Deve falhar
    assert "Erro de Validação: A consulta não pode ser vazia." in result.stdout
    mock_perform_rag_query.assert_called_once_with("", "padrao")

@pytest.mark.asyncio
@patch('src.app.cli.perform_rag_query')
async def test_rapida_command_json_output(mock_perform_rag_query):
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

# --- Testes para o comando 'profunda' ---

@pytest.mark.asyncio
@patch('src.app.cli.run_deep_research')
@patch('src.app.cli.PDFExporter')
@patch('src.app.cli.DOCXExporter')
@patch('src.app.cli.MarkdownExporter')
async def test_profunda_command_happy_path(
    mock_markdown_exporter, mock_docx_exporter, mock_pdf_exporter, mock_run_deep_research
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

@pytest.mark.asyncio
@patch('src.app.cli.run_deep_research')
@patch('src.app.cli.PDFExporter')
@patch('src.app.cli.DOCXExporter')
@patch('src.app.cli.MarkdownExporter')
async def test_profunda_command_export_options(
    mock_markdown_exporter, mock_docx_exporter, mock_pdf_exporter, mock_run_deep_research
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
