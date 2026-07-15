"""Testes unitários do NewsService.

Estratégia de isolamento
------------------------
- ``INewsRepository`` é substituído por um ``MagicMock`` para que o
  NewsService seja testado sem depender de banco de dados.
- Cada método público é testado de forma independente, cobrindo:
    * retorno correto e mapeamento completo de campos (DTO ↔ entidade)
    * comportamento com listas vazias e itens múltiplos
    * propagação de ValueError quando a notícia não é encontrada
    * garantia de que ``repository.update`` é chamado com os valores corretos
    * atualização do campo ``updated_at`` ao salvar
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from unittest.mock import MagicMock, call

import pytest

from src.application.dtos.news_dto import NewsDTO
from src.application.services.news_service import NewsService
from src.domain.entities.news import News, NewsStatus
from src.domain.interfaces.news_repository import INewsRepository


# ---------------------------------------------------------------------------
# Fixtures e fábricas
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_repo() -> MagicMock:
    """Mock do INewsRepository com comportamento padrão configurado."""
    repo = MagicMock(spec=INewsRepository)
    repo.update.side_effect = lambda news: news
    return repo


@pytest.fixture
def service(mock_repo: MagicMock) -> NewsService:
    return NewsService(news_repository=mock_repo)


def _make_news(
    titulo: str = "Título de Teste",
    conteudo: str = "Corpo da notícia.",
    source_file: str = "boletim.docx",
    status: NewsStatus = NewsStatus.PENDING,
    resumo: Optional[str] = "Resumo.",
    categoria: Optional[str] = "Tecnologia",
    imagem: Optional[str] = "img.jpg",
    texto_alternativo: Optional[str] = "Alt text.",
    reviewed_content: Optional[str] = None,
) -> News:
    return News(
        titulo=titulo,
        conteudo=conteudo,
        source_file=source_file,
        status=status,
        resumo=resumo,
        categoria=categoria,
        imagem=imagem,
        texto_alternativo=texto_alternativo,
        reviewed_content=reviewed_content,
    )


# ---------------------------------------------------------------------------
# list_all
# ---------------------------------------------------------------------------


class TestNewsServiceListAll:
    """Testes do método list_all."""

    def test_retorna_lista_vazia_quando_nao_ha_noticias(
        self, service: NewsService, mock_repo: MagicMock
    ) -> None:
        mock_repo.find_all.return_value = []

        resultado = service.list_all()

        assert resultado == []

    def test_retorna_lista_com_um_dto_por_noticia(
        self, service: NewsService, mock_repo: MagicMock
    ) -> None:
        mock_repo.find_all.return_value = [_make_news(), _make_news(), _make_news()]

        resultado = service.list_all()

        assert len(resultado) == 3
        assert all(isinstance(dto, NewsDTO) for dto in resultado)

    def test_mapeia_todos_os_campos_obrigatorios(
        self, service: NewsService, mock_repo: MagicMock
    ) -> None:
        news = _make_news(titulo="Notícia Especial", conteudo="Conteúdo X")
        mock_repo.find_all.return_value = [news]

        resultado = service.list_all()

        dto = resultado[0]
        assert dto.id == news.id
        assert dto.titulo == "Notícia Especial"
        assert dto.conteudo == "Conteúdo X"
        assert dto.source_file == "boletim.docx"
        assert dto.status == NewsStatus.PENDING

    def test_mapeia_campos_opcionais(
        self, service: NewsService, mock_repo: MagicMock
    ) -> None:
        news = _make_news(
            resumo="Resumo aqui",
            categoria="Política",
            imagem="foto.png",
            texto_alternativo="Foto do evento",
        )
        mock_repo.find_all.return_value = [news]

        dto = service.list_all()[0]

        assert dto.resumo == "Resumo aqui"
        assert dto.categoria == "Política"
        assert dto.imagem == "foto.png"
        assert dto.texto_alternativo == "Foto do evento"

    def test_mapeia_campos_opcionais_como_none(
        self, service: NewsService, mock_repo: MagicMock
    ) -> None:
        news = _make_news(resumo=None, categoria=None, imagem=None, texto_alternativo=None)
        mock_repo.find_all.return_value = [news]

        dto = service.list_all()[0]

        assert dto.resumo is None
        assert dto.categoria is None
        assert dto.imagem is None
        assert dto.texto_alternativo is None

    def test_mapeia_reviewed_content(
        self, service: NewsService, mock_repo: MagicMock
    ) -> None:
        news = _make_news(reviewed_content="Conteúdo revisado pela IA.")
        mock_repo.find_all.return_value = [news]

        dto = service.list_all()[0]

        assert dto.reviewed_content == "Conteúdo revisado pela IA."

    def test_mapeia_status_reviewed(
        self, service: NewsService, mock_repo: MagicMock
    ) -> None:
        news = _make_news(status=NewsStatus.REVIEWED)
        mock_repo.find_all.return_value = [news]

        dto = service.list_all()[0]

        assert dto.status == NewsStatus.REVIEWED

    def test_mapeia_status_published(
        self, service: NewsService, mock_repo: MagicMock
    ) -> None:
        news = _make_news(status=NewsStatus.PUBLISHED)
        mock_repo.find_all.return_value = [news]

        dto = service.list_all()[0]

        assert dto.status == NewsStatus.PUBLISHED

    def test_chama_find_all_exatamente_uma_vez(
        self, service: NewsService, mock_repo: MagicMock
    ) -> None:
        mock_repo.find_all.return_value = []

        service.list_all()

        mock_repo.find_all.assert_called_once()

    def test_preserva_ordem_das_noticias(
        self, service: NewsService, mock_repo: MagicMock
    ) -> None:
        noticias = [_make_news(titulo=f"Notícia {i}") for i in range(5)]
        mock_repo.find_all.return_value = noticias

        dtos = service.list_all()

        assert [d.titulo for d in dtos] == [f"Notícia {i}" for i in range(5)]


# ---------------------------------------------------------------------------
# find_by_id
# ---------------------------------------------------------------------------


class TestNewsServiceFindById:
    """Testes do método find_by_id."""

    def test_retorna_dto_quando_noticia_existe(
        self, service: NewsService, mock_repo: MagicMock
    ) -> None:
        news = _make_news()
        mock_repo.find_by_id.return_value = news

        resultado = service.find_by_id(news.id)

        assert resultado is not None
        assert resultado.id == news.id

    def test_retorna_none_quando_noticia_nao_existe(
        self, service: NewsService, mock_repo: MagicMock
    ) -> None:
        mock_repo.find_by_id.return_value = None

        resultado = service.find_by_id("id-inexistente")

        assert resultado is None

    def test_passa_id_correto_para_o_repositorio(
        self, service: NewsService, mock_repo: MagicMock
    ) -> None:
        mock_repo.find_by_id.return_value = None
        news_id = "abc-123"

        service.find_by_id(news_id)

        mock_repo.find_by_id.assert_called_once_with(news_id)

    def test_mapeia_todos_os_campos_do_dto(
        self, service: NewsService, mock_repo: MagicMock
    ) -> None:
        news = _make_news(
            titulo="Título Completo",
            conteudo="Conteúdo Completo",
            resumo="Resumo",
            categoria="Ciência",
            imagem="img.jpg",
            texto_alternativo="Alt",
            reviewed_content="Revisado",
            status=NewsStatus.REVIEWED,
        )
        mock_repo.find_by_id.return_value = news

        dto = service.find_by_id(news.id)

        assert dto.titulo == "Título Completo"
        assert dto.conteudo == "Conteúdo Completo"
        assert dto.resumo == "Resumo"
        assert dto.categoria == "Ciência"
        assert dto.imagem == "img.jpg"
        assert dto.texto_alternativo == "Alt"
        assert dto.reviewed_content == "Revisado"
        assert dto.status == NewsStatus.REVIEWED


# ---------------------------------------------------------------------------
# update_fields
# ---------------------------------------------------------------------------


class TestNewsServiceUpdateFields:
    """Testes do método update_fields."""

    def test_levanta_value_error_quando_noticia_nao_existe(
        self, service: NewsService, mock_repo: MagicMock
    ) -> None:
        mock_repo.find_by_id.return_value = None

        with pytest.raises(ValueError, match="não encontrada"):
            service.update_fields(
                news_id="id-inexistente",
                titulo="Título",
                conteudo="Conteúdo",
            )

    def test_nao_chama_update_quando_noticia_nao_existe(
        self, service: NewsService, mock_repo: MagicMock
    ) -> None:
        mock_repo.find_by_id.return_value = None

        with pytest.raises(ValueError):
            service.update_fields("id-inexistente", "T", "C")

        mock_repo.update.assert_not_called()

    def test_atualiza_titulo_e_conteudo(
        self, service: NewsService, mock_repo: MagicMock
    ) -> None:
        news = _make_news(titulo="Antigo", conteudo="Antigo conteúdo")
        mock_repo.find_by_id.return_value = news

        service.update_fields(
            news_id=news.id,
            titulo="Novo Título",
            conteudo="Novo conteúdo",
        )

        entidade_salva: News = mock_repo.update.call_args[0][0]
        assert entidade_salva.titulo == "Novo Título"
        assert entidade_salva.conteudo == "Novo conteúdo"

    def test_atualiza_campos_opcionais(
        self, service: NewsService, mock_repo: MagicMock
    ) -> None:
        news = _make_news()
        mock_repo.find_by_id.return_value = news

        service.update_fields(
            news_id=news.id,
            titulo="T",
            conteudo="C",
            resumo="Novo resumo",
            categoria="Esporte",
            imagem="nova.jpg",
            texto_alternativo="Nova alt",
        )

        entidade_salva: News = mock_repo.update.call_args[0][0]
        assert entidade_salva.resumo == "Novo resumo"
        assert entidade_salva.categoria == "Esporte"
        assert entidade_salva.imagem == "nova.jpg"
        assert entidade_salva.texto_alternativo == "Nova alt"

    def test_aceita_campos_opcionais_como_none(
        self, service: NewsService, mock_repo: MagicMock
    ) -> None:
        news = _make_news(resumo="Velho", categoria="Velho")
        mock_repo.find_by_id.return_value = news

        service.update_fields(
            news_id=news.id,
            titulo="T",
            conteudo="C",
            resumo=None,
            categoria=None,
            imagem=None,
            texto_alternativo=None,
        )

        entidade_salva: News = mock_repo.update.call_args[0][0]
        assert entidade_salva.resumo is None
        assert entidade_salva.categoria is None
        assert entidade_salva.imagem is None
        assert entidade_salva.texto_alternativo is None

    def test_chama_repository_update_exatamente_uma_vez(
        self, service: NewsService, mock_repo: MagicMock
    ) -> None:
        news = _make_news()
        mock_repo.find_by_id.return_value = news

        service.update_fields(news.id, "T", "C")

        mock_repo.update.assert_called_once()

    def test_passa_a_mesma_entidade_para_update(
        self, service: NewsService, mock_repo: MagicMock
    ) -> None:
        news = _make_news()
        mock_repo.find_by_id.return_value = news

        service.update_fields(news.id, "T", "C")

        entidade_salva: News = mock_repo.update.call_args[0][0]
        assert entidade_salva.id == news.id

    def test_retorna_dto_com_valores_atualizados(
        self, service: NewsService, mock_repo: MagicMock
    ) -> None:
        news = _make_news()
        mock_repo.find_by_id.return_value = news

        dto = service.update_fields(
            news_id=news.id,
            titulo="Título Atualizado",
            conteudo="Conteúdo Atualizado",
        )

        assert isinstance(dto, NewsDTO)
        assert dto.titulo == "Título Atualizado"
        assert dto.conteudo == "Conteúdo Atualizado"

    def test_atualiza_updated_at(
        self, service: NewsService, mock_repo: MagicMock
    ) -> None:
        news = _make_news()
        before = news.updated_at
        mock_repo.find_by_id.return_value = news

        service.update_fields(news.id, "T", "C")

        entidade_salva: News = mock_repo.update.call_args[0][0]
        assert entidade_salva.updated_at >= before

    def test_nao_altera_status_ao_salvar(
        self, service: NewsService, mock_repo: MagicMock
    ) -> None:
        news = _make_news(status=NewsStatus.REVIEWED)
        mock_repo.find_by_id.return_value = news

        service.update_fields(news.id, "T", "C")

        entidade_salva: News = mock_repo.update.call_args[0][0]
        assert entidade_salva.status == NewsStatus.REVIEWED

    def test_nao_altera_reviewed_content_ao_salvar(
        self, service: NewsService, mock_repo: MagicMock
    ) -> None:
        news = _make_news(reviewed_content="Conteúdo revisado")
        mock_repo.find_by_id.return_value = news

        service.update_fields(news.id, "T", "C")

        entidade_salva: News = mock_repo.update.call_args[0][0]
        assert entidade_salva.reviewed_content == "Conteúdo revisado"

    def test_mensagem_de_erro_contem_id(
        self, service: NewsService, mock_repo: MagicMock
    ) -> None:
        mock_repo.find_by_id.return_value = None

        with pytest.raises(ValueError, match="id-especifico-xyz"):
            service.update_fields("id-especifico-xyz", "T", "C")
