from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class IntegrationConfig:
    name: str
    enabled: bool = False
    config: Dict = None

    def __post_init__(self):
        if self.config is None:
            self.config = {}


class IntegrationBase(ABC):
    """Base class for all integrations (Excel, Calendar, Drive, etc.)."""

    name: str = ""
    version: str = "1.0.0"

    @abstractmethod
    def connect(self) -> bool:
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def sync(self, direction: str = "both") -> Dict:
        """Sync data. direction: 'import', 'export', 'both'."""
        pass

    def test_connection(self) -> bool:
        try:
            return self.connect()
        except Exception:
            return False
