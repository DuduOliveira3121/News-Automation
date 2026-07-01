"""Testes unitários do ParseDocxUseCase."""
import pytest

from src.application.use_cases.parse_docx_use_case import ParseDocxUseCase


class TestParseDocxUseCase:
    """Testes do use case de parsing de .docx."""

    def test_execute_returns_list_of_news(self) -> None:
        # TODO: implementar com mocks de DocxService e INewsRepository
        pass

    def test_execute_raises_on_invalid_file(self) -> None:
        pass
