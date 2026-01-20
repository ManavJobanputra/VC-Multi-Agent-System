from abc import ABC, abstractmethod
from typing import Dict, List

class BaseAgent(ABC):
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def process(self, data: Dict) -> Dict:
        pass


