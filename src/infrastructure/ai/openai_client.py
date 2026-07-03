"""Cliente OpenAI — wrapper para a API de chat completions."""
from __future__ import annotations

import logging

from openai import OpenAI

from config.settings import settings
from src.domain.interfaces.ai_client import IAIClient

logger = logging.getLogger(__name__)


class OpenAIClient(IAIClient):
    """Implementação de IAIClient usando o SDK oficial da OpenAI.

    Abstraindo detalhes de autenticação e chamada à API.
    """

    def __init__(self) -> None:
        self._client = OpenAI(api_key=settings.openai_api_key)
        self._model: str = settings.openai_model

    def complete(self, system_prompt: str, user_message: str) -> str:
        """Envia um par de mensagens ao modelo e retorna o texto gerado.

        Args:
            system_prompt: Instrução de comportamento (role=system).
            user_message: Conteúdo do usuário (role=user).

        Returns:
            Texto de resposta gerado pelo modelo.

        Raises:
            RuntimeError: Se a chamada à API falhar.
        """
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            logger.exception("Falha na chamada à API da OpenAI.")
            raise RuntimeError("Erro ao comunicar com a API da OpenAI.") from exc
