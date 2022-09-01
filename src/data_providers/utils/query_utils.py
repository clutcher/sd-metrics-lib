import datetime
from enum import Enum, auto


class JiraIssueSearchQueryBuilder:
    class __QueryParts(Enum):
        PROJECT = auto()
        TYPE = auto()
        STATUS = auto()
        RESOLUTION_DATE = auto()

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
        start_date_str = resolution_dates[0].strftime('%Y-%m-%d')
        end_date_str = resolution_dates[1].strftime('%Y-%m-%d')
        resolution_date_filter = "resolutiondate >= '%s' and resolutiondate <= '%s'" % (start_date_str, end_date_str)
        self.__add_filter(self.__QueryParts.RESOLUTION_DATE, resolution_date_filter)

    def for_issue_types(self, issue_types):
        if issue_types is None:
            return
        issue_type_filter = "issuetype in (" + self.__convert_in_jql_value_list(issue_types) + ")"
        self.__add_filter(self.__QueryParts.TYPE, issue_type_filter)

    def build_query(self) -> str:
        return ' '.join(self.query_parts.values())

    @staticmethod
    def __convert_in_jql_value_list(statuses):
        return ', '.join(['"%s"' % w for w in statuses])

    def __add_filter(self, query_part_type: __QueryParts, query_part):
        self.query_parts[query_part_type] = query_part.strip()
