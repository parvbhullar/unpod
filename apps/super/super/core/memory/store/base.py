from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List


class BaseStore(ABC):
    @abstractmethod
    def add(self, docs: List[Any], ttl: Optional[int] = None) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def delete(self, key: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def search(self, query: str) -> List[Dict[str, Any]]:
        pass
