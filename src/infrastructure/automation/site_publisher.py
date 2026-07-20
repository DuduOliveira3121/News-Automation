"""Módulo de automação de publicação no portal via Playwright."""
from __future__ import annotations

import logging
from pathlib import Path
from types import TracebackType
from typing import Optional, Type

from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright

from config.settings import settings
from src.application.dtos.news_dto import NewsDTO

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Seletores – ajuste conforme o portal alvo
# ---------------------------------------------------------------------------
_SEL_LOGIN_URL: str = "/wp-login.php"          # caminho relativo à portal_url
_SEL_USERNAME_INPUT: str = "#user_login"
_SEL_PASSWORD_INPUT: str = "#user_pass"
_SEL_LOGIN_BUTTON: str = "#wp-submit"

_SEL_NEW_POST_LINK: str = "#menu-posts a.menu-top"  # link "Posts" no menu
_SEL_ADD_NEW_BUTTON: str = "a.page-title-action"    # botão "Adicionar novo"

_SEL_TITLE_INPUT: str = "#title"                    # campo de título
_SEL_CONTENT_AREA: str = "#content"                 # área de texto (TinyMCE/clássico)
_SEL_CATEGORY_CHECKBOX: str = "input[type='checkbox'][value='{categoria}']"

_SEL_IMAGE_UPLOAD_BUTTON: str = ".editor-post-featured-image__toggle"  # Gutenberg
_SEL_IMAGE_FILE_INPUT: str = "input[type='file']"
_SEL_IMAGE_CONFIRM: str = "button.media-button-select"

_SEL_PUBLISH_BUTTON: str = "#publish"              # clássico; ajuste para Gutenberg
_SEL_CONFIRM_PUBLISH: str = "a.components-button--is-primary"  # confirmação (Gutenberg)
_SEL_SUCCESS_NOTICE: str = "#message.updated"       # aviso de sucesso


class SitePublisher:
    """Automatiza a publicação de uma notícia no painel administrativo do portal.

    Responsabilidades exclusivas desta classe:
        - Controlar o ciclo de vida do browser (Playwright).
        - Executar cada etapa de interação com a interface web.

    Regras de negócio (aprovação, revisão, seleção de notícias) pertencem
    à camada de aplicação e **nunca** devem residir aqui.

    Uso típico::

        with SitePublisher() as publisher:
            publisher.login()
            publisher.abrir_painel()
            publisher.criar_noticia()
            publisher.preencher_campos(dto)
            publisher.enviar_imagem(dto.imagem)
            publisher.publicar()
    """

    def __init__(self, headless: bool = True) -> None:
        self._portal_url: str = settings.portal_url.rstrip("/")
        self._username: str = settings.portal_username
        self._password: str = settings.portal_password
        self._headless: bool = headless

        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

    # ------------------------------------------------------------------
    # Gerenciamento de ciclo de vida
    # ------------------------------------------------------------------

    def __enter__(self) -> "SitePublisher":
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=self._headless)
        self._context = self._browser.new_context()
        self._page = self._context.new_page()
        logger.debug("Browser Playwright iniciado.")
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        if self._context:
            self._context.close()
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()
        logger.debug("Browser Playwright encerrado.")

    # ------------------------------------------------------------------
    # Métodos públicos – cada um com responsabilidade única
    # ------------------------------------------------------------------

    def login(self) -> None:
        """Navega para a página de login e autentica com as credenciais configuradas.

        Raises:
            RuntimeError: Se a autenticação falhar (redirecionamento não ocorrer).
        """
        page = self._get_page()
        login_url = f"{self._portal_url}{_SEL_LOGIN_URL}"
        logger.info("Acessando página de login: %s", login_url)

        page.goto(login_url)
        page.wait_for_load_state("networkidle")

        page.fill(_SEL_USERNAME_INPUT, self._username)
        page.fill(_SEL_PASSWORD_INPUT, self._password)
        page.click(_SEL_LOGIN_BUTTON)

        page.wait_for_load_state("networkidle")

        if "wp-login" in page.url:
            raise RuntimeError(
                "Falha na autenticação: a página de login não foi abandonada. "
                "Verifique as credenciais em PORTAL_USERNAME e PORTAL_PASSWORD."
            )

        logger.info("Login realizado com sucesso.")

    def abrir_painel(self) -> None:
        """Navega para o painel administrativo (Dashboard).

        Raises:
            RuntimeError: Se a URL do painel não for atingida.
        """
        page = self._get_page()
        painel_url = f"{self._portal_url}/wp-admin/"
        logger.info("Abrindo painel administrativo: %s", painel_url)

        page.goto(painel_url)
        page.wait_for_load_state("networkidle")

        if "wp-admin" not in page.url:
            raise RuntimeError(
                "Não foi possível acessar o painel administrativo. "
                "Confirme que o login foi realizado antes de chamar abrir_painel()."
            )

        logger.info("Painel administrativo aberto.")

    def criar_noticia(self) -> None:
        """Navega até o formulário de criação de nova notícia.

        Raises:
            RuntimeError: Se o formulário de nova notícia não carregar.
        """
        page = self._get_page()
        new_post_url = f"{self._portal_url}/wp-admin/post-new.php"
        logger.info("Navegando para criação de nova notícia: %s", new_post_url)

        page.goto(new_post_url)
        page.wait_for_load_state("networkidle")

        if "post-new.php" not in page.url:
            raise RuntimeError(
                "Falha ao acessar o formulário de nova notícia. "
                "Verifique as permissões do usuário autenticado."
            )

        logger.info("Formulário de nova notícia carregado.")

    def preencher_campos(self, dto: NewsDTO) -> None:
        """Preenche os campos do formulário com os dados da notícia.

        Recebe exclusivamente um DTO — nenhuma regra de negócio é aplicada aqui.

        Args:
            dto: Dados da notícia a serem inseridos no formulário.

        Raises:
            RuntimeError: Se um campo obrigatório não puder ser preenchido.
        """
        page = self._get_page()
        conteudo = dto.reviewed_content or dto.conteudo
        logger.info("Preenchendo campos do formulário para notícia id=%s.", dto.id)

        # Título
        page.wait_for_selector(_SEL_TITLE_INPUT, state="visible")
        page.fill(_SEL_TITLE_INPUT, dto.titulo)

        # Conteúdo (editor clássico / TinyMCE)
        page.wait_for_selector(_SEL_CONTENT_AREA, state="visible")
        page.fill(_SEL_CONTENT_AREA, conteudo)

        # Categoria (opcional)
        if dto.categoria:
            selector = _SEL_CATEGORY_CHECKBOX.format(categoria=dto.categoria)
            categoria_checkbox = page.query_selector(selector)
            if categoria_checkbox and not categoria_checkbox.is_checked():
                categoria_checkbox.check()
                logger.debug("Categoria '%s' marcada.", dto.categoria)
            elif not categoria_checkbox:
                logger.warning(
                    "Checkbox de categoria '%s' não encontrado — ignorado.",
                    dto.categoria,
                )

        logger.info("Campos do formulário preenchidos.")

    def enviar_imagem(self, caminho_imagem: str) -> None:
        """Realiza o upload da imagem de capa da notícia.

        Args:
            caminho_imagem: Caminho absoluto ou relativo para o arquivo de imagem.

        Raises:
            FileNotFoundError: Se o arquivo de imagem não existir no caminho indicado.
            RuntimeError: Se o upload não puder ser concluído.
        """
        page = self._get_page()
        imagem = Path(caminho_imagem)

        if not imagem.exists():
            raise FileNotFoundError(
                f"Arquivo de imagem não encontrado: {imagem.resolve()}"
            )

        logger.info("Enviando imagem: %s", imagem.name)

        # Abre o modal de mídia
        page.wait_for_selector(_SEL_IMAGE_UPLOAD_BUTTON, state="visible")
        page.click(_SEL_IMAGE_UPLOAD_BUTTON)

        # Aguarda o input de arquivo e faz o upload
        with page.expect_file_chooser() as fc_info:
            page.click(_SEL_IMAGE_FILE_INPUT)
        file_chooser = fc_info.value
        file_chooser.set_files(str(imagem.resolve()))

        # Confirma a seleção no modal de mídia
        page.wait_for_selector(_SEL_IMAGE_CONFIRM, state="visible")
        page.click(_SEL_IMAGE_CONFIRM)

        page.wait_for_load_state("networkidle")
        logger.info("Imagem enviada com sucesso.")

    def publicar(self) -> None:
        """Submete o formulário e aguarda a confirmação de publicação.

        Raises:
            RuntimeError: Se a publicação não for confirmada pelo portal.
        """
        page = self._get_page()
        logger.info("Submetendo publicação.")

        page.wait_for_selector(_SEL_PUBLISH_BUTTON, state="visible")
        page.click(_SEL_PUBLISH_BUTTON)

        page.wait_for_load_state("networkidle")

        # Verifica aviso de sucesso
        success = page.query_selector(_SEL_SUCCESS_NOTICE)
        if not success:
            raise RuntimeError(
                "Publicação não confirmada: o aviso de sucesso não foi detectado. "
                "Verifique os seletores ou o estado do formulário."
            )

        logger.info("Notícia publicada com sucesso.")

    # ------------------------------------------------------------------
    # Auxiliares privados
    # ------------------------------------------------------------------

    def _get_page(self) -> Page:
        """Retorna a página ativa, garantindo que o contexto foi inicializado.

        Raises:
            RuntimeError: Se o SitePublisher for usado fora de um bloco ``with``.
        """
        if self._page is None:
            raise RuntimeError(
                "SitePublisher não foi inicializado. "
                "Use-o como gerenciador de contexto: ``with SitePublisher() as pub:``"
            )
        return self._page
