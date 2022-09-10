import datetime
from abc import ABC, abstractmethod

from calculators.utils import time_utils
from calculators.utils.time_utils import WEEKDAY_FRIDAY


class WorkTimeExtractor(ABC):

    @abstractmethod
    def extract_time_from_period(self, start_time_period: datetime.date, end_time_period: datetime.date) -> int | None:
        pass


class SimpleWorkTimeExtractor(WorkTimeExtractor):

    def extract_time_from_period(self,
                                 start_time_period: datetime.date,
                                 end_time_period: datetime.date) -> int | None:
        # Use businesstimedelta lib for more precision calculation
        period_delta = end_time_period - start_time_period

        if period_delta.days > 0:
            work_days = self.__count_work_days(start_time_period, end_time_period)
            round_up_period_days = period_delta.days + 1
            return min(work_days, round_up_period_days) * time_utils.get_seconds_in_day()
        elif period_delta.total_seconds() < 15 * 60:
            return None
        elif period_delta.total_seconds() < time_utils.get_seconds_in_day():
            return int(period_delta.total_seconds())
        else:
            return time_utils.get_seconds_in_day()

    @staticmethod
    def __count_work_days(start_date: datetime.date, end_date: datetime.date):
        # if the start date is on a weekend, forward the date to next Monday
        if start_date.weekday() > WEEKDAY_FRIDAY:
            start_date = start_date + datetime.timedelta(days=7 - start_date.weekday())

        # if the end date is on a weekend, rewind the date to the previous Friday
        if end_date.weekday() > WEEKDAY_FRIDAY:
            end_date = end_date - datetime.timedelta(days=end_date.weekday() - WEEKDAY_FRIDAY)

        if start_date > end_date:
            return 0
        # that makes the difference easy, no remainders etc
        diff_days = (end_date - start_date).days + 1
        weeks = int(diff_days / 7)

        remainder = end_date.weekday() - start_date.weekday() + 1
        if remainder != 0 and end_date.weekday() < start_date.weekday():
            remainder = 5 + remainder

        return weeks * 5 + remainder


class BoundarySimpleWorkTimeExtractor(SimpleWorkTimeExtractor):

    def __init__(self,
                 start_time_boundary: datetime.date,
                 end_time_boundary: datetime.date) -> None:
        self.start_time_boundary = start_time_boundary
        self.end_time_boundary = end_time_boundary

    def extract_time_from_period(self, start_time_period: datetime.date, end_time_period: datetime.date) -> int | None:

        if self.start_time_boundary < start_time_period:
            new_start_period = start_time_period
        else:
            new_start_period = self.start_time_boundary

        if self.end_time_boundary > end_time_period:
            new_end_time_period = end_time_period
        else:
            new_end_time_period = self.end_time_boundary

        return super().extract_time_from_period(new_start_period, new_end_time_period)
