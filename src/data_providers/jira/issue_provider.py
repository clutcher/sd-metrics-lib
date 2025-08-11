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


class CachingJiraIssueProvider(JiraIssueProvider):

    def __init__(self,
                 jira_client,
                 query: str,
                 additional_fields: Iterable[str] = None,
                 thread_pool_executor: ThreadPoolExecutor = None,
                 cache=None) -> None:
        super().__init__(jira_client, query, additional_fields, thread_pool_executor)
        self.cache = cache

    def get_issues(self):
        # JIRA API is broken and set of maxResults doesn`t works.
        # return jira.jql(jql_query, limit=MAX_SEARCH_RESULTS)

        cached_issues = self._search_in_cache()
        if cached_issues is not None:
            return cached_issues

        issues = super(CachingJiraIssueProvider, self).get_issues()

        self._set_in_cache(issues)

        return issues

    def _search_in_cache(self):
        if self.cache is None:
            return None

        # if query with same additional_fields is already present in cache
        cache_key_with_fields = self._create_cache_key_for_query()
        if self._is_key_in_cache(cache_key_with_fields):
            return self._get_from_cache(cache_key_with_fields)

        # searching for cached responses with not less additional_fields (superset)
        partial_key = self._create_partial_cache_key()
        for key in self._get_all_cache_keys():
            if key.startswith(partial_key):
                if self.additional_fields is None:
                    return self._get_from_cache(key)
                else:
                    all_fields_present = True
                    for field in self.additional_fields:
                        if "_" + field not in key:
                            all_fields_present = False
                    if all_fields_present:
                        return self._get_from_cache(key)

        return None

    def _get_from_cache(self, cache_key):
        return self.cache.get(cache_key)

    def _set_in_cache(self, issues):
        if self.cache is None:
            return
        self.cache[self._create_cache_key_for_query()] = issues

    def _is_key_in_cache(self, cache_key):
        return cache_key in self.cache

    def _get_all_cache_keys(self):
        return self.cache.keys()

    def _create_cache_key_for_query(self):
        if self.additional_fields is None:
            return self._create_partial_cache_key()
        return self._create_partial_cache_key() + "_".join(self.additional_fields)

    def _create_partial_cache_key(self):
        return base64.b64encode(self.query.encode("ascii")).decode("ascii") + "||"
