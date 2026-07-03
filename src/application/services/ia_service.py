"""Serviço de geração e melhoria de conteúdo jornalístico via IA."""
from __future__ import annotations

import logging

from src.domain.interfaces.ai_client import IAIClient

logger = logging.getLogger(__name__)

_SYSTEM_TITULO = (
    "Você é um editor jornalístico experiente. "
    "Crie um título conciso, objetivo e atraente para a notícia fornecida. "
    "Responda apenas com o título, sem aspas ou pontuação final."
)

_SYSTEM_RESUMO = (
    "Você é um editor jornalístico experiente. "
    "Escreva um resumo claro e objetivo da notícia em no máximo duas frases. "
    "Responda apenas com o resumo."
)

_SYSTEM_MELHORAR = (
    "Você é um editor jornalístico experiente. "
    "Melhore o texto da notícia corrigindo gramática, ortografia e estilo, "
    "mantendo o conteúdo factual intacto. "
    "Responda apenas com o texto melhorado."
)

_SYSTEM_TEXTO_ALTERNATIVO = (
    "Você é um especialista em acessibilidade digital. "
    "Crie um texto alternativo (alt text) conciso e descritivo para uma imagem "
    "associada à notícia fornecida. "
    "Responda apenas com o texto alternativo, sem introduções."
)


class IAService:
    """Serviço de geração e melhoria de conteúdo jornalístico usando IA.

    Cada método é independente e pode ser usado de forma isolada.
    O cliente de IA é injetado no construtor para facilitar testes.
    """

    def __init__(self, ai_client: IAIClient) -> None:
        self._client = ai_client

    def gerar_titulo(self, content: str) -> str:
        """Gera um título jornalístico para o conteúdo fornecido.

        Args:
            content: Corpo da notícia a partir do qual o título será criado.

        Returns:
            Título gerado pelo modelo de IA.

        Raises:
            ValueError: Se ``content`` estiver vazio.
            RuntimeError: Se a chamada ao cliente de IA falhar.
        """
        if not content or not content.strip():
            raise ValueError("O conteúdo não pode estar vazio para gerar um título.")

        logger.debug("Gerando título via IA.")
        return self._client.complete(
            system_prompt=_SYSTEM_TITULO,
            user_message=content.strip(),
        )

    def gerar_resumo(self, content: str) -> str:
        """Gera um resumo em até duas frases a partir do conteúdo fornecido.

        Args:
            content: Corpo da notícia a ser resumida.

        Returns:
            Resumo gerado pelo modelo de IA.

        Raises:
            ValueError: Se ``content`` estiver vazio.
            RuntimeError: Se a chamada ao cliente de IA falhar.
        """
        if not content or not content.strip():
            raise ValueError("O conteúdo não pode estar vazio para gerar um resumo.")

        logger.debug("Gerando resumo via IA.")
        return self._client.complete(
            system_prompt=_SYSTEM_RESUMO,
            user_message=content.strip(),
        )

    def melhorar_conteudo(self, content: str) -> str:
        """Melhora gramática, ortografia e estilo do conteúdo preservando os fatos.

        Args:
            content: Texto original da notícia.

        Returns:
            Texto melhorado pelo modelo de IA.

        Raises:
            ValueError: Se ``content`` estiver vazio.
            RuntimeError: Se a chamada ao cliente de IA falhar.
        """
        if not content or not content.strip():
            raise ValueError("O conteúdo não pode estar vazio para ser melhorado.")

        logger.debug("Melhorando conteúdo via IA.")
        return self._client.complete(
            system_prompt=_SYSTEM_MELHORAR,
            user_message=content.strip(),
        )

    def gerar_texto_alternativo(self, content: str, context: str = "") -> str:
        """Gera um texto alternativo (alt text) para imagem relacionada à notícia.

        Args:
            content: Corpo da notícia que contextualiza a imagem.
            context: Descrição adicional opcional da imagem ou cena.

        Returns:
            Texto alternativo gerado pelo modelo de IA.

        Raises:
            ValueError: Se ``content`` estiver vazio.
            RuntimeError: Se a chamada ao cliente de IA falhar.
        """
        if not content or not content.strip():
            raise ValueError("O conteúdo não pode estar vazio para gerar texto alternativo.")

        user_message = content.strip()
        if context and context.strip():
            user_message = f"Contexto da imagem: {context.strip()}\n\nNotícia:\n{user_message}"

        logger.debug("Gerando texto alternativo via IA.")
        return self._client.complete(
            system_prompt=_SYSTEM_TEXTO_ALTERNATIVO,
            user_message=user_message,
        )
