import math
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED
from typing import Iterable, List, Optional

from azure.devops.v7_1.work_item_tracking.models import Wiql

from data_providers.issue_provider import IssueProvider


class AzureIssueProvider(IssueProvider):
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

    def get_issues(self) -> list:
        query = Wiql(query=self.query)
        query_result = self.azure_client.query_by_wiql(query)

        work_item_ids = [ref.id for ref in (query_result.work_items or [])]

        fetched_issues = []
        if not work_item_ids:
            return fetched_issues

        total_ids = len(work_item_ids)
        total_batches = math.ceil(total_ids / float(self.page_size))

        if self.thread_pool_executor is None:
            fetched_issues = self._fetch_issue_sync(work_item_ids, total_batches, total_ids)
        else:
            fetched_issues = self._fetch_issue_concurrently(work_item_ids, total_batches, total_ids)

        self._attach_changelog_history(fetched_issues)
        return fetched_issues

    def _fetch_issue_sync(self, work_item_ids: List[int], total_batches: int, total_ids: int) -> List:
        issues = []
        for batch_index in range(total_batches):
            batch_start = batch_index * self.page_size
            batch_end = min(batch_start + self.page_size, total_ids)
            batch_ids = work_item_ids[batch_start:batch_end]
            wis = self.azure_client.get_work_items(ids=batch_ids, fields=self.additional_fields)
            issues.extend(wis or [])
        return issues

    def _fetch_issue_concurrently(self, work_item_ids: List[int], total_batches: int, total_ids: int) -> List:
        issues = []
        futures = []
        for batch_index in range(total_batches):
            batch_start = batch_index * self.page_size
            batch_end = min(batch_start + self.page_size, total_ids)
            batch_ids = work_item_ids[batch_start:batch_end]
            futures.append(
                self.thread_pool_executor.submit(self.azure_client.get_work_items, ids=batch_ids, fields=self.additional_fields))
        done = wait(futures, return_when=ALL_COMPLETED).done
        for done_feature in done:
            issues.extend(done_feature.result() or [])
        return issues

    def _attach_changelog_history(self, issues: List[object]):

        def fetch_changelog_history(issue):
            issue.fields['CustomExpand.WorkItemUpdate'] = self.azure_client.get_updates(issue.id)

        if self.thread_pool_executor is None:
            for issue in issues:
                fetch_changelog_history(issue)
        else:
            futures = [self.thread_pool_executor.submit(fetch_changelog_history, issue) for issue in issues]
            wait(futures, return_when=ALL_COMPLETED)
