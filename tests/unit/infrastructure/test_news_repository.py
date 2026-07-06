"""Testes unitários do NewsRepository com SQLite em memória."""
from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from src.domain.entities.news import News, NewsStatus
from src.infrastructure.repositories.news_repository import NewsRepository


def _make_news(**kwargs) -> News:
    """Fábrica auxiliar de notícias com valores padrão."""
    defaults = dict(
        titulo="Título de teste",
        conteudo="Conteúdo de teste",
        source_file="arquivo.docx",
        resumo="Resumo de teste",
        categoria="Tecnologia",
        imagem="imagem.jpg",
        texto_alternativo="Imagem descritiva",
    )
    defaults.update(kwargs)
    return News(**defaults)


class TestNewsRepositorySave:
    """Testes para o método save."""

    def test_save_retorna_a_entidade_persistida(self, in_memory_session: Session) -> None:
        repo = NewsRepository(in_memory_session)
        news = _make_news()

        salva = repo.save(news)

        assert salva.id == news.id
        assert salva.titulo == "Título de teste"
        assert salva.conteudo == "Conteúdo de teste"
        assert salva.resumo == "Resumo de teste"
        assert salva.categoria == "Tecnologia"
        assert salva.imagem == "imagem.jpg"
        assert salva.texto_alternativo == "Imagem descritiva"
        assert salva.status == NewsStatus.PENDING

    def test_save_persiste_no_banco(self, in_memory_session: Session) -> None:
        repo = NewsRepository(in_memory_session)
        news = _make_news()

        repo.save(news)
        in_memory_session.commit()

        recuperada = repo.find_by_id(news.id)
        assert recuperada is not None
        assert recuperada.id == news.id

    def test_save_multiplas_noticias(self, in_memory_session: Session) -> None:
        repo = NewsRepository(in_memory_session)

        repo.save(_make_news(titulo="Notícia 1"))
        repo.save(_make_news(titulo="Notícia 2"))
        repo.save(_make_news(titulo="Notícia 3"))

        assert len(repo.find_all()) == 3

    def test_save_campos_opcionais_nulos(self, in_memory_session: Session) -> None:
        repo = NewsRepository(in_memory_session)
        news = _make_news(resumo=None, categoria=None, imagem=None, texto_alternativo=None)

        salva = repo.save(news)

        assert salva.resumo is None
        assert salva.categoria is None
        assert salva.imagem is None
        assert salva.texto_alternativo is None


class TestNewsRepositoryFindById:
    """Testes para o método find_by_id."""

    def test_find_by_id_retorna_entidade_correta(self, in_memory_session: Session) -> None:
        repo = NewsRepository(in_memory_session)
        news = _make_news(titulo="Busca por ID")
        repo.save(news)

        encontrada = repo.find_by_id(news.id)

        assert encontrada is not None
        assert encontrada.id == news.id
        assert encontrada.titulo == "Busca por ID"

    def test_find_by_id_retorna_none_quando_nao_existe(self, in_memory_session: Session) -> None:
        repo = NewsRepository(in_memory_session)

        resultado = repo.find_by_id("id-inexistente")

        assert resultado is None


class TestNewsRepositoryFindAll:
    """Testes para o método find_all."""

    def test_find_all_retorna_lista_vazia_sem_registros(self, in_memory_session: Session) -> None:
        repo = NewsRepository(in_memory_session)

        assert repo.find_all() == []

    def test_find_all_retorna_todas_as_noticias(self, in_memory_session: Session) -> None:
        repo = NewsRepository(in_memory_session)
        repo.save(_make_news(titulo="N1"))
        repo.save(_make_news(titulo="N2"))

        resultado = repo.find_all()

        assert len(resultado) == 2
        titulos = {n.titulo for n in resultado}
        assert titulos == {"N1", "N2"}

    def test_find_all_preserva_todos_os_campos(self, in_memory_session: Session) -> None:
        repo = NewsRepository(in_memory_session)
        repo.save(_make_news())

        noticias = repo.find_all()

        assert len(noticias) == 1
        n = noticias[0]
        assert n.resumo == "Resumo de teste"
        assert n.categoria == "Tecnologia"
        assert n.imagem == "imagem.jpg"
        assert n.texto_alternativo == "Imagem descritiva"


class TestNewsRepositoryUpdate:
    """Testes para o método update."""

    def test_update_altera_campos_da_noticia(self, in_memory_session: Session) -> None:
        repo = NewsRepository(in_memory_session)
        news = _make_news()
        repo.save(news)

        news.titulo = "Título atualizado"
        news.conteudo = "Conteúdo atualizado"
        news.resumo = "Resumo atualizado"
        news.categoria = "Política"
        news.imagem = "nova_imagem.jpg"
        news.texto_alternativo = "Nova descrição"
        atualizada = repo.update(news)

        assert atualizada.titulo == "Título atualizado"
        assert atualizada.conteudo == "Conteúdo atualizado"
        assert atualizada.resumo == "Resumo atualizado"
        assert atualizada.categoria == "Política"
        assert atualizada.imagem == "nova_imagem.jpg"
        assert atualizada.texto_alternativo == "Nova descrição"

    def test_update_altera_status(self, in_memory_session: Session) -> None:
        repo = NewsRepository(in_memory_session)
        news = _make_news()
        repo.save(news)

        news.mark_as_reviewed("Conteúdo revisado pela IA")
        atualizada = repo.update(news)

        assert atualizada.status == NewsStatus.REVIEWED
        assert atualizada.reviewed_content == "Conteúdo revisado pela IA"

    def test_update_persiste_alteracao_no_banco(self, in_memory_session: Session) -> None:
        repo = NewsRepository(in_memory_session)
        news = _make_news()
        repo.save(news)

        news.titulo = "Título persistido"
        repo.update(news)
        in_memory_session.commit()

        recarregada = repo.find_by_id(news.id)
        assert recarregada is not None
        assert recarregada.titulo == "Título persistido"

    def test_update_levanta_erro_para_id_inexistente(self, in_memory_session: Session) -> None:
        repo = NewsRepository(in_memory_session)
        news = _make_news()  # não salva

        with pytest.raises(ValueError, match=news.id):
            repo.update(news)


class TestNewsRepositoryDelete:
    """Testes para o método delete."""

    def test_delete_remove_a_noticia(self, in_memory_session: Session) -> None:
        repo = NewsRepository(in_memory_session)
        news = _make_news()
        repo.save(news)

        repo.delete(news.id)

        assert repo.find_by_id(news.id) is None

    def test_delete_nao_afeta_outras_noticias(self, in_memory_session: Session) -> None:
        repo = NewsRepository(in_memory_session)
        n1 = _make_news(titulo="Manter")
        n2 = _make_news(titulo="Remover")
        repo.save(n1)
        repo.save(n2)

        repo.delete(n2.id)

        assert repo.find_by_id(n1.id) is not None
        assert repo.find_by_id(n2.id) is None
        assert len(repo.find_all()) == 1

    def test_delete_id_inexistente_nao_levanta_excecao(self, in_memory_session: Session) -> None:
        repo = NewsRepository(in_memory_session)

        repo.delete("id-que-nao-existe")  # não deve lançar

