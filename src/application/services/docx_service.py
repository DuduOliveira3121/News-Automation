"""Serviço de leitura e parsing de arquivos .docx."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from src.application.dtos.news_dto import ParsedNewsDTO
from src.infrastructure.parsers.news_parser import NewsParser

logger = logging.getLogger(__name__)


class DocxService:
    """Responsável por extrair notícias de documentos Word (.docx).

    Delega o parsing ao :class:`~src.infrastructure.parsers.news_parser.NewsParser`
    e converte o resultado em :class:`~src.application.dtos.news_dto.ParsedNewsDTO`
    para consumo pelas camadas de aplicação.

    Convenção de estrutura esperada no documento:
        - Cada notícia começa com um parágrafo de estilo "Heading 1" (título).
        - O corpo da notícia é composto pelos parágrafos subsequentes até o
          próximo "Heading 1" ou o fim do documento.

    Para detalhes completos das premissas adotadas, consulte o módulo
    :mod:`src.infrastructure.parsers.news_parser`.
    """

    def __init__(self, parser: NewsParser | None = None) -> None:
        """Inicializa o serviço.

        Args:
            parser: Instância de :class:`NewsParser` a utilizar.  Se não
                fornecida, uma instância padrão é criada automaticamente.
        """
        self._parser = parser or NewsParser()

    def extract_news(self, file_path: Path) -> List[ParsedNewsDTO]:
        """Lê o .docx e retorna uma lista de notícias extraídas.

        Args:
            file_path: Caminho para o arquivo .docx.

        Returns:
            Lista de :class:`ParsedNewsDTO` com título e conteúdo de cada
            notícia, na ordem em que aparecem no documento.

        Raises:
            FileNotFoundError: Se o arquivo não existir.
            ValueError: Se a extensão for inválida, o arquivo estiver
                corrompido, ou não contiver nenhuma notícia válida.
        """
        self.validate_file(file_path)
        noticias = self._parser.parse(file_path)

        if not noticias:
            raise ValueError(
                f"Nenhuma notícia encontrada em '{file_path.name}'. "
                "Verifique se o documento possui parágrafos com estilo 'Heading 1'."
            )

        return [
            ParsedNewsDTO(
                title=n.titulo,
                content=n.corpo,
                source_file=n.arquivo_origem,
            )
            for n in noticias
        ]

    def validate_file(self, file_path: Path) -> None:
        """Valida se o caminho aponta para um .docx existente e com extensão correta.

        Args:
            file_path: Caminho a validar.

        Raises:
            FileNotFoundError: Arquivo inexistente.
            ValueError: Extensão inválida.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
        if file_path.suffix.lower() != ".docx":
            raise ValueError(
                f"Extensão inválida '{file_path.suffix}'. Esperado: .docx"
            )
