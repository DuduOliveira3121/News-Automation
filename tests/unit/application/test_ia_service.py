"""Testes unitários do IAService.

Estratégia de isolamento
------------------------
- O ``IAIClient`` é substituído por um ``MagicMock`` para que o IAService
  seja testado sem depender de nenhum provedor de IA real.
- Cada método é testado de forma independente, cobrindo:
    * retorno correto
    * tratamento de timeout
    * exceções da API
    * respostas vazias
    * prompts inválidos
"""
from __future__ import annotations

from unittest.mock import MagicMock, call

import pytest

from src.application.services.ia_service import IAService
from src.domain.interfaces.ai_client import IAIClient

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_client() -> MagicMock:
    """Mock de IAIClient com retorno configurável."""
    return MagicMock(spec=IAIClient)


@pytest.fixture
def service(mock_client: MagicMock) -> IAService:
    """IAService com cliente de IA mockado."""
    return IAService(ai_client=mock_client)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PROMPTS_INVALIDOS = [
    pytest.param("", id="vazio"),
    pytest.param("   ", id="somente_espacos"),
    pytest.param("\t\n", id="somente_tabulacao_e_newline"),
]

_EXCECOES_DA_API = [
    pytest.param(RuntimeError("Erro de autenticação [401]"), id="auth_error"),
    pytest.param(RuntimeError("Rate limit atingido [429]"), id="rate_limit"),
    pytest.param(RuntimeError("Erro interno do servidor [500]"), id="server_error"),
    pytest.param(RuntimeError("Timeout na comunicação com a API."), id="timeout"),
]

# ---------------------------------------------------------------------------
# gerar_titulo
# ---------------------------------------------------------------------------


class TestGerarTitulo:
    # ---- retorno correto ------------------------------------------------

    def test_retorna_titulo_gerado(self, service: IAService, mock_client: MagicMock) -> None:
        mock_client.complete.return_value = "Prefeito anuncia novo hospital"

        resultado = service.gerar_titulo("O prefeito anunciou a construção de um novo hospital.")

        assert resultado == "Prefeito anuncia novo hospital"

    def test_chama_complete_exatamente_uma_vez(
        self, service: IAService, mock_client: MagicMock
    ) -> None:
        mock_client.complete.return_value = "Título qualquer"

        service.gerar_titulo("Conteúdo da notícia.")

        mock_client.complete.assert_called_once()

    def test_passa_conteudo_como_user_message(
        self, service: IAService, mock_client: MagicMock
    ) -> None:
        mock_client.complete.return_value = "Título"
        conteudo = "Conteúdo da notícia."

        service.gerar_titulo(conteudo)

        _, kwargs = mock_client.complete.call_args
        assert kwargs["user_message"] == conteudo

    def test_passa_system_prompt(self, service: IAService, mock_client: MagicMock) -> None:
        mock_client.complete.return_value = "Título"

        service.gerar_titulo("Qualquer conteúdo.")

        _, kwargs = mock_client.complete.call_args
        assert "system_prompt" in kwargs
        assert len(kwargs["system_prompt"]) > 0

    def test_remove_espacos_das_bordas_do_conteudo(
        self, service: IAService, mock_client: MagicMock
    ) -> None:
        mock_client.complete.return_value = "Título"

        service.gerar_titulo("  Conteúdo com espaços.  ")

        _, kwargs = mock_client.complete.call_args
        assert kwargs["user_message"] == "Conteúdo com espaços."

    # ---- respostas vazias -----------------------------------------------

    def test_retorna_string_vazia_quando_api_retorna_vazio(
        self, service: IAService, mock_client: MagicMock
    ) -> None:
        mock_client.complete.return_value = ""

        resultado = service.gerar_titulo("Conteúdo válido.")

        assert resultado == ""

    # ---- prompts inválidos ----------------------------------------------

    @pytest.mark.parametrize("conteudo", _PROMPTS_INVALIDOS)
    def test_levanta_value_error_para_prompt_invalido(
        self, service: IAService, conteudo: str
    ) -> None:
        with pytest.raises(ValueError, match="vazio"):
            service.gerar_titulo(conteudo)

    def test_nao_chama_cliente_para_prompt_invalido(
        self, service: IAService, mock_client: MagicMock
    ) -> None:
        with pytest.raises(ValueError):
            service.gerar_titulo("")
        mock_client.complete.assert_not_called()

    # ---- timeout e exceções da API -------------------------------------

    @pytest.mark.parametrize("excecao", _EXCECOES_DA_API)
    def test_propaga_runtime_error_do_cliente(
        self, service: IAService, mock_client: MagicMock, excecao: RuntimeError
    ) -> None:
        mock_client.complete.side_effect = excecao

        with pytest.raises(RuntimeError):
            service.gerar_titulo("Conteúdo válido.")

    def test_propaga_timeout_como_runtime_error(
        self, service: IAService, mock_client: MagicMock
    ) -> None:
        mock_client.complete.side_effect = RuntimeError("Timeout na comunicação com a API.")

        with pytest.raises(RuntimeError, match="Timeout"):
            service.gerar_titulo("Conteúdo válido.")

    def test_nao_suprime_excecao_da_api(
        self, service: IAService, mock_client: MagicMock
    ) -> None:
        mock_client.complete.side_effect = RuntimeError("Falha crítica")

        with pytest.raises(RuntimeError, match="Falha crítica"):
            service.gerar_titulo("Conteúdo.")


# ---------------------------------------------------------------------------
# gerar_resumo
# ---------------------------------------------------------------------------


class TestGerarResumo:
    # ---- retorno correto ------------------------------------------------

    def test_retorna_resumo_gerado(self, service: IAService, mock_client: MagicMock) -> None:
        mock_client.complete.return_value = "Resumo da notícia em duas frases."

        resultado = service.gerar_resumo("Texto longo da notícia sobre investimentos.")

        assert resultado == "Resumo da notícia em duas frases."

    def test_chama_complete_exatamente_uma_vez(
        self, service: IAService, mock_client: MagicMock
    ) -> None:
        mock_client.complete.return_value = "Resumo."

        service.gerar_resumo("Texto longo.")

        mock_client.complete.assert_called_once()

    def test_passa_conteudo_como_user_message(
        self, service: IAService, mock_client: MagicMock
    ) -> None:
        mock_client.complete.return_value = "Resumo."
        conteudo = "Texto longo."

        service.gerar_resumo(conteudo)

        _, kwargs = mock_client.complete.call_args
        assert kwargs["user_message"] == conteudo

    def test_passa_system_prompt_diferente_do_titulo(
        self, service: IAService, mock_client: MagicMock
    ) -> None:
        """Garante que cada método usa seu próprio system_prompt."""
        mock_client.complete.return_value = ""

        service.gerar_titulo("Conteúdo.")
        prompt_titulo = mock_client.complete.call_args_list[0][1]["system_prompt"]

        mock_client.reset_mock()
        service.gerar_resumo("Conteúdo.")
        prompt_resumo = mock_client.complete.call_args_list[0][1]["system_prompt"]

        assert prompt_titulo != prompt_resumo

    # ---- respostas vazias -----------------------------------------------

    def test_retorna_string_vazia_quando_api_retorna_vazio(
        self, service: IAService, mock_client: MagicMock
    ) -> None:
        mock_client.complete.return_value = ""

        resultado = service.gerar_resumo("Conteúdo válido.")

        assert resultado == ""

    # ---- prompts inválidos ----------------------------------------------

    @pytest.mark.parametrize("conteudo", _PROMPTS_INVALIDOS)
    def test_levanta_value_error_para_prompt_invalido(
        self, service: IAService, conteudo: str
    ) -> None:
        with pytest.raises(ValueError, match="vazio"):
            service.gerar_resumo(conteudo)

    def test_nao_chama_cliente_para_prompt_invalido(
        self, service: IAService, mock_client: MagicMock
    ) -> None:
        with pytest.raises(ValueError):
            service.gerar_resumo("")
        mock_client.complete.assert_not_called()

    # ---- timeout e exceções da API -------------------------------------

    @pytest.mark.parametrize("excecao", _EXCECOES_DA_API)
    def test_propaga_runtime_error_do_cliente(
        self, service: IAService, mock_client: MagicMock, excecao: RuntimeError
    ) -> None:
        mock_client.complete.side_effect = excecao

        with pytest.raises(RuntimeError):
            service.gerar_resumo("Conteúdo válido.")

    def test_propaga_timeout_como_runtime_error(
        self, service: IAService, mock_client: MagicMock
    ) -> None:
        mock_client.complete.side_effect = RuntimeError("Timeout na comunicação com a API.")

        with pytest.raises(RuntimeError, match="Timeout"):
            service.gerar_resumo("Conteúdo válido.")


# ---------------------------------------------------------------------------
# melhorar_conteudo
# ---------------------------------------------------------------------------


class TestMelhorarConteudo:
    # ---- retorno correto ------------------------------------------------

    def test_retorna_conteudo_melhorado(self, service: IAService, mock_client: MagicMock) -> None:
        mock_client.complete.return_value = "Texto melhorado com boa gramática."

        resultado = service.melhorar_conteudo("Texto ruim de gramática.")

        assert resultado == "Texto melhorado com boa gramática."

    def test_chama_complete_exatamente_uma_vez(
        self, service: IAService, mock_client: MagicMock
    ) -> None:
        mock_client.complete.return_value = "Texto corrigido."

        service.melhorar_conteudo("texto a melhorar")

        mock_client.complete.assert_called_once()

    def test_passa_conteudo_como_user_message(
        self, service: IAService, mock_client: MagicMock
    ) -> None:
        mock_client.complete.return_value = "Texto corrigido."
        conteudo = "texto a melhorar"

        service.melhorar_conteudo(conteudo)

        _, kwargs = mock_client.complete.call_args
        assert kwargs["user_message"] == conteudo

    def test_conteudo_melhorado_pode_diferir_do_original(
        self, service: IAService, mock_client: MagicMock
    ) -> None:
        original = "texto com erros ortograficos"
        mock_client.complete.return_value = "Texto com erros ortográficos."

        resultado = service.melhorar_conteudo(original)

        assert resultado != original

    # ---- respostas vazias -----------------------------------------------

    def test_retorna_string_vazia_quando_api_retorna_vazio(
        self, service: IAService, mock_client: MagicMock
    ) -> None:
        mock_client.complete.return_value = ""

        resultado = service.melhorar_conteudo("Conteúdo válido.")

        assert resultado == ""

    # ---- prompts inválidos ----------------------------------------------

    @pytest.mark.parametrize("conteudo", _PROMPTS_INVALIDOS)
    def test_levanta_value_error_para_prompt_invalido(
        self, service: IAService, conteudo: str
    ) -> None:
        with pytest.raises(ValueError, match="vazio"):
            service.melhorar_conteudo(conteudo)

    def test_nao_chama_cliente_para_prompt_invalido(
        self, service: IAService, mock_client: MagicMock
    ) -> None:
        with pytest.raises(ValueError):
            service.melhorar_conteudo("")
        mock_client.complete.assert_not_called()

    # ---- timeout e exceções da API -------------------------------------

    @pytest.mark.parametrize("excecao", _EXCECOES_DA_API)
    def test_propaga_runtime_error_do_cliente(
        self, service: IAService, mock_client: MagicMock, excecao: RuntimeError
    ) -> None:
        mock_client.complete.side_effect = excecao

        with pytest.raises(RuntimeError):
            service.melhorar_conteudo("Conteúdo válido.")

    def test_propaga_timeout_como_runtime_error(
        self, service: IAService, mock_client: MagicMock
    ) -> None:
        mock_client.complete.side_effect = RuntimeError("Timeout na comunicação com a API.")

        with pytest.raises(RuntimeError, match="Timeout"):
            service.melhorar_conteudo("Conteúdo válido.")


# ---------------------------------------------------------------------------
# gerar_texto_alternativo
# ---------------------------------------------------------------------------


class TestGerarTextoAlternativo:
    # ---- retorno correto ------------------------------------------------

    def test_retorna_alt_text_gerado(self, service: IAService, mock_client: MagicMock) -> None:
        mock_client.complete.return_value = "Pessoas celebrando em praça pública."

        resultado = service.gerar_texto_alternativo("Notícia sobre a festa da cidade.")

        assert resultado == "Pessoas celebrando em praça pública."

    def test_chama_complete_exatamente_uma_vez(
        self, service: IAService, mock_client: MagicMock
    ) -> None:
        mock_client.complete.return_value = "Alt text."

        service.gerar_texto_alternativo("Notícia sobre tecnologia.")

        mock_client.complete.assert_called_once()

    def test_passa_conteudo_como_user_message_sem_contexto(
        self, service: IAService, mock_client: MagicMock
    ) -> None:
        mock_client.complete.return_value = "Alt text."
        conteudo = "Notícia sobre tecnologia."

        service.gerar_texto_alternativo(conteudo)

        _, kwargs = mock_client.complete.call_args
        assert kwargs["user_message"] == conteudo

    def test_inclui_contexto_na_mensagem_quando_fornecido(
        self, service: IAService, mock_client: MagicMock
    ) -> None:
        mock_client.complete.return_value = "Imagem de satélite."
        conteudo = "Notícia sobre clima."
        contexto = "Imagem de nuvens sobre o oceano"

        service.gerar_texto_alternativo(conteudo, context=contexto)

        _, kwargs = mock_client.complete.call_args
        assert contexto in kwargs["user_message"]
        assert conteudo in kwargs["user_message"]

    def test_ignora_contexto_vazio(self, service: IAService, mock_client: MagicMock) -> None:
        mock_client.complete.return_value = "Alt text."
        conteudo = "Notícia."

        service.gerar_texto_alternativo(conteudo, context="")

        _, kwargs = mock_client.complete.call_args
        assert kwargs["user_message"] == conteudo

    def test_ignora_contexto_somente_espacos(
        self, service: IAService, mock_client: MagicMock
    ) -> None:
        mock_client.complete.return_value = "Alt text."
        conteudo = "Notícia."

        service.gerar_texto_alternativo(conteudo, context="   ")

        _, kwargs = mock_client.complete.call_args
        assert kwargs["user_message"] == conteudo

    # ---- respostas vazias -----------------------------------------------

    def test_retorna_string_vazia_quando_api_retorna_vazio(
        self, service: IAService, mock_client: MagicMock
    ) -> None:
        mock_client.complete.return_value = ""

        resultado = service.gerar_texto_alternativo("Conteúdo válido.")

        assert resultado == ""

    # ---- prompts inválidos ----------------------------------------------

    @pytest.mark.parametrize("conteudo", _PROMPTS_INVALIDOS)
    def test_levanta_value_error_para_prompt_invalido(
        self, service: IAService, conteudo: str
    ) -> None:
        with pytest.raises(ValueError, match="vazio"):
            service.gerar_texto_alternativo(conteudo)

    def test_nao_chama_cliente_para_prompt_invalido(
        self, service: IAService, mock_client: MagicMock
    ) -> None:
        with pytest.raises(ValueError):
            service.gerar_texto_alternativo("")
        mock_client.complete.assert_not_called()

    # ---- timeout e exceções da API -------------------------------------

    @pytest.mark.parametrize("excecao", _EXCECOES_DA_API)
    def test_propaga_runtime_error_do_cliente(
        self, service: IAService, mock_client: MagicMock, excecao: RuntimeError
    ) -> None:
        mock_client.complete.side_effect = excecao

        with pytest.raises(RuntimeError):
            service.gerar_texto_alternativo("Conteúdo válido.")

    def test_propaga_timeout_como_runtime_error(
        self, service: IAService, mock_client: MagicMock
    ) -> None:
        mock_client.complete.side_effect = RuntimeError("Timeout na comunicação com a API.")

        with pytest.raises(RuntimeError, match="Timeout"):
            service.gerar_texto_alternativo("Conteúdo válido.")


# ---------------------------------------------------------------------------
# Independência entre métodos
# ---------------------------------------------------------------------------


class TestIndependenciaEntreMetodos:
    def test_cada_metodo_usa_system_prompt_distinto(
        self, service: IAService, mock_client: MagicMock
    ) -> None:
        mock_client.complete.return_value = ""
        conteudo = "Texto de referência."

        service.gerar_titulo(conteudo)
        service.gerar_resumo(conteudo)
        service.melhorar_conteudo(conteudo)
        service.gerar_texto_alternativo(conteudo)

        prompts = [c[1]["system_prompt"] for c in mock_client.complete.call_args_list]
        assert len(set(prompts)) == 4, "Cada método deve ter um system_prompt único."

    def test_falha_em_um_metodo_nao_afeta_outro(
        self, service: IAService, mock_client: MagicMock
    ) -> None:
        mock_client.complete.side_effect = [
            RuntimeError("Erro no título"),
            "Resumo gerado com sucesso.",
        ]

        with pytest.raises(RuntimeError):
            service.gerar_titulo("Conteúdo.")

        resultado = service.gerar_resumo("Conteúdo.")
        assert resultado == "Resumo gerado com sucesso."

    def test_chamadas_sucessivas_sao_independentes(
        self, service: IAService, mock_client: MagicMock
    ) -> None:
        mock_client.complete.side_effect = ["Título A", "Título B"]

        resultado_1 = service.gerar_titulo("Notícia A.")
        resultado_2 = service.gerar_titulo("Notícia B.")

        assert resultado_1 == "Título A"
        assert resultado_2 == "Título B"
        assert mock_client.complete.call_count == 2
