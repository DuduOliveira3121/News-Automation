"""Testes unitários do SitePublisher.

Estratégia de isolamento
-------------------------
- ``sync_playwright`` é completamente substituído por mocks; nenhum browser
  real é aberto durante os testes.
- ``config.settings`` é patchado para fornecer valores controlados e
  previsíveis independentemente do ambiente.
- Coberto:
    * lifecycle do context manager (abertura/fechamento de recursos)
    * login: sucesso, falha por URL, timeout, erro de navegação
    * abrir_painel / criar_noticia: sucesso e falha por URL inesperada
    * preencher_campos: reviewed_content vs conteudo, com/sem categoria,
      checkbox já marcado, elemento inexistente ignorado, timeout
    * enviar_imagem: sucesso, FileNotFoundError, set_files com caminho
      absoluto, timeout
    * publicar: sucesso, RuntimeError quando aviso de sucesso ausente,
      timeout no botão e no wait_for_load_state
    * _get_page: RuntimeError ao usar fora do context manager
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from src.application.dtos.news_dto import NewsDTO
from src.domain.entities.news import NewsStatus
from src.infrastructure.automation.site_publisher import SitePublisher

# ---------------------------------------------------------------------------
# Constantes de teste
# ---------------------------------------------------------------------------
_PORTAL_URL = "https://portal.example.com"
_USERNAME = "editor"
_PASSWORD = "s3cr3t"

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _patch_settings():
    """Isola settings do ambiente real em todos os testes deste módulo."""
    with patch("src.infrastructure.automation.site_publisher.settings") as mock_s:
        mock_s.portal_url = _PORTAL_URL
        mock_s.portal_username = _USERNAME
        mock_s.portal_password = _PASSWORD
        yield mock_s


@pytest.fixture
def mock_page() -> MagicMock:
    """Página Playwright completamente simulada com URL padrão do painel."""
    page = MagicMock()
    page.url = f"{_PORTAL_URL}/wp-admin/"
    return page


@pytest.fixture
def pw_stack(mock_page: MagicMock):
    """Patch de toda a cadeia sync_playwright → Browser → Context → Page.

    Yields:
        Tupla ``(mock_page, mock_browser, mock_context, mock_playwright_obj)``.
    """
    mock_context = MagicMock()
    mock_context.new_page.return_value = mock_page

    mock_browser = MagicMock()
    mock_browser.new_context.return_value = mock_context

    mock_playwright_obj = MagicMock()
    mock_playwright_obj.chromium.launch.return_value = mock_browser

    with patch("src.infrastructure.automation.site_publisher.sync_playwright") as mock_sp:
        mock_sp.return_value.start.return_value = mock_playwright_obj
        yield mock_page, mock_browser, mock_context, mock_playwright_obj


@pytest.fixture
def publisher(pw_stack):
    """SitePublisher ativo dentro do context manager, pronto para asserções."""
    page = pw_stack[0]
    with SitePublisher() as pub:
        yield pub, page


@pytest.fixture
def dto_revisado() -> NewsDTO:
    """DTO com reviewed_content preenchido e categoria definida."""
    return NewsDTO(
        id="dto-001",
        titulo="Notícia de Teste",
        conteudo="Conteúdo original.",
        source_file="teste.docx",
        status=NewsStatus.REVIEWED,
        categoria="politica",
        reviewed_content="Conteúdo revisado pela IA.",
        imagem="/tmp/capa.jpg",
    )


@pytest.fixture
def dto_pendente() -> NewsDTO:
    """DTO sem reviewed_content e sem categoria."""
    return NewsDTO(
        id="dto-002",
        titulo="Notícia Pendente",
        conteudo="Conteúdo sem revisão.",
        source_file="teste.docx",
        status=NewsStatus.PENDING,
    )


@pytest.fixture
def image_file(tmp_path: Path) -> Path:
    """Arquivo de imagem real em disco temporário."""
    img = tmp_path / "capa.jpg"
    img.write_bytes(b"\xff\xd8\xff\xe0")  # cabeçalho JPEG mínimo
    return img


# ---------------------------------------------------------------------------
# Lifecycle do Context Manager
# ---------------------------------------------------------------------------


class TestContextManagerLifecycle:
    def test_page_esta_disponivel_dentro_do_bloco_with(self, pw_stack) -> None:
        page = pw_stack[0]
        with SitePublisher() as pub:
            assert pub._page is page

    def test_fecha_browser_context_ao_sair(self, pw_stack) -> None:
        _, _, context, _ = pw_stack
        with SitePublisher():
            pass
        context.close.assert_called_once()

    def test_fecha_browser_ao_sair(self, pw_stack) -> None:
        _, browser, _, _ = pw_stack
        with SitePublisher():
            pass
        browser.close.assert_called_once()

    def test_para_playwright_ao_sair(self, pw_stack) -> None:
        _, _, _, pw = pw_stack
        with SitePublisher():
            pass
        pw.stop.assert_called_once()

    def test_fecha_recursos_mesmo_quando_excecao_e_lancada(self, pw_stack) -> None:
        _, browser, context, pw = pw_stack
        with pytest.raises(ValueError):
            with SitePublisher():
                raise ValueError("erro interno")
        context.close.assert_called_once()
        browser.close.assert_called_once()
        pw.stop.assert_called_once()


# ---------------------------------------------------------------------------
# _get_page – uso fora do context manager
# ---------------------------------------------------------------------------


class TestGetPageForaDoContexto:
    """Garante que todos os métodos públicos falham de forma clara quando
    o SitePublisher não foi inicializado via context manager."""

    def test_login_levanta_runtime_error(self) -> None:
        pub = SitePublisher()
        with pytest.raises(RuntimeError, match="gerenciador de contexto"):
            pub.login()

    def test_abrir_painel_levanta_runtime_error(self) -> None:
        pub = SitePublisher()
        with pytest.raises(RuntimeError, match="with SitePublisher"):
            pub.abrir_painel()

    def test_criar_noticia_levanta_runtime_error(self) -> None:
        pub = SitePublisher()
        with pytest.raises(RuntimeError, match="gerenciador de contexto"):
            pub.criar_noticia()

    def test_publicar_levanta_runtime_error(self) -> None:
        pub = SitePublisher()
        with pytest.raises(RuntimeError, match="gerenciador de contexto"):
            pub.publicar()


# ---------------------------------------------------------------------------
# login()
# ---------------------------------------------------------------------------


class TestLogin:
    def test_navega_para_url_de_login(self, publisher) -> None:
        pub, page = publisher
        page.url = f"{_PORTAL_URL}/wp-admin/"

        pub.login()

        page.goto.assert_called_with(f"{_PORTAL_URL}/wp-login.php")

    def test_preenche_campo_username(self, publisher) -> None:
        pub, page = publisher
        page.url = f"{_PORTAL_URL}/wp-admin/"

        pub.login()

        page.fill.assert_any_call("#user_login", _USERNAME)

    def test_preenche_campo_password(self, publisher) -> None:
        pub, page = publisher
        page.url = f"{_PORTAL_URL}/wp-admin/"

        pub.login()

        page.fill.assert_any_call("#user_pass", _PASSWORD)

    def test_clica_no_botao_submit(self, publisher) -> None:
        pub, page = publisher
        page.url = f"{_PORTAL_URL}/wp-admin/"

        pub.login()

        page.click.assert_called_with("#wp-submit")

    def test_levanta_runtime_error_quando_url_ainda_e_login(self, publisher) -> None:
        pub, page = publisher
        page.url = f"{_PORTAL_URL}/wp-login.php?login=failed"

        with pytest.raises(RuntimeError, match="Falha na autenticação"):
            pub.login()

    def test_mensagem_de_erro_orienta_verificacao_de_credenciais(self, publisher) -> None:
        pub, page = publisher
        page.url = f"{_PORTAL_URL}/wp-login.php"

        with pytest.raises(RuntimeError, match="PORTAL_USERNAME"):
            pub.login()

    def test_timeout_em_goto_e_propagado(self, publisher) -> None:
        pub, page = publisher
        page.goto.side_effect = PlaywrightTimeoutError("navigation timeout")

        with pytest.raises(PlaywrightTimeoutError):
            pub.login()

    def test_timeout_em_wait_for_load_state_e_propagado(self, publisher) -> None:
        pub, page = publisher
        page.wait_for_load_state.side_effect = PlaywrightTimeoutError("load timeout")

        with pytest.raises(PlaywrightTimeoutError):
            pub.login()


# ---------------------------------------------------------------------------
# abrir_painel()
# ---------------------------------------------------------------------------


class TestAbrirPainel:
    def test_navega_para_wp_admin(self, publisher) -> None:
        pub, page = publisher
        page.url = f"{_PORTAL_URL}/wp-admin/"

        pub.abrir_painel()

        page.goto.assert_called_with(f"{_PORTAL_URL}/wp-admin/")

    def test_levanta_runtime_error_quando_url_nao_contem_wp_admin(self, publisher) -> None:
        pub, page = publisher
        page.url = "https://outro-dominio.com/login"

        with pytest.raises(RuntimeError, match="painel administrativo"):
            pub.abrir_painel()

    def test_timeout_em_goto_e_propagado(self, publisher) -> None:
        pub, page = publisher
        page.goto.side_effect = PlaywrightTimeoutError("timeout")

        with pytest.raises(PlaywrightTimeoutError):
            pub.abrir_painel()

    def test_timeout_em_wait_for_load_state_e_propagado(self, publisher) -> None:
        pub, page = publisher
        page.wait_for_load_state.side_effect = PlaywrightTimeoutError("load timeout")

        with pytest.raises(PlaywrightTimeoutError):
            pub.abrir_painel()


# ---------------------------------------------------------------------------
# criar_noticia()
# ---------------------------------------------------------------------------


class TestCriarNoticia:
    def test_navega_para_post_new_php(self, publisher) -> None:
        pub, page = publisher
        page.url = f"{_PORTAL_URL}/wp-admin/post-new.php"

        pub.criar_noticia()

        page.goto.assert_called_with(f"{_PORTAL_URL}/wp-admin/post-new.php")

    def test_levanta_runtime_error_quando_url_sem_post_new(self, publisher) -> None:
        pub, page = publisher
        page.url = f"{_PORTAL_URL}/wp-admin/"  # redirecionado para dashboard

        with pytest.raises(RuntimeError, match="formulário de nova notícia"):
            pub.criar_noticia()

    def test_timeout_em_wait_for_load_state_e_propagado(self, publisher) -> None:
        pub, page = publisher
        page.wait_for_load_state.side_effect = PlaywrightTimeoutError("timeout")

        with pytest.raises(PlaywrightTimeoutError):
            pub.criar_noticia()


# ---------------------------------------------------------------------------
# preencher_campos()
# ---------------------------------------------------------------------------


class TestPreencherCampos:
    def test_preenche_titulo_com_valor_do_dto(self, publisher, dto_revisado) -> None:
        pub, page = publisher

        pub.preencher_campos(dto_revisado)

        page.fill.assert_any_call("#title", "Notícia de Teste")

    def test_usa_reviewed_content_quando_disponivel(self, publisher, dto_revisado) -> None:
        pub, page = publisher

        pub.preencher_campos(dto_revisado)

        page.fill.assert_any_call("#content", "Conteúdo revisado pela IA.")

    def test_usa_conteudo_original_como_fallback(self, publisher, dto_pendente) -> None:
        pub, page = publisher

        pub.preencher_campos(dto_pendente)

        page.fill.assert_any_call("#content", "Conteúdo sem revisão.")

    def test_marca_checkbox_de_categoria_desmarcado(self, publisher, dto_revisado) -> None:
        pub, page = publisher
        checkbox_mock = MagicMock()
        checkbox_mock.is_checked.return_value = False
        page.query_selector.return_value = checkbox_mock

        pub.preencher_campos(dto_revisado)

        checkbox_mock.check.assert_called_once()

    def test_nao_marca_checkbox_se_ja_estiver_marcado(self, publisher, dto_revisado) -> None:
        pub, page = publisher
        checkbox_mock = MagicMock()
        checkbox_mock.is_checked.return_value = True
        page.query_selector.return_value = checkbox_mock

        pub.preencher_campos(dto_revisado)

        checkbox_mock.check.assert_not_called()

    def test_elemento_de_categoria_inexistente_e_ignorado(
        self, publisher, dto_revisado
    ) -> None:
        pub, page = publisher
        page.query_selector.return_value = None  # seletor não encontrado

        pub.preencher_campos(dto_revisado)  # não deve levantar exceção

    def test_nao_consulta_categoria_quando_dto_sem_categoria(
        self, publisher, dto_pendente
    ) -> None:
        pub, page = publisher

        pub.preencher_campos(dto_pendente)

        page.query_selector.assert_not_called()

    def test_timeout_em_wait_for_selector_e_propagado(
        self, publisher, dto_revisado
    ) -> None:
        pub, page = publisher
        page.wait_for_selector.side_effect = PlaywrightTimeoutError("timeout no título")

        with pytest.raises(PlaywrightTimeoutError):
            pub.preencher_campos(dto_revisado)


# ---------------------------------------------------------------------------
# enviar_imagem()
# ---------------------------------------------------------------------------


class TestEnviarImagem:
    def test_levanta_file_not_found_para_caminho_inexistente(self, publisher) -> None:
        pub, _ = publisher

        with pytest.raises(FileNotFoundError, match="inexistente.jpg"):
            pub.enviar_imagem("/caminho/que/nao/existe/inexistente.jpg")

    def test_clica_no_botao_de_upload(self, publisher, image_file) -> None:
        pub, page = publisher

        pub.enviar_imagem(str(image_file))

        page.click.assert_any_call(".editor-post-featured-image__toggle")

    def test_confirma_selecao_no_modal_de_midia(self, publisher, image_file) -> None:
        pub, page = publisher

        pub.enviar_imagem(str(image_file))

        page.click.assert_any_call("button.media-button-select")

    def test_chama_set_files_com_caminho_absoluto(self, publisher, image_file) -> None:
        pub, page = publisher

        fc_info_mock = MagicMock()
        file_chooser_mock = MagicMock()
        fc_info_mock.value = file_chooser_mock
        page.expect_file_chooser.return_value.__enter__.return_value = fc_info_mock

        pub.enviar_imagem(str(image_file))

        file_chooser_mock.set_files.assert_called_once_with(str(image_file.resolve()))

    def test_timeout_em_wait_for_selector_e_propagado(self, publisher, image_file) -> None:
        pub, page = publisher
        page.wait_for_selector.side_effect = PlaywrightTimeoutError("timeout na imagem")

        with pytest.raises(PlaywrightTimeoutError):
            pub.enviar_imagem(str(image_file))

    def test_timeout_em_wait_for_load_state_apos_upload_e_propagado(
        self, publisher, image_file
    ) -> None:
        pub, page = publisher
        page.wait_for_load_state.side_effect = PlaywrightTimeoutError("timeout pós-upload")

        with pytest.raises(PlaywrightTimeoutError):
            pub.enviar_imagem(str(image_file))


# ---------------------------------------------------------------------------
# publicar()
# ---------------------------------------------------------------------------


class TestPublicar:
    def test_clica_no_botao_publicar(self, publisher) -> None:
        pub, page = publisher
        page.query_selector.return_value = MagicMock()  # aviso de sucesso presente

        pub.publicar()

        page.click.assert_any_call("#publish")

    def test_sucesso_quando_aviso_de_confirmacao_presente(self, publisher) -> None:
        pub, page = publisher
        page.query_selector.return_value = MagicMock()

        pub.publicar()  # não deve levantar exceção

    def test_levanta_runtime_error_quando_aviso_ausente(self, publisher) -> None:
        pub, page = publisher
        page.query_selector.return_value = None  # elemento inexistente

        with pytest.raises(RuntimeError, match="Publicação não confirmada"):
            pub.publicar()

    def test_mensagem_de_erro_orienta_sobre_seletores(self, publisher) -> None:
        pub, page = publisher
        page.query_selector.return_value = None

        with pytest.raises(RuntimeError, match="seletores"):
            pub.publicar()

    def test_timeout_em_wait_for_selector_e_propagado(self, publisher) -> None:
        pub, page = publisher
        page.wait_for_selector.side_effect = PlaywrightTimeoutError("timeout no botão")

        with pytest.raises(PlaywrightTimeoutError):
            pub.publicar()

    def test_timeout_em_wait_for_load_state_e_propagado(self, publisher) -> None:
        pub, page = publisher
        page.wait_for_load_state.side_effect = PlaywrightTimeoutError("timeout pós-submissão")

        with pytest.raises(PlaywrightTimeoutError):
            pub.publicar()
