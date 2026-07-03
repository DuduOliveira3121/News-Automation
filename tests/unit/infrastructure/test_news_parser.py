"""Testes unitários do NewsParser.

Os testes criam documentos Word em memória (via io.BytesIO) para garantir
isolamento total do sistema de arquivos.
"""
from __future__ import annotations

import io
from pathlib import Path
from unittest.mock import patch

import docx
import pytest

from src.infrastructure.parsers.news_parser import NewsParser, Noticia


# ---------------------------------------------------------------------------
# Helpers de fixture
# ---------------------------------------------------------------------------


def _build_docx(*items: tuple[str, list[str]]) -> io.BytesIO:
    """Cria um .docx em memória a partir de pares (título, [parágrafos]).

    Args:
        items: Sequência de tuplas ``(titulo, [par1, par2, ...])``.
            Um título vazio ("") insere um Heading 1 sem texto.

    Returns:
        Buffer ``BytesIO`` pronto para ser lido pelo python-docx.
    """
    document = docx.Document()
    for title, body_paragraphs in items:
        document.add_heading(title, level=1)
        for para in body_paragraphs:
            document.add_paragraph(para)
    buf = io.BytesIO()
    document.save(buf)
    buf.seek(0)
    return buf


def _parser_from_buf(buf: io.BytesIO, filename: str = "test.docx") -> list[Noticia]:
    """Abre um buffer BytesIO como Document e executa o parser internamente."""
    document = docx.Document(buf)
    parser = NewsParser()
    return parser._extract(document, source_name=filename)


# ---------------------------------------------------------------------------
# Testes da classe Noticia
# ---------------------------------------------------------------------------


class TestNoticia:
    """Testes básicos da dataclass Noticia."""

    def test_fields_are_assigned_correctly(self) -> None:
        n = Noticia(titulo="T", corpo="C", arquivo_origem="f.docx", indice=1)

        assert n.titulo == "T"
        assert n.corpo == "C"
        assert n.arquivo_origem == "f.docx"
        assert n.indice == 1

    def test_default_indice_is_zero(self) -> None:
        n = Noticia(titulo="T", corpo="C", arquivo_origem="f.docx")

        assert n.indice == 0


# ---------------------------------------------------------------------------
# Testes do NewsParser — validação de arquivos
# ---------------------------------------------------------------------------


class TestNewsParserValidation:
    """Testes de validação de entrada do NewsParser."""

    def test_raises_file_not_found_for_missing_file(self, tmp_path: Path) -> None:
        parser = NewsParser()
        missing = tmp_path / "nao_existe.docx"

        with pytest.raises(FileNotFoundError, match="Arquivo não encontrado"):
            parser.parse(missing)

    def test_raises_value_error_for_wrong_extension(self, tmp_path: Path) -> None:
        parser = NewsParser()
        wrong = tmp_path / "arquivo.txt"
        wrong.touch()

        with pytest.raises(ValueError, match="Extensão inválida"):
            parser.parse(wrong)

    def test_raises_value_error_for_corrupted_file(self, tmp_path: Path) -> None:
        parser = NewsParser()
        corrupted = tmp_path / "corrompido.docx"
        corrupted.write_bytes(b"not a valid docx content")

        with pytest.raises(ValueError, match="Não foi possível abrir"):
            parser.parse(corrupted)


# ---------------------------------------------------------------------------
# Testes do NewsParser — extração de conteúdo
# ---------------------------------------------------------------------------


class TestNewsParserExtraction:
    """Testes de extração de notícias a partir de documentos em memória."""

    def test_single_news_is_extracted(self) -> None:
        buf = _build_docx(("Título da Notícia", ["Parágrafo 1.", "Parágrafo 2."]))
        noticias = _parser_from_buf(buf)

        assert len(noticias) == 1
        assert noticias[0].titulo == "Título da Notícia"

    def test_multiple_news_are_extracted_in_order(self) -> None:
        buf = _build_docx(
            ("Notícia A", ["Corpo A"]),
            ("Notícia B", ["Corpo B"]),
            ("Notícia C", ["Corpo C"]),
        )
        noticias = _parser_from_buf(buf)

        assert len(noticias) == 3
        assert [n.titulo for n in noticias] == ["Notícia A", "Notícia B", "Notícia C"]

    def test_indice_is_sequential_starting_at_one(self) -> None:
        buf = _build_docx(
            ("Notícia 1", ["Corpo"]),
            ("Notícia 2", ["Corpo"]),
        )
        noticias = _parser_from_buf(buf)

        assert [n.indice for n in noticias] == [1, 2]

    def test_body_paragraphs_are_joined_with_double_newline(self) -> None:
        buf = _build_docx(("Notícia", ["Primeiro parágrafo.", "Segundo parágrafo."]))
        noticias = _parser_from_buf(buf)

        assert noticias[0].corpo == "Primeiro parágrafo.\n\nSegundo parágrafo."

    def test_empty_body_paragraphs_are_ignored(self) -> None:
        buf = _build_docx(("Notícia", ["", "Parágrafo real.", ""]))
        noticias = _parser_from_buf(buf)

        assert noticias[0].corpo == "Parágrafo real."

    def test_news_with_no_body_has_empty_corpo(self) -> None:
        buf = _build_docx(("Notícia Sem Corpo", []))
        noticias = _parser_from_buf(buf)

        assert len(noticias) == 1
        assert noticias[0].corpo == ""

    def test_content_before_first_heading_is_ignored(self) -> None:
        document = docx.Document()
        document.add_paragraph("Este parágrafo não pertence a nenhuma notícia.")
        document.add_heading("Primeira Notícia", level=1)
        document.add_paragraph("Corpo da notícia.")
        buf = io.BytesIO()
        document.save(buf)
        buf.seek(0)

        noticias = _parser_from_buf(buf)

        assert len(noticias) == 1
        assert noticias[0].titulo == "Primeira Notícia"

    def test_empty_heading1_is_skipped(self) -> None:
        buf = _build_docx(("", ["Corpo órfão"]), ("Notícia Válida", ["Corpo"]))
        noticias = _parser_from_buf(buf)

        # Heading 1 vazio deve ser descartado
        assert len(noticias) == 1
        assert noticias[0].titulo == "Notícia Válida"

    def test_document_with_no_heading1_returns_empty_list(self) -> None:
        document = docx.Document()
        document.add_paragraph("Apenas texto comum, sem heading.")
        buf = io.BytesIO()
        document.save(buf)
        buf.seek(0)

        noticias = _parser_from_buf(buf)

        assert noticias == []

    def test_source_file_is_preserved_in_noticia(self) -> None:
        buf = _build_docx(("Notícia", ["Corpo"]))
        noticias = _parser_from_buf(buf, filename="boletim.docx")

        assert noticias[0].arquivo_origem == "boletim.docx"

    def test_heading2_is_treated_as_body_not_new_news(self) -> None:
        document = docx.Document()
        document.add_heading("Notícia Principal", level=1)
        document.add_paragraph("Introdução.")
        document.add_heading("Sub-seção", level=2)
        document.add_paragraph("Detalhe da sub-seção.")
        buf = io.BytesIO()
        document.save(buf)
        buf.seek(0)

        noticias = _parser_from_buf(buf)

        assert len(noticias) == 1
        assert "Sub-seção" in noticias[0].corpo


# ---------------------------------------------------------------------------
# Testes do NewsParser — integração com arquivo real no disco
# ---------------------------------------------------------------------------


class TestNewsParserWithRealFile:
    """Testes que escrevem um .docx no sistema de arquivos temporário."""

    def test_parse_reads_file_from_disk(self, tmp_path: Path) -> None:
        buf = _build_docx(
            ("Notícia do Disco", ["Conteúdo gravado no disco."]),
        )
        file_path = tmp_path / "teste.docx"
        file_path.write_bytes(buf.read())

        parser = NewsParser()
        noticias = parser.parse(file_path)

        assert len(noticias) == 1
        assert noticias[0].titulo == "Notícia do Disco"
        assert noticias[0].corpo == "Conteúdo gravado no disco."

    def test_parse_multiple_news_from_disk(self, tmp_path: Path) -> None:
        buf = _build_docx(
            ("Esporte", ["Resultado dos jogos."]),
            ("Política", ["Sessão no congresso."]),
            ("Economia", ["Índice subiu."]),
        )
        file_path = tmp_path / "boletim.docx"
        file_path.write_bytes(buf.read())

        parser = NewsParser()
        noticias = parser.parse(file_path)

        assert len(noticias) == 3
        assert noticias[1].titulo == "Política"


# ---------------------------------------------------------------------------
# Testes do NewsParser — extração de tabelas
# ---------------------------------------------------------------------------


class TestNewsParserTableExtraction:
    """Testes do comportamento do parser quando o documento contém tabelas."""

    def test_table_in_body_is_extracted_as_text(self) -> None:
        document = docx.Document()
        document.add_heading("Notícia com Tabela", level=1)
        table = document.add_table(rows=2, cols=2)
        table.cell(0, 0).text = "Cabeçalho A"
        table.cell(0, 1).text = "Cabeçalho B"
        table.cell(1, 0).text = "Valor 1"
        table.cell(1, 1).text = "Valor 2"
        buf = io.BytesIO()
        document.save(buf)
        buf.seek(0)

        noticias = _parser_from_buf(buf)

        assert len(noticias) == 1
        assert "Cabeçalho A" in noticias[0].corpo
        assert "Valor 1" in noticias[0].corpo

    def test_table_cells_joined_by_tab_and_rows_by_newline(self) -> None:
        document = docx.Document()
        document.add_heading("Notícia", level=1)
        table = document.add_table(rows=2, cols=2)
        table.cell(0, 0).text = "A"
        table.cell(0, 1).text = "B"
        table.cell(1, 0).text = "C"
        table.cell(1, 1).text = "D"
        buf = io.BytesIO()
        document.save(buf)
        buf.seek(0)

        noticias = _parser_from_buf(buf)

        assert "A\tB" in noticias[0].corpo
        assert "C\tD" in noticias[0].corpo

    def test_empty_table_is_not_added_to_body(self) -> None:
        document = docx.Document()
        document.add_heading("Notícia", level=1)
        document.add_paragraph("Parágrafo real.")
        # Tabela com células vazias
        document.add_table(rows=1, cols=2)
        buf = io.BytesIO()
        document.save(buf)
        buf.seek(0)

        noticias = _parser_from_buf(buf)

        # Apenas o parágrafo deve estar no corpo; a tabela vazia é descartada.
        assert noticias[0].corpo == "Parágrafo real."

    def test_table_before_first_heading_is_ignored(self) -> None:
        document = docx.Document()
        # Tabela antes de qualquer Heading 1 — deve ser ignorada.
        table = document.add_table(rows=1, cols=1)
        table.cell(0, 0).text = "Dado órfão"
        document.add_heading("Notícia", level=1)
        document.add_paragraph("Corpo da notícia.")
        buf = io.BytesIO()
        document.save(buf)
        buf.seek(0)

        noticias = _parser_from_buf(buf)

        assert len(noticias) == 1
        assert "Dado órfão" not in noticias[0].corpo

    def test_table_followed_by_paragraph_in_same_news(self) -> None:
        document = docx.Document()
        document.add_heading("Notícia", level=1)
        document.add_paragraph("Introdução.")
        table = document.add_table(rows=1, cols=1)
        table.cell(0, 0).text = "Dado da tabela"
        document.add_paragraph("Conclusão.")
        buf = io.BytesIO()
        document.save(buf)
        buf.seek(0)

        noticias = _parser_from_buf(buf)

        corpo = noticias[0].corpo
        assert "Introdução." in corpo
        assert "Dado da tabela" in corpo
        assert "Conclusão." in corpo
