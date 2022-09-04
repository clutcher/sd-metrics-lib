from data_providers.utils import VelocityTimeUnit

SECONDS_IN_HOUR = 3600
WORKING_HOURS_PER_DAY = 8
WORKING_DAYS_PER_WEEK = 5
WORKING_WEEKS_IN_MONTH = 4


def convert_time(spent_time_in_seconds: int, time_unit: VelocityTimeUnit):
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


def get_seconds_in_day():
    return WORKING_HOURS_PER_DAY * SECONDS_IN_HOUR
