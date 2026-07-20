"""Parser de documentos Word (.docx) para extração de notícias.

Estratégia de detecção — baseada em heurísticas
================================================

O parser percorre todos os parágrafos e identifica títulos de notícias
sem depender dos estilos Word (Heading 1, etc.).  As regras aplicadas são:

1. **Ignorar capa**
   Tudo que aparece antes do primeiro marcador de bloco
   ("1º BLOCO", "2º BLOCO" etc.) é descartado como conteúdo de capa.
   Se o documento não contiver nenhum marcador de bloco, nenhum conteúdo
   é descartado (o documento inteiro é processado).

2. **Ignorar linhas vazias**
   Parágrafos cujo texto seja vazio (ou apenas espaços em branco) são
   ignorados tanto na detecção de títulos quanto no corpo das notícias.

3. **Ignorar marcadores de bloco**
   Parágrafos que correspondam ao padrão ``Nº BLOCO`` (ex.:
   ``"1º BLOCO – EVOLUÇÃO"``, ``"2º BLOCO -  FASTBRAILLE"``) são
   descartados e marcam o fim da capa.

4. **Ignorar títulos de seção curtos**
   Parágrafos em caixa alta com menos de :data:`_MIN_TITLE_WORDS` palavras
   são tratados como títulos de seção e **não** iniciam uma nova notícia.
   Eles são incluídos no corpo da notícia corrente (se houver).

5. **Detectar título de notícia**
   Um parágrafo é considerado título quando:

   * Todos os seus caracteres alfabéticos são maiúsculos (caixa alta).
   * Possui pelo menos :data:`_MIN_TITLE_WORDS` palavras.
   * Não corresponde ao padrão de marcador de bloco.

6. **Corpo da notícia**
   Todo parágrafo (não vazio, não marcador de bloco) que surge após um
   título pertence ao corpo daquela notícia, até que outro título seja
   encontrado ou o documento se encerre.

7. **Tabelas**
   Tabelas encontradas após um título são convertidas para texto plano e
   incluídas no corpo.  Células da mesma linha são separadas por ``\t``;
   linhas, por ``\n``.

8. **Posição**
   Cada notícia registra o índice (base 0) do parágrafo de título na
   sequência de blocos do documento (:attr:`Noticia.posicao_inicial`) e o
   índice do último bloco de conteúdo pertencente a ela
   (:attr:`Noticia.posicao_final`).

Comportamento em caso de desvio das premissas
---------------------------------------------
- **Nenhum título detectado** → retorna lista vazia e emite aviso no log.
- **Arquivo inexistente** → ``FileNotFoundError``.
- **Extensão diferente de .docx** → ``ValueError``.
- **Arquivo corrompido / ilegível** → ``ValueError``.
"""

from __future__ import annotations

import logging
import re
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

#: Padrão que identifica marcadores de bloco: "1º BLOCO", "2º BLOCO", etc.
_BLOCO_RE = re.compile(r"^\d+[ºª°]\s*BLOCO", re.IGNORECASE)

#: Número mínimo de palavras para que um parágrafo em caixa alta seja
#: considerado um título de notícia (e não um título de seção).
_MIN_TITLE_WORDS: int = 5

#: Tags XML qualificadas usadas na iteração do body do documento.
_TAG_PARAGRAPH = qn("w:p")
_TAG_TABLE = qn("w:tbl")


# ---------------------------------------------------------------------------
# Dataclass de domínio do parser
# ---------------------------------------------------------------------------


@dataclass
class Noticia:
    """Representa uma notícia extraída de um documento Word.

    Atributos:
        titulo: Texto do parágrafo de título (caixa alta, >= 5 palavras).
        corpo: Texto concatenado dos parágrafos que formam o corpo da notícia.
            Blocos separados por ``\n\n``.  Pode ser vazio.
        arquivo_origem: Nome do arquivo ``.docx`` de origem (sem caminho).
        indice: Posição ordinal da notícia no documento, base 1.
        posicao_inicial: Índice (base 0) do bloco de título na sequência de
            blocos do documento.
        posicao_final: Índice (base 0) do último bloco de conteúdo da
            notícia na sequência de blocos do documento.
    """

    titulo: str
    corpo: str
    arquivo_origem: str
    indice: int = field(default=0)
    posicao_inicial: int = field(default=0)
    posicao_final: int = field(default=0)


# ---------------------------------------------------------------------------
# Helpers privados
# ---------------------------------------------------------------------------


def _is_bloco_marker(text: str) -> bool:
    """Retorna True se *text* for um marcador de bloco (``Nº BLOCO …``)."""
    return bool(_BLOCO_RE.match(text))


def _is_all_upper(text: str) -> bool:
    """Retorna True se todos os caracteres alfabéticos de *text* forem maiúsculos."""
    letters = [c for c in text if c.isalpha()]
    return len(letters) > 0 and all(c.isupper() for c in letters)


def _is_title_candidate(text: str) -> bool:
    """Retorna True se *text* satisfizer as heurísticas de título de notícia.

    Um texto é candidato a título quando:
    * Não é vazio.
    * Não é marcador de bloco.
    * Todos os seus caracteres alfabéticos são maiúsculos (caixa alta).
    * Possui pelo menos :data:`_MIN_TITLE_WORDS` palavras.
    """
    if not text:
        return False
    if _is_bloco_marker(text):
        return False
    if not _is_all_upper(text):
        return False
    return len(text.split()) >= _MIN_TITLE_WORDS


def _table_to_text(table: Table) -> str:
    """Converte uma tabela Word em texto plano.

    Células da mesma linha são separadas por ``\t``; linhas, por ``\n``.
    Linhas completamente vazias são omitidas.
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
    """Itera os elementos de bloco do documento na ordem de aparecimento.

    Percorre diretamente o XML do ``<w:body>`` para preservar a ordem
    relativa entre parágrafos e tabelas.

    Yields:
        Instâncias de Paragraph ou Table.
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
    """Extrai notícias de documentos Word (.docx) usando heurísticas.

    Nao depende de estilos Word.  A detecção de títulos é feita com base
    no texto em caixa alta e no número de palavras.

    A mesma instância pode ser reutilizada para múltiplos arquivos.

    Exemplo de uso::

        from pathlib import Path
        from src.infrastructure.parsers.news_parser import NewsParser

        parser = NewsParser()
        noticias = parser.parse(Path("boletim.docx"))
        for n in noticias:
            print(f"[{n.indice}] {n.titulo} (paras {n.posicao_inicial}–{n.posicao_final})")
    """

    def parse(self, file_path: Path) -> List[Noticia]:
        """Lê o documento e retorna uma lista ordenada de notícias.

        Args:
            file_path: Caminho para o arquivo ``.docx``.

        Returns:
            Lista de Noticia em ordem de aparecimento no documento.
            Retorna lista vazia se nenhum título for detectado.

        Raises:
            FileNotFoundError: Se *file_path* não existir.
            ValueError: Se a extensão não for ``.docx`` ou o arquivo estiver
                corrompido / ilegível.
        """
        self._validate(file_path)
        document = self._open_document(file_path)
        return self._extract(document, source_name=file_path.name)

    # ------------------------------------------------------------------
    # Métodos auxiliares
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
            ValueError: Se o arquivo não puder ser aberto.
        """
        try:
            return docx.Document(str(file_path))
        except Exception as exc:
            raise ValueError(
                f"Não foi possível abrir '{file_path}': {exc}"
            ) from exc

    def _extract(self, document: Document, source_name: str) -> List[Noticia]:
        """Percorre os blocos do documento e agrupa por notícia.

        Aplica as heurísticas para detectar títulos e delimitar o corpo de
        cada notícia.

        A capa (tudo antes do primeiro marcador de bloco) é ignorada quando
        o documento contém pelo menos um marcador de bloco.  Documentos sem
        marcador de bloco são processados integralmente.

        Args:
            document: Documento Word já aberto.
            source_name: Nome do arquivo de origem.

        Returns:
            Lista de Noticia.
        """
        items: list[Union[Paragraph, Table]] = list(_iter_block_items(document))

        # Se o documento tem marcador de bloco, o início é considerado capa.
        has_bloco = any(
            isinstance(item, Paragraph) and _is_bloco_marker(item.text.strip())
            for item in items
        )
        past_cover: bool = not has_bloco

        noticias: List[Noticia] = []
        current_title: str | None = None
        current_start: int = 0
        last_pos: int = 0
        body_parts: List[str] = []
        index: int = 0

        def flush(end_pos: int) -> None:
            """Fecha a notícia corrente e a adiciona à lista."""
            nonlocal index, current_title, body_parts, current_start
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
                    posicao_inicial=current_start,
                    posicao_final=end_pos,
                )
            )
            current_title = None
            body_parts = []

        for pos, block in enumerate(items):
            if isinstance(block, Paragraph):
                text = block.text.strip()

                # Ignora linhas vazias.
                if not text:
                    continue

                # Marcador de bloco: sinaliza fim da capa e é descartado.
                if _is_bloco_marker(text):
                    past_cover = True
                    continue

                # Enquanto na capa, descarta tudo.
                if not past_cover:
                    continue

                if _is_title_candidate(text):
                    # Novo título: fecha a notícia anterior (se houver).
                    flush(last_pos)
                    current_title = text
                    current_start = pos
                    last_pos = pos
                elif current_title is not None:
                    # Parágrafo de corpo.
                    body_parts.append(text)
                    last_pos = pos

            elif isinstance(block, Table):
                if current_title is not None and past_cover:
                    table_text = _table_to_text(block)
                    if table_text.strip():
                        body_parts.append(table_text)
                        last_pos = pos

        # Salva a última notícia ainda aberta.
        flush(last_pos)

        if not noticias:
            logger.warning(
                "Nenhuma notícia encontrada em '%s'. "
                "Verifique se o documento contém títulos em caixa alta com "
                "pelo menos %d palavras.",
                source_name,
                _MIN_TITLE_WORDS,
            )
        else:
            logger.info(
                "%d notícia(s) extraída(s) de '%s'.",
                len(noticias),
                source_name,
            )

        return noticias
