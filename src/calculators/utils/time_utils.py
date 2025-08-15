from common import (
    VelocityTimeUnit,
    SECONDS_IN_HOUR,
    WORKING_HOURS_PER_DAY,
    WORKING_DAYS_PER_WEEK,
    WORKING_WEEKS_IN_MONTH,
)


def convert_time(spent_time_in_seconds: int, time_unit: VelocityTimeUnit):
    if spent_time_in_seconds is None:
        return 0
    if time_unit == VelocityTimeUnit.HOUR:
        return spent_time_in_seconds / SECONDS_IN_HOUR
    elif time_unit == VelocityTimeUnit.DAY:
        return spent_time_in_seconds / SECONDS_IN_HOUR / WORKING_HOURS_PER_DAY
    elif time_unit == VelocityTimeUnit.WEEK:
        return spent_time_in_seconds / SECONDS_IN_HOUR / WORKING_HOURS_PER_DAY / WORKING_DAYS_PER_WEEK
    elif time_unit == VelocityTimeUnit.MONTH:
        return spent_time_in_seconds / SECONDS_IN_HOUR / WORKING_HOURS_PER_DAY / WORKING_DAYS_PER_WEEK / WORKING_WEEKS_IN_MONTH
    else:
        return spent_time_in_seconds


