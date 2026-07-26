from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    name = "BaseAgent"

    @abstractmethod
    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError
