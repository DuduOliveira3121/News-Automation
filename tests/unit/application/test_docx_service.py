"""Testes unitários do DocxService.

Estratégia de isolamento
------------------------
- O ``NewsParser`` é substituído por um ``MagicMock`` para que o DocxService
  seja testado de forma independente da lógica de parsing.
- Nos testes que exercitam o caminho feliz, um arquivo ``.docx`` mínimo é
  gravado em disco via ``tmp_path`` para que ``validate_file`` passe sem
  ter de ser contornado.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, call

import docx
import pytest

from src.application.dtos.news_dto import ParsedNewsDTO
from src.application.services.docx_service import DocxService
from src.infrastructure.parsers.news_parser import NewsParser, Noticia


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def docx_on_disk(tmp_path: Path) -> Path:
    """Arquivo .docx mínimo gravado no disco para que ``validate_file`` passe."""
    path = tmp_path / "boletim.docx"
    docx.Document().save(str(path))
    return path


def _make_noticia(titulo: str = "Título", corpo: str = "Corpo", indice: int = 1) -> Noticia:
    return Noticia(titulo=titulo, corpo=corpo, arquivo_origem="boletim.docx", indice=indice)


# ---------------------------------------------------------------------------
# Testes de validate_file
# ---------------------------------------------------------------------------


class TestDocxServiceValidateFile:
    """Testes diretos do método validate_file."""

    def test_raises_file_not_found_for_missing_file(self, tmp_path: Path) -> None:
        service = DocxService()
        missing = tmp_path / "nao_existe.docx"

        with pytest.raises(FileNotFoundError, match="Arquivo não encontrado"):
            service.validate_file(missing)

    def test_raises_value_error_for_wrong_extension(self, tmp_path: Path) -> None:
        service = DocxService()
        wrong = tmp_path / "arquivo.pdf"
        wrong.touch()

        with pytest.raises(ValueError, match="Extensão inválida"):
            service.validate_file(wrong)

    def test_does_not_raise_for_existing_docx(self, docx_on_disk: Path) -> None:
        service = DocxService()

        # Não deve lançar exceção
        service.validate_file(docx_on_disk)


# ---------------------------------------------------------------------------
# Testes de extract_news — caminhos de erro
# ---------------------------------------------------------------------------


class TestDocxServiceExtractNewsErrors:
    """Testes de propagação de erros em extract_news."""

    def test_raises_file_not_found_when_file_is_missing(self, tmp_path: Path) -> None:
        service = DocxService()
        missing = tmp_path / "nao_existe.docx"

        with pytest.raises(FileNotFoundError):
            service.extract_news(missing)

    def test_raises_value_error_for_wrong_extension(self, tmp_path: Path) -> None:
        service = DocxService()
        wrong = tmp_path / "arquivo.csv"
        wrong.touch()

        with pytest.raises(ValueError, match="Extensão inválida"):
            service.extract_news(wrong)

    def test_raises_value_error_when_parser_returns_empty_list(
        self, docx_on_disk: Path
    ) -> None:
        mock_parser = MagicMock(spec=NewsParser)
        mock_parser.parse.return_value = []
        service = DocxService(parser=mock_parser)

        with pytest.raises(ValueError, match="Nenhuma notícia encontrada"):
            service.extract_news(docx_on_disk)


# ---------------------------------------------------------------------------
# Testes de extract_news — caminho feliz
# ---------------------------------------------------------------------------


class TestDocxServiceExtractNewsHappyPath:
    """Testes do comportamento correto de extract_news."""

    def test_returns_list_of_parsed_news_dtos(self, docx_on_disk: Path) -> None:
        mock_parser = MagicMock(spec=NewsParser)
        mock_parser.parse.return_value = [_make_noticia()]
        service = DocxService(parser=mock_parser)

        result = service.extract_news(docx_on_disk)

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], ParsedNewsDTO)

    def test_dto_fields_match_noticia_fields(self, docx_on_disk: Path) -> None:
        noticia = _make_noticia(titulo="Exclusivo", corpo="Detalhes do fato.")
        mock_parser = MagicMock(spec=NewsParser)
        mock_parser.parse.return_value = [noticia]
        service = DocxService(parser=mock_parser)

        dtos = service.extract_news(docx_on_disk)

        assert dtos[0].title == "Exclusivo"
        assert dtos[0].content == "Detalhes do fato."
        assert dtos[0].source_file == "boletim.docx"

    def test_multiple_noticias_produce_multiple_dtos(self, docx_on_disk: Path) -> None:
        mock_parser = MagicMock(spec=NewsParser)
        mock_parser.parse.return_value = [
            _make_noticia("Notícia 1", "Corpo 1", indice=1),
            _make_noticia("Notícia 2", "Corpo 2", indice=2),
            _make_noticia("Notícia 3", "Corpo 3", indice=3),
        ]
        service = DocxService(parser=mock_parser)

        dtos = service.extract_news(docx_on_disk)

        assert len(dtos) == 3
        assert [d.title for d in dtos] == ["Notícia 1", "Notícia 2", "Notícia 3"]

    def test_parser_is_called_with_the_file_path(self, docx_on_disk: Path) -> None:
        mock_parser = MagicMock(spec=NewsParser)
        mock_parser.parse.return_value = [_make_noticia()]
        service = DocxService(parser=mock_parser)

        service.extract_news(docx_on_disk)

        mock_parser.parse.assert_called_once_with(docx_on_disk)

    def test_order_of_dtos_matches_order_of_noticias(self, docx_on_disk: Path) -> None:
        noticias = [_make_noticia(titulo=f"N{i}", indice=i) for i in range(1, 6)]
        mock_parser = MagicMock(spec=NewsParser)
        mock_parser.parse.return_value = noticias
        service = DocxService(parser=mock_parser)

        dtos = service.extract_news(docx_on_disk)

        assert [d.title for d in dtos] == [f"N{i}" for i in range(1, 6)]


# ---------------------------------------------------------------------------
# Testes de instanciação do DocxService
# ---------------------------------------------------------------------------


class TestDocxServiceInit:
    """Testes do construtor do DocxService."""

    def test_default_parser_is_created_when_none_provided(self) -> None:
        service = DocxService()

        assert isinstance(service._parser, NewsParser)

    def test_custom_parser_is_used_when_provided(self) -> None:
        mock_parser = MagicMock(spec=NewsParser)
        service = DocxService(parser=mock_parser)

        assert service._parser is mock_parser
