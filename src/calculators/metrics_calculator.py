from abc import ABC, abstractmethod
from typing import Dict


class MetricCalculator(ABC):

    @abstractmethod
    def calculate(self):
        pass
