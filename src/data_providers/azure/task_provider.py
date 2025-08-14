import math
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED
from typing import Iterable, List, Optional

from azure.devops.v7_1.work_item_tracking.models import Wiql

from data_providers.task_provider import TaskProvider


class AzureTaskProvider(TaskProvider):
    DEFAULT_FIELDS = [
        'System.Title',
        'System.WorkItemType',
        'System.State',
        'System.CreatedDate',
        'System.AssignedTo',

        'Microsoft.VSTS.Scheduling.StoryPoints',
        'Microsoft.VSTS.Common.ClosedDate',
    ]

    def __init__(self, azure_client, query: str, additional_fields: Optional[Iterable[str]] = None,
                 page_size: int = 200, thread_pool_executor: Optional[ThreadPoolExecutor] = None) -> None:
        self.azure_client = azure_client
        self.query = query.strip()
        self.additional_fields = list(additional_fields) if additional_fields is not None else list(self.DEFAULT_FIELDS)
        self.page_size = max(1, page_size)
        self.thread_pool_executor = thread_pool_executor

    def get_tasks(self) -> list:
        query = Wiql(query=self.query)
        query_result = self.azure_client.query_by_wiql(query)

        work_item_ids = [ref.id for ref in (query_result.work_items or [])]

        fetched_tasks = []
        if not work_item_ids:
            return fetched_tasks

        total_ids = len(work_item_ids)
        total_batches = math.ceil(total_ids / float(self.page_size))

        if self.thread_pool_executor is None:
            fetched_tasks = self._fetch_task_sync(work_item_ids, total_batches, total_ids)
        else:
            fetched_tasks = self._fetch_task_concurrently(work_item_ids, total_batches, total_ids)

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

        def fetch_changelog_history(task):
            task.fields['CustomExpand.WorkItemUpdate'] = self.azure_client.get_updates(task.id)

        if self.thread_pool_executor is None:
            for task in tasks:
                fetch_changelog_history(task)
        else:
            futures = [self.thread_pool_executor.submit(fetch_changelog_history, task) for task in tasks]
            wait(futures, return_when=ALL_COMPLETED)
