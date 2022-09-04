import calendar
import datetime
from enum import Enum, auto

from dateutil.relativedelta import relativedelta

from data_providers.utils import VelocityTimeUnit


class JiraIssueSearchQueryBuilder:
    class __QueryParts(Enum):
        PROJECT = auto()
        TYPE = auto()
        STATUS = auto()
        RESOLUTION_DATE = auto()
        LAST_MODIFIED = auto()

    def __init__(self,
                 projects: list[str] = None,
                 resolution_dates: tuple[datetime.datetime, datetime.datetime] = None,
                 statuses: list[str] = None,
                 issue_types: list[str] = None
                 ) -> None:
        self.query_parts = {}

        self.with_projects(projects)
        self.with_statuses(statuses)
        self.for_resolution_dates(resolution_dates)
        self.for_issue_types(issue_types)

    def with_projects(self, projects: list[str]):
        if projects is None:
            return
        project_filter = "project IN (" + ",".join(projects) + ")"
        self.__add_filter(self.__QueryParts.PROJECT, project_filter)

    def with_statuses(self, statuses):
        if statuses is None:
            return
        status_filter = "status in (" + self.__convert_in_jql_value_list(statuses) + ")"
        self.__add_filter(self.__QueryParts.STATUS, status_filter)

    def for_resolution_dates(self, resolution_dates: tuple[datetime.datetime, datetime.datetime]):
        if resolution_dates is None:
            return
        date_filter = self.__create_date_range_filter("resolutiondate",
                                                      resolution_dates[0],
                                                      resolution_dates[1])
        self.__add_filter(self.__QueryParts.RESOLUTION_DATE, date_filter)

    def for_last_modified_dates(self, last_modified_datas: tuple[datetime.datetime, datetime.datetime]):
        if last_modified_datas is None:
            return
        date_filter = self.__create_date_range_filter("updated",
                                                      last_modified_datas[0],
                                                      last_modified_datas[1])
        self.__add_filter(self.__QueryParts.LAST_MODIFIED, date_filter)

    def for_issue_types(self, issue_types):
        if issue_types is None:
            return
        issue_type_filter = "issuetype in (" + self.__convert_in_jql_value_list(issue_types) + ")"
        self.__add_filter(self.__QueryParts.TYPE, issue_type_filter)

    def build_query(self) -> str:
        return ' AND '.join(self.query_parts.values())

    @staticmethod
    def __convert_in_jql_value_list(statuses):
        return ', '.join(['"%s"' % w for w in statuses])

    @staticmethod
    def __create_date_range_filter(field_name: str, start_date: datetime.date, end_date: datetime.date):
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        return "%s >= '%s' and %s <= '%s'" % (field_name, start_date_str, field_name, end_date_str)

    def __add_filter(self, query_part_type: __QueryParts, query_part):
        self.query_parts[query_part_type] = query_part.strip()


class TimeRangeGenerator:

    def __init__(self, time_unit: VelocityTimeUnit, number_of_ranges: int) -> None:
        self.time_unit = time_unit
        self.number_of_ranges = number_of_ranges
        self.period_initial_date = datetime.datetime.today()

    def __iter__(self):
        for i in range(self.number_of_ranges):
            yield tuple((self.__resolve_start_date_of_period(), self.__resolve_end_date_of_period()))
            self.__decrease_date_range()

    def __decrease_date_range(self):
        if self.time_unit == VelocityTimeUnit.HOUR:
            self.period_initial_date -= relativedelta(hours=1)
        elif self.time_unit == VelocityTimeUnit.DAY:
            self.period_initial_date -= relativedelta(days=1)
        elif self.time_unit == VelocityTimeUnit.WEEK:
            self.period_initial_date -= relativedelta(weeks=1)
        elif self.time_unit == VelocityTimeUnit.MONTH:
            self.period_initial_date -= relativedelta(months=1)

    def __resolve_start_date_of_period(self) -> datetime.datetime:
        if self.time_unit == VelocityTimeUnit.HOUR:
            return self.period_initial_date.replace(minute=0, second=0, microsecond=0)
        elif self.time_unit == VelocityTimeUnit.DAY:
            return self.period_initial_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif self.time_unit == VelocityTimeUnit.WEEK:
            current_day_of_week = self.period_initial_date.weekday()
            delta_with_first_day_of_week = datetime.timedelta(days=current_day_of_week)
            return self.period_initial_date - delta_with_first_day_of_week
        elif self.time_unit == VelocityTimeUnit.MONTH:
            return self.period_initial_date.replace(day=1)

    def __resolve_end_date_of_period(self):
        if self.time_unit == VelocityTimeUnit.HOUR:
            return self.period_initial_date.replace(minute=59, second=59, microsecond=999999)
        elif self.time_unit == VelocityTimeUnit.DAY:
            return self.period_initial_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        elif self.time_unit == VelocityTimeUnit.WEEK:
            current_day_of_week = self.period_initial_date.weekday()
            delta_with_last_day_of_week = datetime.timedelta(days=6 - current_day_of_week)
            return self.period_initial_date - delta_with_last_day_of_week
        elif self.time_unit == VelocityTimeUnit.MONTH:
            last_day_of_month = calendar.monthrange(self.period_initial_date.year, self.period_initial_date.month)[1]
            return self.period_initial_date.replace(day=last_day_of_month)
