from data_providers import IssueProvider


class JiraIssueProvider(IssueProvider):

    def __init__(self, jira_client, query: str, expand: [str] = None) -> None:
        self.jira_client = jira_client
        self.query = query.strip()
        self.expand = expand
        if expand is None:
            self.expand_str = None
        else:
            self.expand_str = ",".join(self.expand)

    def get_issues(self):
        # JIRA API is broken and set of maxResults doesn`t works.
        # return jira.jql(jql_query, limit=MAX_SEARCH_RESULTS)

        first_page = self.jira_client.jql(self.query, expand=self.expand_str)

        isssues = []
        first_page_issues = first_page["issues"]
        isssues.extend(first_page_issues)

        issues_total_count = first_page["total"]
        first_page_len = len(first_page_issues)
        if first_page_len < issues_total_count:
            next_search_start = first_page_len
            while next_search_start < issues_total_count:
                current_page_result = self.jira_client.jql(self.query, expand=self.expand_str, start=next_search_start)
                current_page_issues = current_page_result["issues"]
                next_search_start += len(current_page_issues)
                isssues.extend(current_page_issues)

        return isssues


class CachingJiraIssueProvider(JiraIssueProvider):

    def __init__(self, jira_client, query: str, expand: [str] = None, cache=None) -> None:
        super().__init__(jira_client, query, expand)
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

        # if query with same expands is already present in cache
        cache_key = self._create_cache_key_for_query()
        if self._is_key_in_cache(cache_key):
            return self._get_from_cache(cache_key)

        # searching for cached responses with not less expands
        # for example we have in cache query with worklog expand and searching
        # fir same query without expands. In such case we can safely return cached results.
        for key in self._get_all_cache_keys():
            if key.startswith(self.query):
                if self.expand is None:
                    return self._get_from_cache(key)
                else:
                    all_expands_present = True
                    for expand in self.expand:
                        if "_" + expand not in key:
                            all_expands_present = False
                    if all_expands_present:
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
        if self.expand is None:
            return self.query
        return self.query + "_" + "_".join(self.expand)
