from abc import ABC, abstractmethod


class MetricCalculator(ABC):

    @abstractmethod
    def calculate(self):
        pass
