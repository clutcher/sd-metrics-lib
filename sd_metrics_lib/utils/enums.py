from enum import auto, Enum


class VelocityTimeUnit(Enum):
    SECOND = auto()
    HOUR = auto()
    DAY = auto()
    WEEK = auto()
    MONTH = auto()


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
