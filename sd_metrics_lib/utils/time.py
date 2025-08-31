from sd_metrics_lib.utils.enums import VelocityTimeUnit

SECONDS_IN_HOUR = 3600
WORKING_HOURS_PER_DAY = 8
WORKING_DAYS_PER_WEEK = 5
WORKING_WEEKS_IN_MONTH = 4

# Python's date.weekday(): Monday=0
WEEKDAY_FRIDAY = 4


def get_seconds_in_day(hours_in_one_day: int = WORKING_HOURS_PER_DAY) -> int:
    return hours_in_one_day * SECONDS_IN_HOUR


def convert_time(
        time_in_seconds: int,
        time_unit: VelocityTimeUnit,
        hours_in_one_day: int = WORKING_HOURS_PER_DAY,
        days_in_one_week: int = WORKING_DAYS_PER_WEEK,
        weeks_in_one_month: int = WORKING_WEEKS_IN_MONTH
) -> float:
    if time_in_seconds is None:
        return 0
    if time_unit == VelocityTimeUnit.SECOND:
        return time_in_seconds
    elif time_unit == VelocityTimeUnit.HOUR:
        return time_in_seconds / SECONDS_IN_HOUR
    elif time_unit == VelocityTimeUnit.DAY:
        return time_in_seconds / SECONDS_IN_HOUR / hours_in_one_day
    elif time_unit == VelocityTimeUnit.WEEK:
        return time_in_seconds / SECONDS_IN_HOUR / hours_in_one_day / days_in_one_week
    elif time_unit == VelocityTimeUnit.MONTH:
        return time_in_seconds / SECONDS_IN_HOUR / hours_in_one_day / days_in_one_week / weeks_in_one_month
    return 0
