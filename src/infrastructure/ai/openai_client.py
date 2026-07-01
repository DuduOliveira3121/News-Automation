"""Cliente OpenAI — wrapper para a API de chat completions."""
from __future__ import annotations

import logging

from openai import OpenAI

from config.settings import settings

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """Você é um editor jornalístico experiente. 
Revise o texto da notícia fornecida corrigindo gramática, ortografia e estilo, 
mantendo o conteúdo factual intacto. Responda apenas com o texto revisado."""


class OpenAIClient:
    """Wrapper em torno do SDK oficial da OpenAI.

    Fornece um método de alto nível para revisão de texto,
    abstraindo detalhes de autenticação e chamada à API.
    """

    def __init__(self) -> None:
        self._client = OpenAI(api_key=settings.openai_api_key)
        self._model: str = settings.openai_model

    def review_text(self, title: str, content: str) -> str:
        """Envia o texto para revisão e retorna o conteúdo corrigido.

        Args:
            title: Título da notícia.
            content: Corpo da notícia original.

        Returns:
            Texto revisado retornado pelo modelo.

        Raises:
            RuntimeError: Se a chamada à API falhar.
        """
        ...
