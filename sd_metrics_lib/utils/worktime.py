import datetime
from abc import ABC, abstractmethod

from sd_metrics_lib.utils.time import WEEKDAY_FRIDAY, Duration, TimeUnit, TimePolicy


class WorkTimeExtractor(ABC):

    @abstractmethod
    def extract_time_from_period(self, start_time_period: datetime.date | datetime.datetime, end_time_period: datetime.date | datetime.datetime) -> Duration | None:
        pass


class SimpleWorkTimeExtractor(WorkTimeExtractor):

    def extract_time_from_period(self,
                                 start_time_period: datetime.date | datetime.datetime,
                                 end_time_period: datetime.date | datetime.datetime) -> Duration | None:
        if end_time_period <= start_time_period:
            return None

        # Compute civil elapsed time only in seconds; derive days when needed via conversion
        period_duration = Duration.datetime_difference(start_time_period, end_time_period, TimeUnit.SECOND)

        # Ignore short periods
        minimal_period_length_limit = Duration.of(0.25, TimeUnit.HOUR).convert(TimeUnit.SECOND)
        if period_duration < minimal_period_length_limit:
            return None

        # Limit multiday periods with week working days and work working hours in a day
        # In other words, a full week period is converted into 5 days with 8 hours in each day
        period_duration_in_days = period_duration.convert(TimeUnit.DAY)
        if period_duration_in_days.time_delta >= 1.0:
            work_days = self.__count_work_days(start_time_period, end_time_period)
            round_up_period_days = int(period_duration_in_days.time_delta) + 1
            return Duration.of(min(work_days, round_up_period_days), TimeUnit.DAY).convert(TimeUnit.SECOND, TimePolicy.BUSINESS_HOURS)

        # Limit 24-hour period with working hours in a single day
        one_business_day = Duration.of(1, TimeUnit.DAY).convert(TimeUnit.SECOND, TimePolicy.BUSINESS_HOURS)
        if period_duration.time_delta < one_business_day.time_delta:
            return period_duration
        return one_business_day

    @staticmethod
    def __count_work_days(start_date: datetime.date, end_date: datetime.date):
        # Move start forward to Monday if it falls on weekend
        if start_date.weekday() > WEEKDAY_FRIDAY:
            start_date = start_date + datetime.timedelta(days=7 - start_date.weekday())
        # Move end backward to Friday if it falls on weekend
        if end_date.weekday() > WEEKDAY_FRIDAY:
            end_date = end_date - datetime.timedelta(days=end_date.weekday() - WEEKDAY_FRIDAY)

        if start_date > end_date:
            return 0

        # Inclusive range
        total_days = (end_date - start_date).days + 1
        full_weeks = total_days // 7
        remainder = total_days % 7

        workdays = full_weeks * 5
        start_wd = start_date.weekday()
        for i in range(remainder):
            if (start_wd + i) % 7 <= WEEKDAY_FRIDAY:
                workdays += 1
        return workdays


class BoundarySimpleWorkTimeExtractor(SimpleWorkTimeExtractor):

    def __init__(self,
                 start_time_boundary: datetime.date,
                 end_time_boundary: datetime.date) -> None:
        self.start_time_boundary = start_time_boundary
        self.end_time_boundary = end_time_boundary

    def extract_time_from_period(self, start_time_period: datetime.date | datetime.datetime, end_time_period: datetime.date | datetime.datetime) -> Duration | None:

        if self.start_time_boundary < start_time_period:
            new_start_period = start_time_period
        else:
            new_start_period = self.start_time_boundary

        if self.end_time_boundary > end_time_period:
            new_end_time_period = end_time_period
        else:
            new_end_time_period = self.end_time_boundary

        return super().extract_time_from_period(new_start_period, new_end_time_period)
