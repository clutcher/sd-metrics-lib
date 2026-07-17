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

        weekday_calendar_hours = self._weekday_calendar_hours(start_time_period, end_time_period, time_policy)
        business_effort = self._ramp_then_plateau_effort(weekday_calendar_hours, time_policy)
        return business_effort.convert(result_unit, time_policy)

    @staticmethod
    def _ramp_then_plateau_effort(weekday_calendar_hours: Duration, time_policy: TimePolicy) -> Duration:
        calendar_days = weekday_calendar_hours.convert(TimeUnit.DAY, TimePolicy.ALL_HOURS)
        full_days = Duration.of(int(calendar_days.time_delta), TimeUnit.DAY)

        partial_calendar_hours = weekday_calendar_hours.sub(full_days, TimePolicy.ALL_HOURS, TimeUnit.HOUR)
        one_business_day_hours = Duration.of(1, TimeUnit.DAY).convert(TimeUnit.HOUR, time_policy)
        ramp_effort = min(partial_calendar_hours, one_business_day_hours)

        return full_days.add(ramp_effort, time_policy, TimeUnit.HOUR)

    @staticmethod
    def _weekday_calendar_hours(start_time_period: datetime.date | datetime.datetime,
                                end_time_period: datetime.date | datetime.datetime,
                                time_policy: TimePolicy) -> Duration:
        last_workday_weekday_index = int(time_policy.days_per_week) - 1
        if last_workday_weekday_index < 0:
            return Duration.zero(TimeUnit.HOUR)

        weekday_calendar_hours = Duration.zero(TimeUnit.HOUR)
        segment_start = SimpleWorkTimeExtractor._as_datetime(start_time_period)
        end_moment = SimpleWorkTimeExtractor._as_datetime(end_time_period)
        while segment_start < end_moment:
            segment_end = min(SimpleWorkTimeExtractor._next_midnight(segment_start), end_moment)
            if segment_start.weekday() <= last_workday_weekday_index:
                segment_hours = Duration.datetime_difference(segment_start, segment_end, TimeUnit.HOUR)
                weekday_calendar_hours = weekday_calendar_hours.add(segment_hours, TimePolicy.ALL_HOURS, TimeUnit.HOUR)
            segment_start = segment_end
        return weekday_calendar_hours

    @staticmethod
    def _as_datetime(moment: datetime.date | datetime.datetime) -> datetime.datetime:
        if isinstance(moment, datetime.datetime):
            return moment
        return datetime.datetime.combine(moment, datetime.time.min)

    @staticmethod
    def _next_midnight(moment: datetime.datetime) -> datetime.datetime:
        next_date = moment.date() + datetime.timedelta(days=1)
        return datetime.datetime.combine(next_date, datetime.time.min, tzinfo=moment.tzinfo)

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
