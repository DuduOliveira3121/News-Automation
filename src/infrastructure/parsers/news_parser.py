"""Parser de documentos Word (.docx) para extração de notícias.

Premissas adotadas sobre a estrutura do documento
==================================================

1. **Separador de notícia — Heading 1**
   Cada notícia começa obrigatoriamente com um parágrafo cujo estilo Word é
   "Heading 1" (PT: "Título 1").  O texto desse parágrafo é usado como título
   da notícia.  Qualquer conteúdo que apareça antes do primeiro "Heading 1"
   é ignorado silenciosamente.

2. **Corpo da notícia**
   Todos os parágrafos com estilo diferente de "Heading 1" que vêm após o
   título pertencem ao corpo daquela notícia.  O corpo se encerra quando um
   novo "Heading 1" ou o fim do documento é encontrado.

3. **Sub-títulos (Heading 2, Heading 3 …)**
   Tratados como parágrafos comuns do corpo — não iniciam uma nova notícia.

4. **Parágrafos vazios**
   Parágrafos sem texto visível são ignorados tanto no título quanto no corpo.
   Isso evita que quebras de página ou linhas em branco gerem artefatos.

5. **Tabelas**
   Quando uma tabela aparece dentro do corpo de uma notícia, o texto de cada
   célula é extraído.  Células da mesma linha são separadas por ``\\t``; linhas
   são separadas por ``\\n``.  O bloco de texto resultante é inserido no corpo
   como se fosse um parágrafo normal.

6. **Concatenação do corpo**
   Os blocos de texto (parágrafos e tabelas) são unidos com ``\\n\\n``.

7. **Encoding**
   A biblioteca *python-docx* retorna strings Unicode nativas.  Nenhum
   tratamento adicional de encoding é realizado.

8. **Metadados do documento**
   Propriedades como autor, data de criação e número de revisão não são
   extraídas — somente título e corpo de cada notícia.

9. **Estilos localizados**
   Para cobrir instalações do Word em português, espanhol e francês, os nomes
   "Título 1", "Titulo 1" e "Rubrique 1" são aceitos como equivalentes a
   "Heading 1".  Outros idiomas podem ser adicionados em ``_HEADING1_STYLE_NAMES``.

Comportamento em caso de desvio das premissas
---------------------------------------------
- **Nenhum "Heading 1" no documento** → retorna lista vazia e emite aviso
  no log.
- **"Heading 1" com texto vazio** → o item é ignorado e um aviso é emitido.
- **Arquivo inexistente** → ``FileNotFoundError``.
- **Extensão diferente de .docx** → ``ValueError``.
- **Arquivo corrompido / ilegível** → ``ValueError``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Generator, List, Union

import docx
from docx.document import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constantes internas
# ---------------------------------------------------------------------------

#: Nomes de estilo que identificam o início de uma nova notícia.
#: Comparação feita em lowercase para evitar problemas de capitalização.
_HEADING1_STYLE_NAMES: frozenset[str] = frozenset(
    {
        "heading 1",   # inglês (padrão)
        "título 1",    # português (com acento)
        "titulo 1",    # português (sem acento)
        "rubrique 1",  # francês
        "título1",     # variação sem espaço
    }
)

#: Tags XML qualificadas usadas na iteração do body do documento.
_TAG_PARAGRAPH = qn("w:p")
_TAG_TABLE = qn("w:tbl")


# ---------------------------------------------------------------------------
# Dataclass de domínio do parser
# ---------------------------------------------------------------------------


@dataclass
class Noticia:
    """Representa uma notícia extraída de um documento Word.

    Esta dataclass é o contrato de saída do :class:`NewsParser`.  Camadas
    superiores (serviços, use-cases) podem mapeá-la para suas próprias
    estruturas de dados conforme necessário.

    Atributos:
        titulo: Texto do parágrafo "Heading 1" que abre a notícia.
            Nunca é vazio — itens com título vazio são descartados pelo parser.
        corpo: Texto concatenado dos parágrafos e tabelas que formam o corpo
            da notícia.  Blocos separados por ``\\n\\n``.  Pode ser vazio se
            o "Heading 1" não for seguido de nenhum conteúdo.
        arquivo_origem: Nome do arquivo .docx (sem caminho completo) de onde
            a notícia foi extraída.
        indice: Posição ordinal da notícia no documento, base 1.
            Útil para depuração e rastreabilidade.
    """

    titulo: str
    corpo: str
    arquivo_origem: str
    indice: int = field(default=0)


# ---------------------------------------------------------------------------
# Helpers privados
# ---------------------------------------------------------------------------


def _is_heading1(paragraph: Paragraph) -> bool:
    """Retorna ``True`` se *paragraph* tiver estilo "Heading 1" (qualquer idioma)."""
    return paragraph.style.name.lower() in _HEADING1_STYLE_NAMES


def _clean_text(paragraph: Paragraph) -> str:
    """Retorna o texto do parágrafo sem espaços nas extremidades."""
    return paragraph.text.strip()


def _table_to_text(table: Table) -> str:
    """Converte uma tabela Word em texto plano.

    Cada linha da tabela vira uma linha de texto; células são separadas por
    tabulação.  Células mescladas repetem o conteúdo para cada coluna lógica
    ocupada (comportamento padrão do python-docx).
    """
    rows: list[str] = []
    for row in table.rows:
        cells = [cell.text.strip() for cell in row.cells]
        row_text = "\t".join(cells)
        if row_text.strip():
            rows.append(row_text)
    return "\n".join(rows)


def _iter_block_items(
    document: Document,
) -> Generator[Union[Paragraph, Table], None, None]:
    """Itera os elementos de bloco do documento na ordem em que aparecem.

    python-docx expõe ``document.paragraphs`` e ``document.tables``
    separadamente, o que perde a ordenação relativa entre parágrafos e
    tabelas.  Esta função percorre diretamente o XML do ``<w:body>`` para
    preservar a ordem correta.

    Yields:
        Instâncias de :class:`~docx.text.paragraph.Paragraph` ou
        :class:`~docx.table.Table`.
    """
    for child in document.element.body:
        if child.tag == _TAG_PARAGRAPH:
            yield Paragraph(child, document)
        elif child.tag == _TAG_TABLE:
            yield Table(child, document)


# ---------------------------------------------------------------------------
# Classe principal
# ---------------------------------------------------------------------------


class NewsParser:
    """Extrai notícias de documentos Word (.docx).

    O parser não mantém estado entre chamadas; a mesma instância pode ser
    reutilizada para múltiplos arquivos.

    Exemplo de uso::

        from pathlib import Path
        from src.infrastructure.parsers.news_parser import NewsParser

        parser = NewsParser()
        noticias = parser.parse(Path("boletim.docx"))
        for n in noticias:
            print(f"[{n.indice}] {n.titulo}")
            print(n.corpo)
    """

    def parse(self, file_path: Path) -> List[Noticia]:
        """Lê o documento e retorna uma lista ordenada de notícias.

        Args:
            file_path: Caminho absoluto (ou relativo ao CWD) para o arquivo
                ``.docx``.

        Returns:
            Lista de :class:`Noticia` em ordem de aparecimento no documento.
            Retorna lista vazia se nenhum "Heading 1" for encontrado.

        Raises:
            FileNotFoundError: Se *file_path* não existir no sistema de arquivos.
            ValueError: Se a extensão não for ``.docx`` ou o arquivo estiver
                corrompido / ilegível.
        """
        self._validate(file_path)
        document = self._open_document(file_path)
        return self._extract(document, source_name=file_path.name)

    # ------------------------------------------------------------------
    # Métodos auxiliares (podem ser sobrescritos em subclasses para
    # customizar o comportamento sem alterar o fluxo principal)
    # ------------------------------------------------------------------

    def _validate(self, file_path: Path) -> None:
        """Valida existência e extensão do arquivo.

        Raises:
            FileNotFoundError: Arquivo não encontrado.
            ValueError: Extensão inválida.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
        if file_path.suffix.lower() != ".docx":
            raise ValueError(
                f"Extensão inválida '{file_path.suffix}'. Esperado: .docx"
            )

    def _open_document(self, file_path: Path) -> Document:
        """Abre o arquivo .docx via python-docx.

        Raises:
            ValueError: Se o arquivo não puder ser aberto (corrompido, acesso
                negado, etc.).
        """
        try:
            return docx.Document(str(file_path))
        except Exception as exc:
            raise ValueError(
                f"Não foi possível abrir '{file_path}': {exc}"
            ) from exc

    def _extract(self, document: Document, source_name: str) -> List[Noticia]:
        """Percorre os elementos do documento e agrupa por notícia.

        Args:
            document: Documento Word já aberto.
            source_name: Nome do arquivo de origem (para preencher
                :attr:`Noticia.arquivo_origem`).

        Returns:
            Lista de :class:`Noticia`.
        """
        noticias: List[Noticia] = []
        current_title: str | None = None
        body_parts: List[str] = []
        index = 0

        def flush() -> None:
            """Finaliza a notícia corrente e a adiciona à lista."""
            nonlocal index, current_title, body_parts
            if current_title is None:
                return
            index += 1
            corpo = "\n\n".join(part for part in body_parts if part)
            noticias.append(
                Noticia(
                    titulo=current_title,
                    corpo=corpo,
                    arquivo_origem=source_name,
                    indice=index,
                )
            )
            current_title = None
            body_parts = []

        for block in _iter_block_items(document):
            if isinstance(block, Paragraph):
                if _is_heading1(block):
                    # Finaliza a notícia anterior (se houver) antes de abrir a nova.
                    flush()
                    title_text = _clean_text(block)
                    if not title_text:
                        logger.warning(
                            "Heading 1 vazio encontrado em '%s' — ignorado.",
                            source_name,
                        )
                    else:
                        current_title = title_text
                else:
                    # Parágrafo de corpo: só processa se já tivermos um título aberto.
                    if current_title is not None:
                        text = _clean_text(block)
                        if text:
                            body_parts.append(text)

            elif isinstance(block, Table):
                # Tabela: inclui no corpo da notícia corrente, se houver.
                if current_title is not None:
                    table_text = _table_to_text(block)
                    if table_text.strip():
                        body_parts.append(table_text)

        # Salva a última notícia ainda aberta.
        flush()

        if not noticias:
            logger.warning(
                "Nenhuma notícia encontrada em '%s'. "
                "Verifique se o documento possui parágrafos com estilo 'Heading 1'.",
                source_name,
            )
        else:
            logger.info(
                "%d notícia(s) extraída(s) de '%s'.",
                len(noticias),
                source_name,
            )

        return noticias
