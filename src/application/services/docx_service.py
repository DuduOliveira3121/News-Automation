"""Serviço de leitura e parsing de arquivos .docx."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from src.application.dtos.news_dto import ParsedNewsDTO

logger = logging.getLogger(__name__)


class DocxService:
    """Responsável por extrair notícias de documentos Word (.docx).

    Convenção de estrutura esperada no documento:
        - Cada notícia começa com um parágrafo de estilo "Heading 1" (título).
        - O corpo da notícia é composto pelos parágrafos subsequentes até o
          próximo "Heading 1" ou o fim do documento.
    """

    def extract_news(self, file_path: Path) -> List[ParsedNewsDTO]:
        """Lê o .docx e retorna uma lista de notícias extraídas.

        Args:
            file_path: Caminho para o arquivo .docx.

        Returns:
            Lista de ParsedNewsDTO com título e conteúdo de cada notícia.

        Raises:
            FileNotFoundError: Se o arquivo não existir.
            ValueError: Se o arquivo não contiver nenhuma notícia válida.
        """
        ...

    def validate_file(self, file_path: Path) -> None:
        """Valida se o caminho aponta para um .docx válido.

        Args:
            file_path: Caminho a validar.

        Raises:
            FileNotFoundError: Arquivo inexistente.
            ValueError: Extensão inválida ou arquivo corrompido.
        """
        ...
