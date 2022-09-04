from abc import ABC, abstractmethod
from typing import Dict


class MetricCalculator(ABC):

    @abstractmethod
    def calculate(self) -> Dict[str, float]:
        pass
