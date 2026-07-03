"""Interface abstrata do cliente de IA."""
from abc import ABC, abstractmethod


class IAIClient(ABC):
    """Contrato para qualquer cliente de IA usado pela aplicação.

    Implementações concretas ficam na camada de infraestrutura.
    Essa abstração permite trocar o provedor (OpenAI, Gemini, etc.)
    sem alterar os serviços que a consomem.
    """

    @abstractmethod
    def complete(self, system_prompt: str, user_message: str) -> str:
        """Envia um par de mensagens (sistema + usuário) e retorna a resposta.

        Args:
            system_prompt: Instrução de comportamento enviada como role=system.
            user_message: Conteúdo enviado como role=user.

        Returns:
            Texto de resposta gerado pelo modelo.

        Raises:
            RuntimeError: Se a chamada ao provedor falhar.
        """
        ...
