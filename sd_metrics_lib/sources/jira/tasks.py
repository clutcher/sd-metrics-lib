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
        tasks = self._fetch_tasks(self.query, self._expand_str)
        if self.additional_fields and 'subtasks' in self.additional_fields:
            self._fetch_child_tasks_and_replace_subtasks_field(tasks)

        return tasks

    def _fetch_tasks(self, query: str, expand_str: str):
        first_page = self.jira_client.jql(query, expand=expand_str, limit=self._get_task_fetch_amount())
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

    def _fetch_child_tasks_and_replace_subtasks_field(self, jira_tasks: Iterable[dict]):
        if not jira_tasks:
            return

        child_tasks_ids = []
        task_id_to_child_tasks_ids = {}
        for jira_task in jira_tasks:
            subtasks = jira_task.get('fields', {}).get('subtasks', [])
            if subtasks:
                subtasks_ids = [subtask.get('key') for subtask in subtasks if subtask.get('key')]
                if subtasks_ids:
                    child_tasks_ids.extend(subtasks_ids)
                    task_id_to_child_tasks_ids[jira_task['key']] = subtasks_ids

        if not child_tasks_ids:
            return

        child_task_id_to_child_task = self._fetch_tasks_by_id(child_tasks_ids)
        for task in jira_tasks:
            task_key = task['key']
            if task_key in task_id_to_child_tasks_ids:
                task['fields']['subtasks'] = self._create_child_task_list(
                    task_key,
                    task_id_to_child_tasks_ids,
                    child_task_id_to_child_task
                )

    def _fetch_tasks_by_id(self, task_ids):
        query = "key in (" + ", ".join(task_ids) + ")"
        child_tasks = self._fetch_tasks(
            query,
            ",".join([field for field in self.additional_fields if field != 'subtasks'])
        )
        return {task['key']: task for task in child_tasks}

    @staticmethod
    def _create_child_task_list(task_key, task_to_child_tasks_ids, child_task_id_to_child_task):
        return [
            child_task_id_to_child_task[child_key]
            for child_key in task_to_child_tasks_ids[task_key]
            if child_key in child_task_id_to_child_task
        ]

    def _get_task_fetch_amount(self):
        if self.thread_pool_executor is None:
            return 100
        else:
            return 50
