import datetime
from enum import Enum, auto
from typing import Optional, Iterable


class JiraSearchQueryBuilder:
    class __QueryParts(Enum):
        PROJECT = auto()
        TYPE = auto()
        STATUS = auto()
        RESOLUTION_DATE = auto()
        LAST_MODIFIED = auto()
        TEAM = auto()
        TASK_IDS = auto()
        ASSIGNEES = auto()
        ASSIGNEES_HISTORY = auto()
        ORDER_BY = auto()

    def __init__(self,
                 projects: Iterable[str] = None,
                 statuses: Iterable[str] = None,
                 task_types: Iterable[str] = None,
                 teams: Iterable[str] = None,
                 resolution_dates: tuple[Optional[datetime.datetime], Optional[datetime.datetime]] = None,
                 last_modified_dates: tuple[Optional[datetime.datetime], Optional[datetime.datetime]] = None,
                 task_ids: Iterable[str] = None,
                 assignees: Iterable[str] = None,
                 raw_queries: Iterable[str] = None,
                 order_by: Optional[str] = None
                 ) -> None:
        self.query_parts = {}
        self.raw_queries: list[str] = []

        self.with_projects(projects)
        self.with_statuses(statuses)
        self.with_resolution_dates(resolution_dates)
        self.with_task_types(task_types)
        self.with_teams(teams)
        self.with_last_modified_dates(last_modified_dates)
        self.with_task_ids(task_ids)
        self.with_assignees(assignees)
        self.with_raw_queries(raw_queries)
        self.with_order_by(order_by)

    def with_projects(self, projects: Iterable[str]):
        if not projects:
            return
        project_filter = "project IN (" + self.__convert_in_jql_value_list(projects) + ")"
        self.__add_filter(self.__QueryParts.PROJECT, project_filter)

    def with_statuses(self, statuses: Iterable[str]):
        if not statuses:
            return
        status_filter = "status in (" + self.__convert_in_jql_value_list(statuses) + ")"
        self.__add_filter(self.__QueryParts.STATUS, status_filter)

    def with_resolution_dates(self, resolution_dates: tuple[Optional[datetime.datetime], Optional[datetime.datetime]]):
        if not resolution_dates:
            return
        date_filter = self.__create_date_range_filter("resolutiondate",
                                                      resolution_dates[0],
                                                      resolution_dates[1])
        if date_filter:
            self.__add_filter(self.__QueryParts.RESOLUTION_DATE, date_filter)

    def with_last_modified_dates(self, last_modified_datas: tuple[Optional[datetime.datetime], Optional[datetime.datetime]]):
        if not last_modified_datas:
            return
        date_filter = self.__create_date_range_filter("updated",
                                                      last_modified_datas[0],
                                                      last_modified_datas[1])
        if date_filter:
            self.__add_filter(self.__QueryParts.LAST_MODIFIED, date_filter)

    def with_task_types(self, task_types: Iterable[str]):
        if not task_types:
            return
        task_type_filter = "issuetype in (" + self.__convert_in_jql_value_list(task_types) + ")"
        self.__add_filter(self.__QueryParts.TYPE, task_type_filter)

    def with_task_ids(self, task_ids: Iterable[str]):
        if not task_ids:
            return
        ids_filter = "key in (" + ", ".join(task_ids) + ")"
        self.__add_filter(self.__QueryParts.TASK_IDS, ids_filter)

    def with_teams(self, teams: Iterable[str]):
        if not teams:
            return
        team_filter = "Team[Team] in (" + self.__convert_in_jql_value_list(teams) + ")"
        self.__add_filter(self.__QueryParts.TEAM, team_filter)

    def with_assignees(self, assignees: Iterable[str]):
        if not assignees:
            return
        assignees_filter = "assignee in (" + self.__convert_in_jql_value_list(assignees) + ")"
        self.__add_filter(self.__QueryParts.ASSIGNEES, assignees_filter)

    def with_assignees_history(self, assignees: Iterable[str]):
        if not assignees:
            return
        assignees_filter = "assignee WAS IN (" + self.__convert_in_jql_value_list(assignees) + ")"
        self.__add_filter(self.__QueryParts.ASSIGNEES_HISTORY, assignees_filter)

    def with_raw_queries(self, raw_queries: Iterable[str]):
        if not raw_queries:
            return
        normalized = [q.strip() for q in raw_queries if q and q.strip()]
        if not normalized:
            return
        self.raw_queries.extend(normalized)

    def with_order_by(self, order_by: str):
        if not order_by:
            return
        self.__add_filter(self.__QueryParts.ORDER_BY, order_by)

    def build_query(self) -> str:
        where_parts = [v for k, v in self.query_parts.items() if k != self.__QueryParts.ORDER_BY]
        if self.raw_queries:
            where_parts.extend([q.strip() for q in self.raw_queries if q and q.strip()])
        base = ' AND '.join(where_parts)
        order_by = self.query_parts.get(self.__QueryParts.ORDER_BY)
        if order_by:
            if base:
                return base + ' ORDER BY ' + order_by
            else:
                return 'ORDER BY ' + order_by
        return base

    @staticmethod
    def __convert_in_jql_value_list(values: Iterable[str]):
        return ', '.join(['"%s"' % w for w in values])

    @staticmethod
    def __create_date_range_filter(field_name: str, start_date: Optional[datetime.date], end_date: Optional[datetime.date]):
        parts = []
        if start_date is not None:
            start_date_str = start_date.strftime('%Y-%m-%d')
            parts.append(f"{field_name} >= '{start_date_str}'")
        if end_date is not None:
            end_date_str = end_date.strftime('%Y-%m-%d')
            parts.append(f"{field_name} <= '{end_date_str}'")
        return ' and '.join(parts)

    def __add_filter(self, query_part_type: __QueryParts, query_part):
        self.query_parts[query_part_type] = query_part.strip()

