import datetime
from abc import ABC, abstractmethod

from sd_metrics_lib.utils.time import Duration, TimeUnit, TimePolicy


class WorkTimeExtractor(ABC):

    @abstractmethod
    def extract_time_from_period(self,
                                 start_time_period: datetime.date | datetime.datetime,
                                 end_time_period: datetime.date | datetime.datetime,
                                 time_policy: TimePolicy = TimePolicy.BUSINESS_HOURS,
                                 result_unit: TimeUnit = TimeUnit.SECOND) -> Duration | None:
        pass


class SimpleWorkTimeExtractor(WorkTimeExtractor):

    def extract_time_from_period(self,
                                 start_time_period: datetime.date | datetime.datetime,
                                 end_time_period: datetime.date | datetime.datetime,
                                 time_policy: TimePolicy = TimePolicy.BUSINESS_HOURS,
                                 result_unit: TimeUnit = TimeUnit.SECOND) -> Duration | None:
        if end_time_period <= start_time_period:
            return None

        calendar_elapsed_seconds = Duration.datetime_difference(start_time_period, end_time_period, TimeUnit.SECOND)

        minimum_trackable_duration_seconds = Duration.of(0.25, TimeUnit.HOUR).convert(TimeUnit.SECOND)
        if calendar_elapsed_seconds < minimum_trackable_duration_seconds:
            return None

        if time_policy == TimePolicy.ALL_HOURS:
            return calendar_elapsed_seconds.convert(result_unit, TimePolicy.ALL_HOURS)

        business_candidate_duration_seconds = calendar_elapsed_seconds

        multi_day_span_in_calendar_days = business_candidate_duration_seconds.convert(TimeUnit.DAY, TimePolicy.ALL_HOURS)
        if multi_day_span_in_calendar_days.time_delta >= 1.0:
            working_days_count = self.__count_work_days_policy_aware(start_time_period, end_time_period, time_policy)
            rounded_up_calendar_days = int(multi_day_span_in_calendar_days.time_delta) + 1
            capped_business_seconds = Duration.of(min(working_days_count, rounded_up_calendar_days), TimeUnit.DAY).convert(TimeUnit.SECOND, time_policy)
            return capped_business_seconds.convert(result_unit, time_policy)

        one_business_day_seconds = Duration.of(1, TimeUnit.DAY).convert(TimeUnit.SECOND, time_policy)
        if business_candidate_duration_seconds.time_delta < one_business_day_seconds.time_delta:
            return business_candidate_duration_seconds.convert(result_unit, time_policy)
        return one_business_day_seconds.convert(result_unit, time_policy)

    @staticmethod
    def __count_work_days_policy_aware(start_date: datetime.date, end_date: datetime.date, policy: TimePolicy) -> int:
        working_days_per_week_as_int = int(policy.days_per_week)
        if working_days_per_week_as_int <= 0:
            return 0
        last_workday_weekday_index = working_days_per_week_as_int - 1

        if start_date.weekday() > last_workday_weekday_index:
            start_date = start_date + datetime.timedelta(days=(7 - start_date.weekday()))
        if end_date.weekday() > last_workday_weekday_index:
            end_date = end_date - datetime.timedelta(days=(end_date.weekday() - last_workday_weekday_index))

        if start_date > end_date:
            return 0

        inclusive_span_days = (end_date - start_date).days + 1
        full_weeks_in_span = inclusive_span_days // 7
        trailing_days_beyond_full_weeks = inclusive_span_days % 7

        working_days = full_weeks_in_span * working_days_per_week_as_int
        start_weekday_index = start_date.weekday()
        for day_offset in range(trailing_days_beyond_full_weeks):
            if (start_weekday_index + day_offset) % 7 <= last_workday_weekday_index:
                working_days += 1
        return working_days

SIMPLE_WORKTIME_EXTRACTOR = SimpleWorkTimeExtractor()

class BoundarySimpleWorkTimeExtractor(SimpleWorkTimeExtractor):

    def __init__(self,
                 start_time_boundary: datetime.date,
                 end_time_boundary: datetime.date) -> None:
        self.start_time_boundary = start_time_boundary
        self.end_time_boundary = end_time_boundary

    def extract_time_from_period(self,
                                 start_time_period: datetime.date | datetime.datetime,
                                 end_time_period: datetime.date | datetime.datetime,
                                 time_policy: TimePolicy = TimePolicy.BUSINESS_HOURS,
                                 result_unit: TimeUnit = TimeUnit.SECOND) -> Duration | None:

        if self.start_time_boundary < start_time_period:
            new_start_period = start_time_period
        else:
            new_start_period = self.start_time_boundary

        if self.end_time_boundary > end_time_period:
            new_end_time_period = end_time_period
        else:
            new_end_time_period = self.end_time_boundary

        return super().extract_time_from_period(new_start_period, new_end_time_period, time_policy, result_unit)
