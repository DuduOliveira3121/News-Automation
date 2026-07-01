"""Use case: leitura e extração de notícias de um arquivo .docx."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from src.application.dtos.news_dto import ParsedNewsDTO
from src.application.services.docx_service import DocxService
from src.domain.entities.news import News
from src.domain.interfaces.news_repository import INewsRepository

logger = logging.getLogger(__name__)


class ParseDocxUseCase:
    """Coordena a extração de notícias de um .docx e sua persistência.

    Responsabilidades:
        1. Delegar ao DocxService a leitura e parsing do arquivo.
        2. Converter cada artigo extraído em uma entidade News.
        3. Persistir as entidades via INewsRepository.
        4. Retornar a lista de notícias salvas.
    """

    def __init__(
        self,
        docx_service: DocxService,
        news_repository: INewsRepository,
    ) -> None:
        self._docx_service = docx_service
        self._news_repository = news_repository

    def execute(self, file_path: Path) -> List[News]:
        """Executa o parsing e persistência de notícias do arquivo.

        Args:
            file_path: Caminho absoluto para o arquivo .docx.

        Returns:
            Lista de entidades News salvas no repositório.
        """
        ...
