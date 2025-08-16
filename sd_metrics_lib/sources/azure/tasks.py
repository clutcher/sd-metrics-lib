import math
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED
from typing import Iterable, List, Optional

from azure.devops.v7_1.work_item_tracking.models import Wiql

from sd_metrics_lib.sources.tasks import TaskProvider


class AzureTaskProvider(TaskProvider):

    WIQL_RESULT_LIMIT_BEFORE_EXCEPTION_THROWING = 19999

    WORK_ITEM_UPDATES_CUSTOM_FIELD_NAME = 'CustomExpand.WorkItemUpdate'
    DEFAULT_FIELDS = [
        'System.Title',
        'System.WorkItemType',
        'System.State',
        'System.CreatedDate',
        'System.AssignedTo',

        'Microsoft.VSTS.Scheduling.StoryPoints',
        'Microsoft.VSTS.Common.ClosedDate'
    ]

    def __init__(self, azure_client, query: str, additional_fields: Optional[Iterable[str]] = None,
                 custom_expand_fields: Optional[Iterable[str]] = None,
                 page_size: int = 200, thread_pool_executor: Optional[ThreadPoolExecutor] = None) -> None:
        self.azure_client = azure_client
        self.query = query.strip()
        self.additional_fields = list(additional_fields) if additional_fields is not None else list(self.DEFAULT_FIELDS)
        self.custom_expand_fields = custom_expand_fields
        self.page_size = max(1, page_size)
        self.thread_pool_executor = thread_pool_executor

    def get_tasks(self) -> list:
        work_item_ids = self._fetch_all_work_item_ids_paginated()

        fetched_tasks = []
        if not work_item_ids:
            return fetched_tasks

        total_ids = len(work_item_ids)
        total_batches = math.ceil(total_ids / float(self.page_size))

        if self.thread_pool_executor is None:
            fetched_tasks = self._fetch_task_sync(work_item_ids, total_batches, total_ids)
        else:
            fetched_tasks = self._fetch_task_concurrently(work_item_ids, total_batches, total_ids)

        if self.custom_expand_fields and self.WORK_ITEM_UPDATES_CUSTOM_FIELD_NAME in self.custom_expand_fields:
            self._attach_changelog_history(fetched_tasks)
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
                self.thread_pool_executor.submit(self.azure_client.get_work_items, ids=batch_ids, fields=self.additional_fields))
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

    def _fetch_all_work_item_ids_paginated(self) -> List[int]:
        base_query_no_order = self._remove_custom_order_by(self.query)
        last_id = 0
        all_ids: List[int] = []
        while True:
            wiql_text = self._add_pagination_with_stable_order_by(base_query_no_order, last_id)
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

    @staticmethod
    def _remove_custom_order_by(query_text: str) -> str:
        lower = query_text.lower()
        idx = lower.rfind(" order by ")
        if idx == -1:
            return query_text.strip()
        return query_text[:idx].strip()

    @staticmethod
    def _add_pagination_with_stable_order_by(base_query_no_order: str, last_id: int) -> str:
        lower = base_query_no_order.lower()
        if " where " in lower:
            paged_query = base_query_no_order + f" AND [System.Id] > {last_id}"

        else:
            paged_query = base_query_no_order + f" WHERE [System.Id] > {last_id}"
        paged_query += " ORDER BY [System.Id] ASC"
        return paged_query
