import datetime
from enum import Enum, auto


class JiraSearchQueryBuilder:
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
                 task_types: list[str] = None
                 ) -> None:
        self.query_parts = {}

        self.with_projects(projects)
        self.with_statuses(statuses)
        self.for_resolution_dates(resolution_dates)
        self.for_task_types(task_types)

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

    def for_task_types(self, task_types):
        if task_types is None:
            return
        task_type_filter = "issuetype in (" + self.__convert_in_jql_value_list(task_types) + ")"
        self.__add_filter(self.__QueryParts.TYPE, task_type_filter)

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

