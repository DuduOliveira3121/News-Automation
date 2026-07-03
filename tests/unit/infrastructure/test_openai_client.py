"""Testes unitários do OpenAIClient.

Estratégia de isolamento
------------------------
- O SDK ``openai.OpenAI`` é interceptado via ``unittest.mock.patch`` para que
  nenhuma chamada real à API seja feita.
- A fixture ``mock_openai`` retorna o objeto interno ``_client`` já mockado,
  permitindo configurar respostas e efeitos por teste.
- Coberto:
    * retorno correto da resposta do modelo
    * resposta com ``content=None`` (retorna string vazia)
    * timeout (``TimeoutError`` → ``RuntimeError``)
    * exceções genéricas da API (``ConnectionError``, ``Exception``) → ``RuntimeError``
    * causa original preservada no ``RuntimeError``
    * estrutura das mensagens enviadas à API (system / user)
    * chamada com ``model`` correto
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.infrastructure.ai.openai_client import OpenAIClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SYSTEM = "Você é um editor."
_USER = "Conteúdo da notícia."


def _make_response(content: str | None) -> MagicMock:
    """Cria um objeto de resposta que imita ``ChatCompletion``."""
    response = MagicMock()
    response.choices[0].message.content = content
    return response


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_sdk() -> MagicMock:
    """Retorna o objeto interno ``_client`` com o SDK OpenAI completamente mockado.

    O patch substitui ``OpenAI`` no módulo antes que ``OpenAIClient.__init__``
    seja executado, evitando qualquer chamada real.
    """
    with patch("src.infrastructure.ai.openai_client.OpenAI") as mock_cls:
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def client(mock_sdk: MagicMock) -> OpenAIClient:
    """``OpenAIClient`` instanciado com SDK mockado."""
    return OpenAIClient()


# ---------------------------------------------------------------------------
# Retorno correto
# ---------------------------------------------------------------------------


class TestRetornoCorreto:
    def test_retorna_conteudo_da_resposta(self, client: OpenAIClient, mock_sdk: MagicMock) -> None:
        mock_sdk.chat.completions.create.return_value = _make_response("Texto gerado pela IA.")

        resultado = client.complete(_SYSTEM, _USER)

        assert resultado == "Texto gerado pela IA."

    def test_retorna_string_vazia_quando_content_e_none(
        self, client: OpenAIClient, mock_sdk: MagicMock
    ) -> None:
        mock_sdk.chat.completions.create.return_value = _make_response(None)

        resultado = client.complete(_SYSTEM, _USER)

        assert resultado == ""

    def test_retorna_string_vazia_quando_content_e_string_vazia(
        self, client: OpenAIClient, mock_sdk: MagicMock
    ) -> None:
        mock_sdk.chat.completions.create.return_value = _make_response("")

        resultado = client.complete(_SYSTEM, _USER)

        assert resultado == ""

    def test_preserva_texto_com_multiplas_linhas(
        self, client: OpenAIClient, mock_sdk: MagicMock
    ) -> None:
        texto_multilinhas = "Primeira frase.\nSegunda frase.\nTerceira frase."
        mock_sdk.chat.completions.create.return_value = _make_response(texto_multilinhas)

        resultado = client.complete(_SYSTEM, _USER)

        assert resultado == texto_multilinhas


# ---------------------------------------------------------------------------
# Estrutura das mensagens enviadas à API
# ---------------------------------------------------------------------------


class TestEstruturaDaMensagem:
    def test_envia_system_prompt_como_role_system(
        self, client: OpenAIClient, mock_sdk: MagicMock
    ) -> None:
        mock_sdk.chat.completions.create.return_value = _make_response("ok")

        client.complete("Instrução do sistema.", _USER)

        _, kwargs = mock_sdk.chat.completions.create.call_args
        mensagens = kwargs["messages"]
        system_msg = next(m for m in mensagens if m["role"] == "system")
        assert system_msg["content"] == "Instrução do sistema."

    def test_envia_user_message_como_role_user(
        self, client: OpenAIClient, mock_sdk: MagicMock
    ) -> None:
        mock_sdk.chat.completions.create.return_value = _make_response("ok")

        client.complete(_SYSTEM, "Mensagem do usuário.")

        _, kwargs = mock_sdk.chat.completions.create.call_args
        mensagens = kwargs["messages"]
        user_msg = next(m for m in mensagens if m["role"] == "user")
        assert user_msg["content"] == "Mensagem do usuário."

    def test_envia_exatamente_dois_papeis(
        self, client: OpenAIClient, mock_sdk: MagicMock
    ) -> None:
        mock_sdk.chat.completions.create.return_value = _make_response("ok")

        client.complete(_SYSTEM, _USER)

        _, kwargs = mock_sdk.chat.completions.create.call_args
        assert len(kwargs["messages"]) == 2

    def test_envia_o_model_configurado(
        self, client: OpenAIClient, mock_sdk: MagicMock
    ) -> None:
        mock_sdk.chat.completions.create.return_value = _make_response("ok")

        client.complete(_SYSTEM, _USER)

        _, kwargs = mock_sdk.chat.completions.create.call_args
        assert "model" in kwargs
        assert isinstance(kwargs["model"], str)
        assert len(kwargs["model"]) > 0

    def test_chama_create_exatamente_uma_vez(
        self, client: OpenAIClient, mock_sdk: MagicMock
    ) -> None:
        mock_sdk.chat.completions.create.return_value = _make_response("ok")

        client.complete(_SYSTEM, _USER)

        mock_sdk.chat.completions.create.assert_called_once()


# ---------------------------------------------------------------------------
# Timeout
# ---------------------------------------------------------------------------


class TestTimeout:
    def test_timeout_levanta_runtime_error(
        self, client: OpenAIClient, mock_sdk: MagicMock
    ) -> None:
        mock_sdk.chat.completions.create.side_effect = TimeoutError("Request timed out")

        with pytest.raises(RuntimeError):
            client.complete(_SYSTEM, _USER)

    def test_timeout_nao_propaga_timeout_error_diretamente(
        self, client: OpenAIClient, mock_sdk: MagicMock
    ) -> None:
        mock_sdk.chat.completions.create.side_effect = TimeoutError("Request timed out")

        with pytest.raises(RuntimeError):
            client.complete(_SYSTEM, _USER)

    def test_timeout_preserva_causa_original(
        self, client: OpenAIClient, mock_sdk: MagicMock
    ) -> None:
        causa = TimeoutError("Request timed out")
        mock_sdk.chat.completions.create.side_effect = causa

        with pytest.raises(RuntimeError) as exc_info:
            client.complete(_SYSTEM, _USER)

        assert exc_info.value.__cause__ is causa


# ---------------------------------------------------------------------------
# Exceções da API
# ---------------------------------------------------------------------------


class TestExcecoesAPI:
    @pytest.mark.parametrize(
        "excecao",
        [
            pytest.param(ConnectionError("Falha de conexão"), id="connection_error"),
            pytest.param(OSError("Socket closed"), id="os_error"),
            pytest.param(ValueError("Resposta inválida da API"), id="value_error"),
            pytest.param(Exception("Erro interno [500]"), id="server_error_500"),
            pytest.param(Exception("Não autorizado [401]"), id="auth_error_401"),
            pytest.param(Exception("Rate limit atingido [429]"), id="rate_limit_429"),
            pytest.param(Exception("Serviço indisponível [503]"), id="unavailable_503"),
        ],
    )
    def test_qualquer_excecao_vira_runtime_error(
        self, client: OpenAIClient, mock_sdk: MagicMock, excecao: Exception
    ) -> None:
        mock_sdk.chat.completions.create.side_effect = excecao

        with pytest.raises(RuntimeError):
            client.complete(_SYSTEM, _USER)

    def test_runtime_error_tem_mensagem_descritiva(
        self, client: OpenAIClient, mock_sdk: MagicMock
    ) -> None:
        mock_sdk.chat.completions.create.side_effect = Exception("qualquer erro")

        with pytest.raises(RuntimeError, match="OpenAI"):
            client.complete(_SYSTEM, _USER)

    def test_causa_original_preservada_em_excecao_de_api(
        self, client: OpenAIClient, mock_sdk: MagicMock
    ) -> None:
        causa = Exception("Erro original da API")
        mock_sdk.chat.completions.create.side_effect = causa

        with pytest.raises(RuntimeError) as exc_info:
            client.complete(_SYSTEM, _USER)

        assert exc_info.value.__cause__ is causa

    def test_erro_de_autenticacao_vira_runtime_error(
        self, client: OpenAIClient, mock_sdk: MagicMock
    ) -> None:
        mock_sdk.chat.completions.create.side_effect = Exception("401 Unauthorized")

        with pytest.raises(RuntimeError):
            client.complete(_SYSTEM, _USER)

    def test_rate_limit_vira_runtime_error(
        self, client: OpenAIClient, mock_sdk: MagicMock
    ) -> None:
        mock_sdk.chat.completions.create.side_effect = Exception("429 Too Many Requests")

        with pytest.raises(RuntimeError):
            client.complete(_SYSTEM, _USER)

    def test_nao_faz_nova_tentativa_automaticamente(
        self, client: OpenAIClient, mock_sdk: MagicMock
    ) -> None:
        mock_sdk.chat.completions.create.side_effect = Exception("Erro")

        with pytest.raises(RuntimeError):
            client.complete(_SYSTEM, _USER)

        mock_sdk.chat.completions.create.assert_called_once()
