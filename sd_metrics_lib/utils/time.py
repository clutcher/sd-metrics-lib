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

    def add(self, other: "Duration", policy: TimePolicy | None = None, unit: TimeUnit | None = None) -> "Duration":
        unit_used = unit or self.time_unit
        policy_used = policy or TimePolicy.ALL_HOURS
        self_value_in_unit = policy_used.convert(self.time_delta, self.time_unit, unit_used)
        other_value_in_unit = policy_used.convert(other.time_delta, other.time_unit, unit_used)
        return Duration.of(self_value_in_unit + other_value_in_unit, unit_used)

    def sub(self, other: "Duration", policy: TimePolicy | None = None, unit: TimeUnit | None = None) -> "Duration":
        unit_used = unit or self.time_unit
        policy_used = policy or TimePolicy.ALL_HOURS
        self_value_in_unit = policy_used.convert(self.time_delta, self.time_unit, unit_used)
        other_value_in_unit = policy_used.convert(other.time_delta, other.time_unit, unit_used)
        return Duration.of(self_value_in_unit - other_value_in_unit, unit_used)

    @staticmethod
    def _coerce_value_in_unit(other: object, target_unit: TimeUnit,
                              time_policy: TimePolicy | None = None) -> float | None:
        if isinstance(other, Duration):
            effective_policy = time_policy or TimePolicy.ALL_HOURS
            return effective_policy.convert(other.time_delta, other.time_unit, target_unit)
        if isinstance(other, (int, float)):
            return float(other)
        return None

    def __add__(self, other: object) -> "Duration":
        coerced_value = self._coerce_value_in_unit(other, self.time_unit)
        if coerced_value is None:
            return NotImplemented
        return Duration.of(self.time_delta + coerced_value, self.time_unit)

    def __radd__(self, other: object) -> "Duration":
        coerced_value = self._coerce_value_in_unit(other, self.time_unit)
        if coerced_value is None:
            return NotImplemented
        return Duration.of(coerced_value + self.time_delta, self.time_unit)

    def __sub__(self, other: object) -> "Duration":
        coerced_value = self._coerce_value_in_unit(other, self.time_unit)
        if coerced_value is None:
            return NotImplemented
        return Duration.of(self.time_delta - coerced_value, self.time_unit)

    def __rsub__(self, other: object) -> "Duration":
        coerced_value = self._coerce_value_in_unit(other, self.time_unit)
        if coerced_value is None:
            return NotImplemented
        return Duration.of(coerced_value - self.time_delta, self.time_unit)

    def __iadd__(self, other: object) -> "Duration":
        coerced_value = self._coerce_value_in_unit(other, self.time_unit)
        if coerced_value is None:
            return NotImplemented  # type: ignore[return-value]
        return Duration.of(self.time_delta + coerced_value, self.time_unit)

    def __isub__(self, other: object) -> "Duration":
        coerced_value = self._coerce_value_in_unit(other, self.time_unit)
        if coerced_value is None:
            return NotImplemented  # type: ignore[return-value]
        return Duration.of(self.time_delta - coerced_value, self.time_unit)

    def __mul__(self, multiplier: SupportsFloat) -> "Duration":
        return Duration.of(float(self.time_delta) * float(multiplier), self.time_unit)

    def __rmul__(self, multiplier: SupportsFloat) -> "Duration":
        return Duration.of(float(multiplier) * float(self.time_delta), self.time_unit)

    def __truediv__(self, other: object):
        if isinstance(other, (int, float)):
            return Duration.of(float(self.time_delta) / float(other), self.time_unit)
        if isinstance(other, Duration):
            denominator_value = self._coerce_value_in_unit(other, self.time_unit)
            if denominator_value is None:
                return NotImplemented
            return float(self.time_delta) / float(denominator_value)
        return NotImplemented

    def _cmp_seconds(self, other: object) -> float | None:
        if isinstance(other, Duration):
            self_seconds = self.to_seconds(TimePolicy.ALL_HOURS)
            other_seconds = other.to_seconds(TimePolicy.ALL_HOURS)
            return self_seconds - other_seconds
        if isinstance(other, (int, float)):
            self_value = self.time_delta
            other_value = float(other)
            return self_value - other_value
        return None

    def __eq__(self, other: object) -> bool:
        comparison_diff = self._cmp_seconds(other)
        if comparison_diff is None:
            return NotImplemented
        return comparison_diff == 0

    def __lt__(self, other: object) -> bool:
        comparison_diff = self._cmp_seconds(other)
        if comparison_diff is None:
            return NotImplemented
        return comparison_diff < 0

    def __le__(self, other: object) -> bool:
        comparison_diff = self._cmp_seconds(other)
        if comparison_diff is None:
            return NotImplemented
        return comparison_diff <= 0

    def __gt__(self, other: object) -> bool:
        comparison_diff = self._cmp_seconds(other)
        if comparison_diff is None:
            return NotImplemented
        return comparison_diff > 0

    def __ge__(self, other: object) -> bool:
        comparison_diff = self._cmp_seconds(other)
        if comparison_diff is None:
            return NotImplemented
        return comparison_diff >= 0

    def __bool__(self) -> bool:
        return self.time_delta != 0

    @staticmethod
    def sum(durations: "Iterable[Duration]", policy: TimePolicy | None = None,
            unit: TimeUnit = TimeUnit.SECOND) -> "Duration":
        policy_used = policy or TimePolicy.ALL_HOURS
        total = 0.0
        if durations:
            for duration in durations:
                total += policy_used.convert(duration.time_delta, duration.time_unit, unit)
        return Duration.of(total, unit)
