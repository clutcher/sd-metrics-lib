import math
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED
from typing import Iterable, List, Optional, Dict

from azure.devops.v7_1.work_item_tracking.models import Wiql

from sd_metrics_lib.sources.tasks import TaskProvider


class AzureTaskProvider(TaskProvider):
    WIQL_RESULT_LIMIT_BEFORE_EXCEPTION_THROWING = 19999

    WORK_ITEM_LINKS_SELECTION_QUERY = """
                                      SELECT [Source].[System.Id], [Target].[System.Id]
                                      FROM WorkItemLinks
                                      WHERE [Source].[System.Id] IN ({parent_task_ids})
                                        AND [System.Links.LinkType] = 'System.LinkTypes.Hierarchy-Forward'"""

    WORK_ITEM_UPDATES_CUSTOM_FIELD_NAME = 'CustomExpand.WorkItemUpdate'
    CHILD_TASKS_CUSTOM_FIELD_NAME = 'CustomExpand.ChildTasks'

    DEFAULT_FIELDS = [
        'System.Title',
        'System.WorkItemType',
        'System.State',
        'System.CreatedDate',
        'System.AssignedTo',
        'Microsoft.VSTS.Scheduling.StoryPoints',
        'Microsoft.VSTS.Common.ClosedDate'
    ]

    def __init__(self, azure_client, query: str,
                 additional_fields: Optional[Iterable[str]] = None,
                 custom_expand_fields: Optional[Iterable[str]] = None,
                 page_size: int = 200, thread_pool_executor: Optional[ThreadPoolExecutor] = None) -> None:
        self.azure_client = azure_client
        self.query = query.strip()
        self.additional_fields = list(additional_fields) if additional_fields is not None else list(self.DEFAULT_FIELDS)
        self.custom_expand_fields = custom_expand_fields or []
        self.page_size = max(1, page_size)
        self.thread_pool_executor = thread_pool_executor

    def get_tasks(self) -> list:
        task_ids = self._fetch_task_ids_paginated()
        if not task_ids:
            return []

        return self._fetch_tasks(task_ids, self.custom_expand_fields)

    def _fetch_task_ids_paginated(self) -> List[int]:
        base_query_no_order = self._remove_custom_order_by(self.query)
        last_id = 0
        all_ids: List[int] = []
        while True:
            wiql_text = self._add_tasks_pagination_with_stable_order_by(base_query_no_order, last_id)
            wiql = Wiql(query=wiql_text)
            query_result = self.azure_client.query_by_wiql(wiql, top=self.WIQL_RESULT_LIMIT_BEFORE_EXCEPTION_THROWING)
            items = query_result.work_items or []
            if not items:
                break
            page_ids = [ref.id for ref in items]
            all_ids.extend(page_ids)
            last_id = page_ids[-1]
            if len(page_ids) < self.WIQL_RESULT_LIMIT_BEFORE_EXCEPTION_THROWING:
                break
        return all_ids

    def _fetch_tasks(self, work_item_ids, custom_expand_fields):
        work_item_ids_list = list(work_item_ids)
        total_ids = len(work_item_ids_list)
        total_batches = math.ceil(total_ids / float(self.page_size))
        if self.thread_pool_executor is None:
            fetched_tasks = self._fetch_task_sync(work_item_ids_list, total_batches, total_ids)
        else:
            fetched_tasks = self._fetch_task_concurrently(work_item_ids_list, total_batches, total_ids)

        if custom_expand_fields:
            if self.WORK_ITEM_UPDATES_CUSTOM_FIELD_NAME in custom_expand_fields:
                self._attach_changelog_history(fetched_tasks)

            if self.CHILD_TASKS_CUSTOM_FIELD_NAME in custom_expand_fields:
                self._attach_child_tasks(fetched_tasks)

        return fetched_tasks

    def _fetch_task_sync(self, work_item_ids: List[int], total_batches: int, total_ids: int) -> List:
        tasks = []
        for batch_index in range(total_batches):
            batch_start = batch_index * self.page_size
            batch_end = min(batch_start + self.page_size, total_ids)
            batch_ids = work_item_ids[batch_start:batch_end]
            wis = self.azure_client.get_work_items(ids=batch_ids, fields=self.additional_fields)
            tasks.extend(wis or [])
        return tasks

    def _fetch_task_concurrently(self, work_item_ids: List[int], total_batches: int, total_ids: int) -> List:
        tasks = []
        futures = []
        for batch_index in range(total_batches):
            batch_start = batch_index * self.page_size
            batch_end = min(batch_start + self.page_size, total_ids)
            batch_ids = work_item_ids[batch_start:batch_end]
            futures.append(
                self.thread_pool_executor.submit(self.azure_client.get_work_items, ids=batch_ids,
                                                 fields=self.additional_fields))
        done = wait(futures, return_when=ALL_COMPLETED).done
        for done_feature in done:
            tasks.extend(done_feature.result() or [])
        return tasks

    def _attach_changelog_history(self, tasks: List[object]):
        def fetch_changelog_history(item):
            item.fields[self.WORK_ITEM_UPDATES_CUSTOM_FIELD_NAME] = self.azure_client.get_updates(item.id)

        if self.thread_pool_executor is None:
            for task in tasks:
                fetch_changelog_history(task)
        else:
            futures = [self.thread_pool_executor.submit(fetch_changelog_history, task) for task in tasks]
            wait(futures, return_when=ALL_COMPLETED)

    def _attach_child_tasks(self, tasks: List[object]):
        if not tasks:
            return

        id_to_parent = {task.id: task for task in tasks if task is not None}
        if not id_to_parent:
            return

        child_to_parent = self._fetch_child_relationships_dict(id_to_parent.keys())
        if not child_to_parent:
            return

        child_custom_expand_fields = [
            field for field in self.custom_expand_fields
            if field != self.CHILD_TASKS_CUSTOM_FIELD_NAME
        ]

        child_tasks = self._fetch_tasks(child_to_parent.keys(), child_custom_expand_fields)
        id_to_child = {child.id: child for child in child_tasks if child is not None}

        for child_id, parent_id in child_to_parent.items():
            if child_id in id_to_child and parent_id in id_to_parent:
                parent_task = id_to_parent[parent_id]
                child_task = id_to_child[child_id]
                if self.CHILD_TASKS_CUSTOM_FIELD_NAME not in parent_task.fields:
                    parent_task.fields[self.CHILD_TASKS_CUSTOM_FIELD_NAME] = []
                parent_task.fields[self.CHILD_TASKS_CUSTOM_FIELD_NAME].append(child_task)

    def _fetch_child_relationships_dict(self, parent_ids) -> Dict[int, int]:
        parent_ids_list = list(parent_ids)
        if not parent_ids_list:
            return {}

        parent_ids_str = ', '.join(str(pid) for pid in parent_ids_list)
        base_query = self.WORK_ITEM_LINKS_SELECTION_QUERY.format(parent_task_ids=parent_ids_str)

        child_to_parent = {}
        last_source_id = 0
        while True:
            wiql_query = self._add_relationships_pagination_with_stable_order_by(base_query, last_source_id)
            wiql = Wiql(query=wiql_query)
            query_result = self.azure_client.query_by_wiql(wiql, top=self.WIQL_RESULT_LIMIT_BEFORE_EXCEPTION_THROWING)

            relations = query_result.work_item_relations or []
            if not relations:
                break

            for relation in relations:
                if relation and relation.source and relation.target:
                    child_to_parent[relation.target.id] = relation.source.id
                    last_source_id = max(last_source_id, relation.source.id)

            if len(relations) < self.WIQL_RESULT_LIMIT_BEFORE_EXCEPTION_THROWING:
                break

        return child_to_parent

    @staticmethod
    def _remove_custom_order_by(query_text: str) -> str:
        lower = query_text.lower()
        idx = lower.rfind(" order by ")
        if idx == -1:
            return query_text.strip()
        return query_text[:idx].strip()

    @staticmethod
    def _add_tasks_pagination_with_stable_order_by(base_query_no_order: str, last_id: int) -> str:
        lower = base_query_no_order.lower()
        if " where " in lower:
            paged_query = base_query_no_order + f" AND [System.Id] > {last_id}"
        else:
            paged_query = base_query_no_order + f" WHERE [System.Id] > {last_id}"
        paged_query += " ORDER BY [System.Id] ASC"
        return paged_query

    @staticmethod
    def _add_relationships_pagination_with_stable_order_by(base_query: str, last_source_id: int) -> str:
        if last_source_id == 0:
            return base_query + " ORDER BY [Source].[System.Id] ASC"

        paged_query = base_query + f" AND [Source].[System.Id] > {last_source_id}"
        paged_query += " ORDER BY [Source].[System.Id] ASC"
        return paged_query
