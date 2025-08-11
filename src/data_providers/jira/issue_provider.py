import base64
import concurrent
import math
from concurrent.futures import ThreadPoolExecutor, wait
from typing import Iterable

from data_providers import IssueProvider


class JiraIssueProvider(IssueProvider):

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

    def get_issues(self):
        first_page = self.jira_client.jql(self.query, expand=self._expand_str, limit=self._get_issue_fetch_amount())
        first_page_issues = first_page["issues"]
        issues_total_count = first_page["total"]
        page_len = len(first_page_issues)

        issues = []
        issues.extend(first_page_issues)

        if page_len < issues_total_count:
            amount_of_fetches = math.ceil(issues_total_count / float(page_len))

            if self.thread_pool_executor is None:
                self._fetch_issue_sync(issues, amount_of_fetches, page_len)
            else:
                self._fetch_issue_concurrently(issues, amount_of_fetches, page_len)

        return issues

    def _fetch_issue_concurrently(self, issues, amount_of_fetches, page_len):
        features = []
        for i in range(1, amount_of_fetches):
            next_search_start = i * page_len
            feature = self.thread_pool_executor.submit(self.jira_client.jql,
                                                       self.query,
                                                       expand=self._expand_str,
                                                       limit=self._get_issue_fetch_amount(),
                                                       start=next_search_start)
            features.append(feature)
        done, not_done = wait(features, return_when=concurrent.futures.ALL_COMPLETED)
        for feature in done:
            issues.extend(feature.result()["issues"])

    def _fetch_issue_sync(self, issues, amount_of_fetches, page_len):
        for i1 in range(1, amount_of_fetches):
            start = i1 * page_len
            current_page_result = self.jira_client.jql(self.query,
                                                       expand=self._expand_str,
                                                       limit=self._get_issue_fetch_amount(),
                                                       start=start)
            current_page_issues = current_page_result["issues"]
            issues.extend(current_page_issues)

    def _get_issue_fetch_amount(self):
        if self.thread_pool_executor is None:
            return 100
        else:
            return 50