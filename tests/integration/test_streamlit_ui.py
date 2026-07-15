"""Testes de integração da interface Streamlit — News Automation.

Por que estes testes são de integração e não unitários
=======================================================
Os componentes Streamlit (``st.button``, ``st.text_input``, ``st.file_uploader``,
``st.session_state``, ``st.rerun`` etc.) dependem do runtime do Streamlit para
funcionar corretamente.  Fora do runtime:

* ``st.session_state`` comporta-se como um objeto vazio sem semântica de "rerun".
* ``st.rerun()`` levanta ``streamlit.runtime.scriptrunner.StopException`` e
  encerra o teste prematuramente.
* Widgets (``st.button``, ``st.text_input`` etc.) retornam ``None`` e não
  produzem saída DOM testável.

As funções de renderização em ``app.py`` (``_render_upload``,
``_render_news_list``, ``_render_editor``) exercitam essas primitivas
diretamente, o que as torna inadequadas para testes unitários puros.

Estratégia de cobertura via integração
=======================================
A ferramenta recomendada para testar interfaces Streamlit é a
``streamlit.testing.v1.AppTest``, disponível a partir do Streamlit 1.18.
Ela executa o script inteiro dentro de um ambiente simulado, permitindo:

- Inspecionar e manipular ``session_state``.
- Acionar widgets por ``key`` ou por posição.
- Verificar mensagens de sucesso/erro exibidas pelo app.

Execução
--------
Instale a dependência de desenvolvimento (já listada em ``requirements.txt``)::

    pip install streamlit>=1.40.0

Execute apenas os testes de integração com::

    pytest tests/integration/ -v

Partes cobertas pelos testes abaixo
=====================================
+---------------------------------------+------------------------------------------+
| Cenário                               | Função de ``app.py`` exercitada          |
+---------------------------------------+------------------------------------------+
| App inicializa sem erros              | ``main()`` / ``_init_state()``           |
| Upload de .docx válido                | ``_render_upload()``                     |
| Upload ignorado para arquivo repetido | ``_render_upload()``                     |
| Upload de arquivo inválido exibe erro | ``_render_upload()``                     |
| Lista de notícias renderiza cards     | ``_render_news_list()``                  |
| Selecionar notícia popula editor      | ``_render_news_list()`` /                |
|                                       | ``_load_news_into_editor()``             |
| Salvar sem selecionar não envia       | ``_render_editor()`` — botão Salvar      |
| Salvar persiste campos editados       | ``_render_editor()`` — botão Salvar      |
| Gerar IA sem chave exibe erro         | ``_render_editor()`` / ``_get_ia_svc()`` |
| Gerar IA com chave preenche campos    | ``_render_editor()`` — botão Gerar IA   |
| Publicar notícia não implementada     | ``_render_editor()`` — botão Publicar   |
+---------------------------------------+------------------------------------------+
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Importações condicionais do AppTest
# ---------------------------------------------------------------------------
try:
    from streamlit.testing.v1 import AppTest
    _APPTEST_AVAILABLE = True
except ImportError:  # Streamlit < 1.18
    _APPTEST_AVAILABLE = False

requires_apptest = pytest.mark.skipif(
    not _APPTEST_AVAILABLE,
    reason="streamlit.testing.v1.AppTest requer Streamlit >= 1.18",
)

# Caminho absoluto para o entry-point da aplicação
_APP_PATH = str(Path(__file__).parent.parent.parent / "app.py")


# ---------------------------------------------------------------------------
# Fixtures de infraestrutura mockada
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_news_service():
    """NewsService sem banco de dados."""
    svc = MagicMock()
    svc.list_all.return_value = []
    svc.update_fields.side_effect = lambda **kw: MagicMock(id=kw.get("news_id"))
    return svc


@pytest.fixture
def mock_parse_uc():
    """ParseDocxUseCase que devolve uma notícia fictícia."""
    from src.domain.entities.news import News

    uc = MagicMock()
    uc.execute.return_value = [
        News(titulo="Notícia Fake", conteudo="Conteúdo fake", source_file="test.docx")
    ]
    return uc


@pytest.fixture
def mock_ia_service():
    """IAService com respostas fixas."""
    svc = MagicMock()
    svc.gerar_titulo.return_value = "Título Gerado"
    svc.gerar_resumo.return_value = "Resumo gerado."
    svc.melhorar_conteudo.return_value = "Conteúdo melhorado."
    svc.gerar_texto_alternativo.return_value = "Alt text gerado."
    return svc


# ---------------------------------------------------------------------------
# 1. Inicialização da aplicação
# ---------------------------------------------------------------------------


@requires_apptest
class TestAppInitialization:
    """Verifica que o app sobe sem erros mesmo sem banco ou chave de IA."""

    def test_app_roda_sem_erro_com_servicos_mockados(
        self, mock_news_service, mock_parse_uc
    ) -> None:
        """main() deve completar o primeiro render sem levantar exceções."""
        with (
            patch("app._build_services", return_value=(mock_news_service, mock_parse_uc, MagicMock())),
            patch("app._init_engine"),
        ):
            at = AppTest.from_file(_APP_PATH)
            at.run()

        assert not at.exception

    def test_session_state_inicializado_com_chaves_obrigatorias(
        self, mock_news_service, mock_parse_uc
    ) -> None:
        """_init_state() deve garantir que todas as chaves existam."""
        with (
            patch("app._build_services", return_value=(mock_news_service, mock_parse_uc, MagicMock())),
            patch("app._init_engine"),
        ):
            at = AppTest.from_file(_APP_PATH)
            at.run()

        assert "selected_news_id" in at.session_state
        assert "editor_titulo" in at.session_state
        assert "editor_conteudo" in at.session_state
        assert "editor_resumo" in at.session_state
        assert "editor_categoria" in at.session_state
        assert "editor_imagem" in at.session_state
        assert "editor_texto_alternativo" in at.session_state


# ---------------------------------------------------------------------------
# 2. Upload de arquivo
# ---------------------------------------------------------------------------


@requires_apptest
class TestUploadSection:
    """Testes do widget de upload e acionamento do ParseDocxUseCase."""

    def test_upload_valido_aciona_parse_use_case(
        self, mock_news_service, mock_parse_uc
    ) -> None:
        """Enviar um .docx deve chamar parse_uc.execute() exatamente uma vez."""
        with (
            patch("app._build_services", return_value=(mock_news_service, mock_parse_uc, MagicMock())),
            patch("app._init_engine"),
        ):
            at = AppTest.from_file(_APP_PATH)
            at.run()
            at.get("file_uploader")[0].set_value(b"conteudo-docx-fake", "relatorio.docx")
            at.run()

        mock_parse_uc.execute.assert_called_once()

    def test_upload_do_mesmo_arquivo_nao_reprocessa(
        self, mock_news_service, mock_parse_uc
    ) -> None:
        """Reenviar o mesmo arquivo não deve chamar parse_uc.execute() novamente."""
        with (
            patch("app._build_services", return_value=(mock_news_service, mock_parse_uc, MagicMock())),
            patch("app._init_engine"),
        ):
            at = AppTest.from_file(_APP_PATH)
            at.run()
            at.session_state["_last_uploaded_name"] = "relatorio.docx"
            at.get("file_uploader")[0].set_value(b"bytes", "relatorio.docx")
            at.run()

        mock_parse_uc.execute.assert_not_called()

    def test_upload_invalido_exibe_mensagem_de_erro(
        self, mock_news_service, mock_parse_uc
    ) -> None:
        """Arquivo que gera ValueError deve exibir st.error na interface."""
        mock_parse_uc.execute.side_effect = ValueError("Nenhuma notícia encontrada.")

        with (
            patch("app._build_services", return_value=(mock_news_service, mock_parse_uc, MagicMock())),
            patch("app._init_engine"),
        ):
            at = AppTest.from_file(_APP_PATH)
            at.run()
            at.get("file_uploader")[0].set_value(b"bytes", "vazio.docx")
            at.run()

        assert len(at.error) > 0


# ---------------------------------------------------------------------------
# 3. Lista de notícias
# ---------------------------------------------------------------------------


@requires_apptest
class TestNewsListSection:
    """Testes de renderização e seleção na lista de notícias."""

    def _news_dto(self, titulo: str = "Notícia X"):
        from src.application.dtos.news_dto import NewsDTO
        from src.domain.entities.news import NewsStatus
        return NewsDTO(
            id="id-abc",
            titulo=titulo,
            conteudo="Conteúdo",
            source_file="f.docx",
            status=NewsStatus.PENDING,
        )

    def test_lista_vazia_exibe_caption_informativo(
        self, mock_news_service, mock_parse_uc
    ) -> None:
        """Sem notícias, deve exibir instrução de upload."""
        mock_news_service.list_all.return_value = []

        with (
            patch("app._build_services", return_value=(mock_news_service, mock_parse_uc, MagicMock())),
            patch("app._init_engine"),
        ):
            at = AppTest.from_file(_APP_PATH)
            at.run()

        assert any("docx" in c.value.lower() for c in at.caption)

    def test_clicar_noticia_define_selected_news_id(
        self, mock_news_service, mock_parse_uc
    ) -> None:
        """Clicar em uma notícia da lista deve persistir seu ID no session_state."""
        dto = self._news_dto()
        mock_news_service.list_all.return_value = [dto]

        with (
            patch("app._build_services", return_value=(mock_news_service, mock_parse_uc, MagicMock())),
            patch("app._init_engine"),
        ):
            at = AppTest.from_file(_APP_PATH)
            at.run()
            at.button(key=f"news_btn_{dto.id}").click()
            at.run()

        assert at.session_state["selected_news_id"] == dto.id

    def test_selecionar_noticia_popula_editor(
        self, mock_news_service, mock_parse_uc
    ) -> None:
        """Selecionar notícia deve copiar seus dados para as chaves de editor."""
        from src.application.dtos.news_dto import NewsDTO
        from src.domain.entities.news import NewsStatus

        dto = NewsDTO(
            id="id-pop",
            titulo="Título Esperado",
            conteudo="Conteúdo Esperado",
            source_file="f.docx",
            status=NewsStatus.PENDING,
            resumo="Resumo Esperado",
        )
        mock_news_service.list_all.return_value = [dto]

        with (
            patch("app._build_services", return_value=(mock_news_service, mock_parse_uc, MagicMock())),
            patch("app._init_engine"),
        ):
            at = AppTest.from_file(_APP_PATH)
            at.run()
            at.button(key=f"news_btn_{dto.id}").click()
            at.run()

        assert at.session_state["editor_titulo"] == "Título Esperado"
        assert at.session_state["editor_conteudo"] == "Conteúdo Esperado"
        assert at.session_state["editor_resumo"] == "Resumo Esperado"


# ---------------------------------------------------------------------------
# 4. Botão Salvar
# ---------------------------------------------------------------------------


@requires_apptest
class TestSalvarButton:
    """Testes do botão Salvar no editor."""

    def _setup_with_selected_news(self):
        from src.application.dtos.news_dto import NewsDTO
        from src.domain.entities.news import NewsStatus

        dto = NewsDTO(
            id="id-salvar",
            titulo="Título",
            conteudo="Conteúdo",
            source_file="f.docx",
            status=NewsStatus.PENDING,
        )
        return dto

    def test_salvar_chama_news_service_update_fields(
        self, mock_news_service, mock_parse_uc
    ) -> None:
        """Clicar em Salvar deve chamar news_service.update_fields com os valores do editor."""
        dto = self._setup_with_selected_news()
        mock_news_service.list_all.return_value = [dto]
        mock_news_service.update_fields.return_value = dto

        with (
            patch("app._build_services", return_value=(mock_news_service, mock_parse_uc, MagicMock())),
            patch("app._init_engine"),
        ):
            at = AppTest.from_file(_APP_PATH)
            at.run()
            at.session_state["selected_news_id"] = dto.id
            at.session_state["_last_selected_id"] = dto.id
            at.session_state["editor_titulo"] = "Título Editado"
            at.session_state["editor_conteudo"] = "Conteúdo Editado"
            at.button("💾 Salvar").click()
            at.run()

        mock_news_service.update_fields.assert_called_once()
        call_kwargs = mock_news_service.update_fields.call_args.kwargs
        assert call_kwargs["titulo"] == "Título Editado"
        assert call_kwargs["conteudo"] == "Conteúdo Editado"

    def test_salvar_exibe_mensagem_de_sucesso(
        self, mock_news_service, mock_parse_uc
    ) -> None:
        """Salvar bem-sucedido deve exibir st.success."""
        dto = self._setup_with_selected_news()
        mock_news_service.list_all.return_value = [dto]
        mock_news_service.update_fields.return_value = dto

        with (
            patch("app._build_services", return_value=(mock_news_service, mock_parse_uc, MagicMock())),
            patch("app._init_engine"),
        ):
            at = AppTest.from_file(_APP_PATH)
            at.run()
            at.session_state["selected_news_id"] = dto.id
            at.session_state["_last_selected_id"] = dto.id
            at.button("💾 Salvar").click()
            at.run()

        assert len(at.success) > 0

    def test_salvar_exibe_erro_quando_service_falha(
        self, mock_news_service, mock_parse_uc
    ) -> None:
        """Exceção em update_fields deve exibir st.error na interface."""
        dto = self._setup_with_selected_news()
        mock_news_service.list_all.return_value = [dto]
        mock_news_service.update_fields.side_effect = ValueError("Notícia 'x' não encontrada.")

        with (
            patch("app._build_services", return_value=(mock_news_service, mock_parse_uc, MagicMock())),
            patch("app._init_engine"),
        ):
            at = AppTest.from_file(_APP_PATH)
            at.run()
            at.session_state["selected_news_id"] = dto.id
            at.session_state["_last_selected_id"] = dto.id
            at.button("💾 Salvar").click()
            at.run()

        assert len(at.error) > 0


# ---------------------------------------------------------------------------
# 5. Botão Gerar IA
# ---------------------------------------------------------------------------


@requires_apptest
class TestGerarIAButton:
    """Testes do botão Gerar IA no editor."""

    def test_gerar_ia_sem_api_key_exibe_erro(
        self, mock_news_service, mock_parse_uc
    ) -> None:
        """_get_ia_service() sem OPENAI_API_KEY deve exibir st.error com instrução."""
        from src.application.dtos.news_dto import NewsDTO
        from src.domain.entities.news import NewsStatus

        dto = NewsDTO(
            id="id-ia",
            titulo="T",
            conteudo="C",
            source_file="f.docx",
            status=NewsStatus.PENDING,
        )
        mock_news_service.list_all.return_value = [dto]

        with (
            patch("app._build_services", return_value=(mock_news_service, mock_parse_uc, MagicMock())),
            patch("app._init_engine"),
            patch("app.settings") as mock_settings,
        ):
            mock_settings.openai_api_key = ""
            at = AppTest.from_file(_APP_PATH)
            at.run()
            at.session_state["selected_news_id"] = dto.id
            at.session_state["_last_selected_id"] = dto.id
            at.session_state["editor_conteudo"] = "Conteúdo para gerar."
            at.button("🤖 Gerar IA").click()
            at.run()

        assert len(at.error) > 0 or len(at.warning) > 0

    def test_gerar_ia_com_service_mockado_preenche_campos(
        self, mock_news_service, mock_parse_uc, mock_ia_service
    ) -> None:
        """Gerar IA com serviço disponível deve preencher todos os campos do editor."""
        from src.application.dtos.news_dto import NewsDTO
        from src.domain.entities.news import NewsStatus

        dto = NewsDTO(
            id="id-ia2",
            titulo="T",
            conteudo="C",
            source_file="f.docx",
            status=NewsStatus.PENDING,
        )
        mock_news_service.list_all.return_value = [dto]

        with (
            patch("app._build_services", return_value=(mock_news_service, mock_parse_uc, MagicMock())),
            patch("app._init_engine"),
            patch("app._get_ia_service", return_value=mock_ia_service),
        ):
            at = AppTest.from_file(_APP_PATH)
            at.run()
            at.session_state["selected_news_id"] = dto.id
            at.session_state["_last_selected_id"] = dto.id
            at.session_state["editor_conteudo"] = "Conteúdo para gerar."
            at.button("🤖 Gerar IA").click()
            at.run()

        assert at.session_state["editor_titulo"] == "Título Gerado"
        assert at.session_state["editor_resumo"] == "Resumo gerado."
        assert at.session_state["editor_conteudo"] == "Conteúdo melhorado."
        assert at.session_state["editor_texto_alternativo"] == "Alt text gerado."

    def test_gerar_ia_sem_conteudo_exibe_aviso(
        self, mock_news_service, mock_parse_uc
    ) -> None:
        """Campo Conteúdo vazio deve exibir st.warning sem chamar o serviço de IA."""
        from src.application.dtos.news_dto import NewsDTO
        from src.domain.entities.news import NewsStatus

        dto = NewsDTO(
            id="id-ia3",
            titulo="T",
            conteudo="",
            source_file="f.docx",
            status=NewsStatus.PENDING,
        )
        mock_news_service.list_all.return_value = [dto]

        with (
            patch("app._build_services", return_value=(mock_news_service, mock_parse_uc, MagicMock())),
            patch("app._init_engine"),
        ):
            at = AppTest.from_file(_APP_PATH)
            at.run()
            at.session_state["selected_news_id"] = dto.id
            at.session_state["_last_selected_id"] = dto.id
            at.session_state["editor_conteudo"] = ""
            at.button("🤖 Gerar IA").click()
            at.run()

        assert len(at.warning) > 0


# ---------------------------------------------------------------------------
# 6. Botão Publicar
# ---------------------------------------------------------------------------


@requires_apptest
class TestPublicarButton:
    """Testes do botão Publicar no editor."""

    def test_publicar_nao_implementado_exibe_aviso(
        self, mock_news_service, mock_parse_uc
    ) -> None:
        """PublishNewsUseCase retornando None deve exibir st.warning."""
        from src.application.dtos.news_dto import NewsDTO
        from src.domain.entities.news import NewsStatus

        dto = NewsDTO(
            id="id-pub",
            titulo="T",
            conteudo="C",
            source_file="f.docx",
            status=NewsStatus.REVIEWED,
        )
        mock_news_service.list_all.return_value = [dto]

        mock_publish_uc = MagicMock()
        mock_publish_uc.execute.return_value = None  # stub não implementado

        with (
            patch(
                "app._build_services",
                return_value=(mock_news_service, mock_parse_uc, mock_publish_uc),
            ),
            patch("app._init_engine"),
        ):
            at = AppTest.from_file(_APP_PATH)
            at.run()
            at.session_state["selected_news_id"] = dto.id
            at.session_state["_last_selected_id"] = dto.id
            at.button("🚀 Publicar").click()
            at.run()

        assert len(at.warning) > 0

    def test_publicar_com_sucesso_exibe_mensagem(
        self, mock_news_service, mock_parse_uc
    ) -> None:
        """Publicação bem-sucedida deve exibir st.success com o ID da publicação."""
        from src.application.dtos.news_dto import NewsDTO
        from src.domain.entities.publication import Publication, PublicationStatus
        from src.domain.entities.news import NewsStatus

        dto = NewsDTO(
            id="id-pub2",
            titulo="T",
            conteudo="C",
            source_file="f.docx",
            status=NewsStatus.REVIEWED,
        )
        pub = Publication(news_id=dto.id, portal_url="http://portal.example.com")
        mock_news_service.list_all.return_value = [dto]

        mock_publish_uc = MagicMock()
        mock_publish_uc.execute.return_value = pub

        with (
            patch(
                "app._build_services",
                return_value=(mock_news_service, mock_parse_uc, mock_publish_uc),
            ),
            patch("app._init_engine"),
        ):
            at = AppTest.from_file(_APP_PATH)
            at.run()
            at.session_state["selected_news_id"] = dto.id
            at.session_state["_last_selected_id"] = dto.id
            at.button("🚀 Publicar").click()
            at.run()

        assert len(at.success) > 0
