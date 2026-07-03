"""Testes unitários do ParseDocxUseCase.

Estratégia de isolamento
------------------------
- ``DocxService`` e ``INewsRepository`` são substituídos por ``MagicMock``
  para que o use-case seja testado sem depender de arquivos ou banco de dados.
- O mock de ``save`` retorna a própria entidade recebida por padrão.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, call

import pytest

from src.application.dtos.news_dto import ParsedNewsDTO
from src.application.services.docx_service import DocxService
from src.application.use_cases.parse_docx_use_case import ParseDocxUseCase
from src.domain.entities.news import News, NewsStatus
from src.domain.interfaces.news_repository import INewsRepository


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_service() -> MagicMock:
    """Mock do DocxService."""
    return MagicMock(spec=DocxService)


@pytest.fixture
def mock_repo() -> MagicMock:
    """Mock do INewsRepository; save devolve a entidade recebida."""
    repo = MagicMock(spec=INewsRepository)
    repo.save.side_effect = lambda news: news
    return repo


@pytest.fixture
def use_case(mock_service: MagicMock, mock_repo: MagicMock) -> ParseDocxUseCase:
    return ParseDocxUseCase(docx_service=mock_service, news_repository=mock_repo)


def _dto(title: str = "Título", content: str = "Corpo", source: str = "f.docx") -> ParsedNewsDTO:
    return ParsedNewsDTO(title=title, content=content, source_file=source)


# ---------------------------------------------------------------------------
# Testes de propagação de erros
# ---------------------------------------------------------------------------


class TestParseDocxUseCaseErrors:
    """Testes de propagação de exceções vindas do DocxService."""

    def test_propagates_file_not_found(
        self, use_case: ParseDocxUseCase, mock_service: MagicMock
    ) -> None:
        mock_service.extract_news.side_effect = FileNotFoundError("Arquivo não encontrado")

        with pytest.raises(FileNotFoundError):
            use_case.execute(Path("nao_existe.docx"))

    def test_propagates_value_error_on_invalid_file(
        self, use_case: ParseDocxUseCase, mock_service: MagicMock
    ) -> None:
        mock_service.extract_news.side_effect = ValueError("Extensão inválida")

        with pytest.raises(ValueError):
            use_case.execute(Path("arquivo.txt"))

    def test_propagates_value_error_when_no_news_found(
        self, use_case: ParseDocxUseCase, mock_service: MagicMock
    ) -> None:
        mock_service.extract_news.side_effect = ValueError("Nenhuma notícia encontrada")

        with pytest.raises(ValueError, match="Nenhuma notícia"):
            use_case.execute(Path("vazio.docx"))


# ---------------------------------------------------------------------------
# Testes do caminho feliz — uma notícia
# ---------------------------------------------------------------------------


class TestParseDocxUseCaseSingleNews:
    """Testes de execute com um único DTO retornado pelo serviço."""

    def test_returns_list_with_one_news(
        self, use_case: ParseDocxUseCase, mock_service: MagicMock
    ) -> None:
        mock_service.extract_news.return_value = [_dto()]

        result = use_case.execute(Path("boletim.docx"))

        assert isinstance(result, list)
        assert len(result) == 1

    def test_returned_news_is_news_instance(
        self, use_case: ParseDocxUseCase, mock_service: MagicMock
    ) -> None:
        mock_service.extract_news.return_value = [_dto()]

        result = use_case.execute(Path("boletim.docx"))

        assert isinstance(result[0], News)

    def test_news_fields_match_dto(
        self, use_case: ParseDocxUseCase, mock_service: MagicMock
    ) -> None:
        mock_service.extract_news.return_value = [
            _dto(title="Exclusivo", content="Detalhes.", source="boletim.docx")
        ]

        result = use_case.execute(Path("boletim.docx"))

        news = result[0]
        assert news.title == "Exclusivo"
        assert news.content == "Detalhes."
        assert news.source_file == "boletim.docx"

    def test_news_initial_status_is_pending(
        self, use_case: ParseDocxUseCase, mock_service: MagicMock
    ) -> None:
        mock_service.extract_news.return_value = [_dto()]

        result = use_case.execute(Path("boletim.docx"))

        assert result[0].status == NewsStatus.PENDING

    def test_repository_save_is_called_once(
        self,
        use_case: ParseDocxUseCase,
        mock_service: MagicMock,
        mock_repo: MagicMock,
    ) -> None:
        mock_service.extract_news.return_value = [_dto()]

        use_case.execute(Path("boletim.docx"))

        assert mock_repo.save.call_count == 1

    def test_saved_news_is_returned(
        self,
        use_case: ParseDocxUseCase,
        mock_service: MagicMock,
        mock_repo: MagicMock,
    ) -> None:
        """Verifica que execute retorna exatamente o que o repositório devolveu."""
        mock_service.extract_news.return_value = [_dto()]

        result = use_case.execute(Path("boletim.docx"))

        # O side_effect do fixture retorna a própria entidade passada para save;
        # o resultado deve ser o mesmo objeto que foi salvo.
        saved_arg = mock_repo.save.call_args[0][0]
        assert result[0] is saved_arg


# ---------------------------------------------------------------------------
# Testes do caminho feliz — múltiplas notícias
# ---------------------------------------------------------------------------


class TestParseDocxUseCaseMultipleNews:
    """Testes de execute com vários DTOs retornados pelo serviço."""

    def test_returns_list_with_correct_count(
        self, use_case: ParseDocxUseCase, mock_service: MagicMock
    ) -> None:
        mock_service.extract_news.return_value = [
            _dto("N1"),
            _dto("N2"),
            _dto("N3"),
        ]

        result = use_case.execute(Path("boletim.docx"))

        assert len(result) == 3

    def test_order_of_results_matches_order_of_dtos(
        self, use_case: ParseDocxUseCase, mock_service: MagicMock
    ) -> None:
        mock_service.extract_news.return_value = [
            _dto("Primeira"),
            _dto("Segunda"),
            _dto("Terceira"),
        ]

        result = use_case.execute(Path("boletim.docx"))

        assert [n.title for n in result] == ["Primeira", "Segunda", "Terceira"]

    def test_repository_save_called_once_per_dto(
        self,
        use_case: ParseDocxUseCase,
        mock_service: MagicMock,
        mock_repo: MagicMock,
    ) -> None:
        mock_service.extract_news.return_value = [_dto("N1"), _dto("N2"), _dto("N3")]

        use_case.execute(Path("boletim.docx"))

        assert mock_repo.save.call_count == 3

    def test_service_extract_news_called_with_file_path(
        self, use_case: ParseDocxUseCase, mock_service: MagicMock
    ) -> None:
        mock_service.extract_news.return_value = [_dto()]
        file_path = Path("boletim.docx")

        use_case.execute(file_path)

        mock_service.extract_news.assert_called_once_with(file_path)

