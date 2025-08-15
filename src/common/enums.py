from enum import auto, Enum


class VelocityTimeUnit(Enum):
    HOUR = auto()
    DAY = auto()
    WEEK = auto()
    MONTH = auto()


class HealthStatus(Enum):
    GREEN = auto()
    YELLOW = auto()
    RED = auto()


class SeniorityLevel(Enum):
    JUNIOR = auto()
    MIDDLE = auto()
    SENIOR = auto()
