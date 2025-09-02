from dataclasses import dataclass
from datetime import datetime

from enum import Enum, auto
from typing import Iterable, ClassVar, SupportsFloat


class TimeUnit(Enum):
    SECOND = auto()
    HOUR = auto()
    DAY = auto()
    WEEK = auto()
    MONTH = auto()


SECONDS_IN_HOUR = 3600
WORKING_HOURS_PER_DAY = 8
WORKING_DAYS_PER_WEEK = 5
WORKING_WEEKS_IN_MONTH = 4

# Python's date.weekday(): Monday=0
WEEKDAY_FRIDAY = 4


@dataclass(frozen=True, slots=True)
class TimePolicy:
    hours_per_day: float
    days_per_week: float
    days_per_month: float

    ALL_HOURS: ClassVar["TimePolicy"]  # 24/7 wall-clock (aka civil)
    BUSINESS_HOURS: ClassVar["TimePolicy"]  # working capacity (e.g., 8h/day, 5d/week)

    def factor_to_day(self, unit: TimeUnit) -> float:
        if unit == TimeUnit.SECOND:
            return 1.0 / (SECONDS_IN_HOUR * self.hours_per_day)
        if unit == TimeUnit.HOUR:
            return 1.0 / self.hours_per_day
        if unit == TimeUnit.DAY:
            return 1.0
        if unit == TimeUnit.WEEK:
            return self.days_per_week
        if unit == TimeUnit.MONTH:
            return self.days_per_month
        return 1.0

    def factor_from_day(self, unit: TimeUnit) -> float:
        if unit == TimeUnit.SECOND:
            return SECONDS_IN_HOUR * self.hours_per_day
        if unit == TimeUnit.HOUR:
            return self.hours_per_day
        if unit == TimeUnit.DAY:
            return 1.0
        if unit == TimeUnit.WEEK:
            return 1.0 / self.days_per_week
        if unit == TimeUnit.MONTH:
            return 1.0 / self.days_per_month
        return 1.0

    def convert(self, value: float, from_unit: TimeUnit, to_unit: TimeUnit) -> float:
        if from_unit == to_unit:
            return float(value)
        return float(value) * self.factor_to_day(from_unit) * self.factor_from_day(to_unit)


TimePolicy.ALL_HOURS = TimePolicy(
    hours_per_day=24,
    days_per_week=7,
    days_per_month=30,
)

TimePolicy.BUSINESS_HOURS = TimePolicy(
    hours_per_day=WORKING_HOURS_PER_DAY,
    days_per_week=WORKING_DAYS_PER_WEEK,
    days_per_month=WORKING_DAYS_PER_WEEK * WORKING_WEEKS_IN_MONTH,
)


@dataclass(frozen=True, slots=True)
class Duration:
    time_delta: float
    time_unit: TimeUnit

    @classmethod
    def zero(cls, unit: TimeUnit = TimeUnit.SECOND) -> "Duration":
        return cls(0.0, unit)

    @classmethod
    def of(cls, time_delta: SupportsFloat, time_unit: TimeUnit) -> "Duration":
        return cls(float(time_delta), time_unit)

    @classmethod
    def difference(cls,
                   start_value: SupportsFloat,
                   end_value: SupportsFloat,
                   time_unit: TimeUnit) -> "Duration":
        return cls(float(end_value) - float(start_value), time_unit)

    @classmethod
    def datetime_difference(
            cls,
            start: datetime,
            end: datetime,
            time_unit: TimeUnit,
            time_policy: TimePolicy | None = None,
    ) -> "Duration":
        policy = time_policy or TimePolicy.ALL_HOURS
        delta_seconds = float((end - start).total_seconds())
        value_in_unit = policy.convert(delta_seconds, TimeUnit.SECOND, time_unit)
        return cls(value_in_unit, time_unit)

    def to_seconds(self, time_policy: TimePolicy | None = None) -> float:
        policy = time_policy or TimePolicy.ALL_HOURS
        return policy.convert(self.time_delta, self.time_unit, TimeUnit.SECOND)

    def convert(self, target_unit: TimeUnit, time_policy: TimePolicy | None = None) -> "Duration":
        policy = time_policy or TimePolicy.ALL_HOURS
        new_value = policy.convert(self.time_delta, self.time_unit, target_unit)
        return Duration(new_value, target_unit)

    def is_zero(self, eps: float = 0.0, time_policy: TimePolicy | None = None) -> bool:
        if eps <= 0:
            return self.time_delta == 0
        return abs(self.to_seconds(time_policy)) <= eps

    # Arithmetic helpers
    def add(self, other: "Duration", policy: TimePolicy | None = None, unit: TimeUnit | None = None) -> "Duration":
        unit_used = unit or self.time_unit
        policy_used = policy or TimePolicy.ALL_HOURS
        a = policy_used.convert(self.time_delta, self.time_unit, unit_used)
        b = policy_used.convert(other.time_delta, other.time_unit, unit_used)
        return Duration.of(a + b, unit_used)

    def sub(self, other: "Duration", policy: TimePolicy | None = None, unit: TimeUnit | None = None) -> "Duration":
        unit_used = unit or self.time_unit
        policy_used = policy or TimePolicy.ALL_HOURS
        a = policy_used.convert(self.time_delta, self.time_unit, unit_used)
        b = policy_used.convert(other.time_delta, other.time_unit, unit_used)
        return Duration.of(a - b, unit_used)

    def __add__(self, other: "Duration") -> "Duration":
        return self.add(other)

    def __sub__(self, other: "Duration") -> "Duration":
        return self.sub(other)

    def __iadd__(self, other: "Duration") -> "Duration":
        return self.add(other)

    def __isub__(self, other: "Duration") -> "Duration":
        return self.sub(other)

    def __mul__(self, k: SupportsFloat) -> "Duration":
        return Duration.of(float(self.time_delta) * float(k), self.time_unit)

    def __truediv__(self, k: SupportsFloat) -> "Duration":
        return Duration.of(float(self.time_delta) / float(k), self.time_unit)

    def __bool__(self) -> bool:
        # treat exact zero as False
        return self.time_delta != 0

    # Ordering comparisons compare using ALL_HOURS policy
    def _cmp_seconds(self, other: "Duration") -> float | None:
        if not isinstance(other, Duration):
            return None
        a = self.to_seconds(TimePolicy.ALL_HOURS)
        b = other.to_seconds(TimePolicy.ALL_HOURS)
        return a - b

    def __lt__(self, other: object) -> bool:
        diff = self._cmp_seconds(other) if isinstance(other, Duration) else None
        if diff is None:
            return NotImplemented
        return diff < 0

    def __le__(self, other: object) -> bool:
        diff = self._cmp_seconds(other) if isinstance(other, Duration) else None
        if diff is None:
            return NotImplemented
        return diff <= 0

    def __gt__(self, other: object) -> bool:
        diff = self._cmp_seconds(other) if isinstance(other, Duration) else None
        if diff is None:
            return NotImplemented
        return diff > 0

    def __ge__(self, other: object) -> bool:
        diff = self._cmp_seconds(other) if isinstance(other, Duration) else None
        if diff is None:
            return NotImplemented
        return diff >= 0

    @staticmethod
    def sum(durations: "Iterable[Duration]", policy: TimePolicy | None = None,
            unit: TimeUnit = TimeUnit.SECOND) -> "Duration":
        policy_used = policy or TimePolicy.ALL_HOURS
        total = 0.0
        if durations:
            for d in durations:
                total += policy_used.convert(d.time_delta, d.time_unit, unit)
        return Duration.of(total, unit)
