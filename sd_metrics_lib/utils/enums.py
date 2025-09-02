from enum import auto, Enum

class HealthStatus(Enum):
    GREEN = auto()
    YELLOW = auto()
    ORANGE = auto()
    RED = auto()
    GRAY = auto()


class SeniorityLevel(Enum):
    JUNIOR = auto()
    MIDDLE = auto()
    SENIOR = auto()
