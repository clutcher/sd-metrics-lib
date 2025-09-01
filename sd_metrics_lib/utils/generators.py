import calendar
import datetime

from dateutil.relativedelta import relativedelta

from sd_metrics_lib.utils.time import TimeUnit


class TimeRangeGenerator:

    def __init__(self, time_unit: TimeUnit, number_of_ranges: int,
                 start_time_adjuster: datetime.timedelta = None) -> None:
        self.time_unit = time_unit
        self.number_of_ranges = number_of_ranges
        self.period_initial_date = datetime.datetime.today()
        if start_time_adjuster is not None:
            self.period_initial_date += start_time_adjuster

    def __iter__(self):
        for i in range(self.number_of_ranges):
            yield tuple((self.__resolve_start_date_of_period(), self.__resolve_end_date_of_period()))
            self.__decrease_date_range()

    def __decrease_date_range(self):
        if self.time_unit == TimeUnit.HOUR:
            self.period_initial_date -= relativedelta(hours=1)
        elif self.time_unit == TimeUnit.DAY:
            self.period_initial_date -= relativedelta(days=1)
        elif self.time_unit == TimeUnit.WEEK:
            self.period_initial_date -= relativedelta(weeks=1)
        elif self.time_unit == TimeUnit.MONTH:
            self.period_initial_date -= relativedelta(months=1)

    def __resolve_start_date_of_period(self) -> datetime.datetime:
        if self.time_unit == TimeUnit.HOUR:
            return self.period_initial_date.replace(minute=0, second=0, microsecond=0)
        elif self.time_unit == TimeUnit.DAY:
            return self.period_initial_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif self.time_unit == TimeUnit.WEEK:
            current_day_of_week = self.period_initial_date.weekday()
            delta_with_first_day_of_week = datetime.timedelta(days=current_day_of_week)
            return self.period_initial_date - delta_with_first_day_of_week
        elif self.time_unit == TimeUnit.MONTH:
            return self.period_initial_date.replace(day=1)

    def __resolve_end_date_of_period(self):
        if self.time_unit == TimeUnit.HOUR:
            return self.period_initial_date.replace(minute=59, second=59, microsecond=999999)
        elif self.time_unit == TimeUnit.DAY:
            return self.period_initial_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif self.time_unit == TimeUnit.WEEK:
            current_day_of_week = self.period_initial_date.weekday()
            delta_with_last_day_of_week = datetime.timedelta(days=6 - current_day_of_week)
            return self.period_initial_date + delta_with_last_day_of_week
        elif self.time_unit == TimeUnit.MONTH:
            last_day_of_month = calendar.monthrange(self.period_initial_date.year, self.period_initial_date.month)[1]
            return self.period_initial_date.replace(day=last_day_of_month)
