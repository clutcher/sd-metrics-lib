from data_providers import IssueProvider


class JiraIssueProvider(IssueProvider):

    def __init__(self, jira_client, query: str, expand=None) -> None:
        self.jira_client = jira_client
        self.query = query
        self.expand = expand

    def get_issues(self):
        # JIRA API is broken and set of maxResults doesn`t works.
        # return jira.jql(jql_query, limit=MAX_SEARCH_RESULTS)

        first_page = self.jira_client.jql(self.query, expand=self.expand)

        isssues = []
        first_page_issues = first_page["issues"]
        isssues.extend(first_page_issues)

        issues_total_count = first_page["total"]
        first_page_len = len(first_page_issues)
        if first_page_len < issues_total_count:
            next_search_start = first_page_len
            while next_search_start < issues_total_count:
                current_page_result = self.jira_client.jql(self.query, expand=self.expand, start=next_search_start)
                current_page_issues = current_page_result["issues"]
                next_search_start += len(current_page_issues)
                isssues.extend(current_page_issues)

        return isssues
