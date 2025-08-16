import datetime
from enum import Enum, auto
from typing import Optional


class JiraSearchQueryBuilder:
    class __QueryParts(Enum):
        PROJECT = auto()
        TYPE = auto()
        STATUS = auto()
        RESOLUTION_DATE = auto()
        LAST_MODIFIED = auto()
        TEAM = auto()
        TASK_IDS = auto()
        ORDER_BY = auto()

    def __init__(self,
                 projects: list[str] = None,
                 statuses: list[str] = None,
                 task_types: list[str] = None,
                 teams: list[str] = None,
                 resolution_dates: tuple[Optional[datetime.datetime], Optional[datetime.datetime]] = None,
                 last_modified_dates: tuple[Optional[datetime.datetime], Optional[datetime.datetime]] = None,
                 task_ids: list[str] = None,
                 raw_queries: list[str] = None,
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
        self.with_raw_queries(raw_queries)
        self.with_order_by(order_by)

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

    def with_resolution_dates(self, resolution_dates: tuple[Optional[datetime.datetime], Optional[datetime.datetime]]):
        if resolution_dates is None:
            return
        date_filter = self.__create_date_range_filter("resolutiondate",
                                                      resolution_dates[0],
                                                      resolution_dates[1])
        if date_filter:
            self.__add_filter(self.__QueryParts.RESOLUTION_DATE, date_filter)

    def with_last_modified_dates(self, last_modified_datas: tuple[Optional[datetime.datetime], Optional[datetime.datetime]]):
        if last_modified_datas is None:
            return
        date_filter = self.__create_date_range_filter("updated",
                                                      last_modified_datas[0],
                                                      last_modified_datas[1])
        if date_filter:
            self.__add_filter(self.__QueryParts.LAST_MODIFIED, date_filter)

    def with_task_types(self, task_types):
        if task_types is None:
            return
        task_type_filter = "issuetype in (" + self.__convert_in_jql_value_list(task_types) + ")"
        self.__add_filter(self.__QueryParts.TYPE, task_type_filter)

    def with_task_ids(self, task_ids: list[str]):
        if task_ids is None:
            return
        ids_filter = "key in (" + ", ".join(task_ids) + ")"
        self.__add_filter(self.__QueryParts.TASK_IDS, ids_filter)

    def with_teams(self, teams: list[str]):
        if teams is None:
            return
        team_filter = "Team[Team] in (" + self.__convert_in_jql_value_list(teams) + ")"
        self.__add_filter(self.__QueryParts.TEAM, team_filter)

    def with_raw_queries(self, raw_queries: list[str]):
        if raw_queries is None:
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
    def __convert_in_jql_value_list(statuses):
        return ', '.join(['"%s"' % w for w in statuses])

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

