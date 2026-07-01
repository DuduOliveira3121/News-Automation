"""Interface abstrata do repositório de publicações."""
from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.entities.publication import Publication, PublicationStatus


class IPublicationRepository(ABC):
    """Contrato para persistência de publicações."""

    @abstractmethod
    def save(self, publication: Publication) -> Publication:
        """Persiste um novo registro de publicação."""
        ...

    @abstractmethod
    def find_by_id(self, publication_id: str) -> Optional[Publication]:
        """Recupera uma publicação pelo identificador."""
        ...

    @abstractmethod
    def find_by_news_id(self, news_id: str) -> List[Publication]:
        """Retorna todas as publicações associadas a uma notícia."""
        ...

    @abstractmethod
    def find_by_status(self, status: PublicationStatus) -> List[Publication]:
        """Retorna publicações filtradas por status."""
        ...

    @abstractmethod
    def update(self, publication: Publication) -> Publication:
        """Atualiza um registro de publicação existente."""
        ...
