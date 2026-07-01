"""Interface abstrata do repositório de notícias."""
from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.entities.news import News, NewsStatus


class INewsRepository(ABC):
    """Contrato para persistência de notícias.

    Implementações concretas ficam na camada de infraestrutura.
    """

    @abstractmethod
    def save(self, news: News) -> News:
        """Persiste uma nova notícia e a retorna com os dados gerados."""
        ...

    @abstractmethod
    def find_by_id(self, news_id: str) -> Optional[News]:
        """Recupera uma notícia pelo seu identificador único."""
        ...

    @abstractmethod
    def find_all(self) -> List[News]:
        """Retorna todas as notícias armazenadas."""
        ...

    @abstractmethod
    def find_by_status(self, status: NewsStatus) -> List[News]:
        """Retorna notícias filtradas por status."""
        ...

    @abstractmethod
    def update(self, news: News) -> News:
        """Atualiza os dados de uma notícia existente."""
        ...

    @abstractmethod
    def delete(self, news_id: str) -> None:
        """Remove uma notícia pelo identificador."""
        ...
