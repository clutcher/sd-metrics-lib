import concurrent
import math
from concurrent.futures import ThreadPoolExecutor, wait
from typing import Iterable

from sd_metrics_lib.sources.tasks import TaskProvider


class JiraTaskProvider(TaskProvider):

    def __init__(self,
                 jira_client,
                 query: str,
                 additional_fields: Iterable[str] = None,
                 thread_pool_executor: ThreadPoolExecutor = None) -> None:
        self.jira_client = jira_client
        self.query = query.strip()
        self.additional_fields = additional_fields
        if additional_fields is None:
            self._expand_str = None
        else:
            # For Jira, additional_fields correspond to expand values (e.g., 'changelog')
            self._expand_str = ",".join(self.additional_fields)
        self.thread_pool_executor = thread_pool_executor

    def get_tasks(self):
        first_page = self.jira_client.jql(self.query, expand=self._expand_str, limit=self._get_task_fetch_amount())
        first_page_tasks = first_page.get("issues", [])
        tasks_total_count = first_page.get("total", len(first_page_tasks))
        page_len = len(first_page_tasks)

        if tasks_total_count == 0 or page_len == 0:
            return []

        tasks = []
        tasks.extend(first_page_tasks)

        if page_len < tasks_total_count:
            amount_of_fetches = math.ceil(tasks_total_count / float(page_len))

            if self.thread_pool_executor is None:
                self._fetch_task_sync(tasks, amount_of_fetches, page_len)
            else:
                self._fetch_task_concurrently(tasks, amount_of_fetches, page_len)

        return tasks

    def _fetch_task_concurrently(self, tasks, amount_of_fetches, page_len):
        features = []
        for i in range(1, amount_of_fetches):
            next_search_start = i * page_len
            feature = self.thread_pool_executor.submit(self.jira_client.jql,
                                                       self.query,
                                                       expand=self._expand_str,
                                                       limit=self._get_task_fetch_amount(),
                                                       start=next_search_start)
            features.append(feature)
        done, not_done = wait(features, return_when=concurrent.futures.ALL_COMPLETED)
        for feature in done:
            tasks.extend(feature.result().get("issues", []))

    def _fetch_task_sync(self, tasks, amount_of_fetches, page_len):
        for i in range(1, amount_of_fetches):
            start = i * page_len
            current_page_result = self.jira_client.jql(self.query,
                                                       expand=self._expand_str,
                                                       limit=self._get_task_fetch_amount(),
                                                       start=start)
            current_page_tasks = current_page_result.get("issues", [])
            tasks.extend(current_page_tasks)

    def _get_task_fetch_amount(self):
        if self.thread_pool_executor is None:
            return 100
        else:
            return 50
