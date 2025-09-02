import datetime
import unittest

from sd_metrics_lib.sources.azure.query import AzureSearchQueryBuilder


class AzureSearchQueryBuilderTestCase(unittest.TestCase):

    def test_empty_builder_returns_select_statement(self):
        # given
        builder = AzureSearchQueryBuilder()
        # when
        query = builder.build_query()
        # then
        self.assertEqual('SELECT [System.Id] FROM workitems', query)

    def test_task_ids_only(self):
        # given
        builder = AzureSearchQueryBuilder(task_ids=['1', '2', '3'])
        # when
        query = builder.build_query()
        # then
        expected = "SELECT [System.Id] FROM workitems WHERE [System.Id] IN (1, 2, 3)"
        self.assertEqual(expected, query)

    def test_full_query_build_with_multiple_teams_and_order_by(self):
        # given
        builder = AzureSearchQueryBuilder(
            projects=['Proj1', 'Proj2'],
            statuses=['Active', 'Closed'],
            task_types=['User Story', 'Bug'],
            teams=['Team A', 'Team B'],
            resolution_dates=(datetime.date(2022, 3, 1), datetime.date(2022, 3, 31)),
            last_modified_dates=(datetime.date(2022, 2, 1), None),
            raw_queries=['[Custom.Field] = 1', '   ', None],
            order_by='[System.ChangedDate] DESC'
        )
        # when
        query = builder.build_query()
        # then
        expected = f"SELECT [System.Id] FROM workitems WHERE {(
            "[System.TeamProject] IN ('Proj1', 'Proj2')"
            " AND [System.State] IN ('Active', 'Closed')"
            " AND [Microsoft.VSTS.Common.ClosedDate] >= '2022-03-01' AND [Microsoft.VSTS.Common.ClosedDate] <= '2022-03-31'"
            " AND [System.WorkItemType] IN ('User Story', 'Bug')"
            " AND [System.AreaPath] IN ('Team A', 'Team B')"
            " AND [System.ChangedDate] >= '2022-02-01'"
            " AND [Custom.Field] = 1"
        )} ORDER BY [System.ChangedDate] DESC"
        self.assertEqual(expected, query)

    def test_single_team_no_parentheses(self):
        # given
        builder = AzureSearchQueryBuilder(
            teams=['Team A']
        )
        # when
        query = builder.build_query()
        # then
        expected = "SELECT [System.Id] FROM workitems WHERE [System.AreaPath] IN ('Team A')"
        self.assertEqual(expected, query)

    def test_order_by_only_appended(self):
        # given
        builder = AzureSearchQueryBuilder(order_by='[System.CreatedDate] ASC')
        # when
        query = builder.build_query()
        # then
        self.assertEqual('SELECT [System.Id] FROM workitems ORDER BY [System.CreatedDate] ASC', query)

    def test_assignees_only(self):
        # given
        builder = AzureSearchQueryBuilder(assignees=['John Doe', 'Jane'])
        # when
        query = builder.build_query()
        # then
        expected = "SELECT [System.Id] FROM workitems WHERE [System.AssignedTo] IN ('John Doe', 'Jane')"
        self.assertEqual(expected, query)


    def test_assignees_history_only(self):
        # given
        builder = AzureSearchQueryBuilder()
        builder.with_assignees_history(['John'])
        # when
        query = builder.build_query()
        # then
        expected = "SELECT [System.Id] FROM workitems WHERE (EVER ([System.AssignedTo] = 'John'))"
        self.assertEqual(expected, query)

    def test_assignees_history_with_project_and_order(self):
        # given
        builder = AzureSearchQueryBuilder(projects=['Proj1'], order_by='[System.ChangedDate] DESC')
        builder.with_assignees_history(['John', 'Jane'])
        # when
        query = builder.build_query()
        # then
        expected = (
            "SELECT [System.Id] FROM workitems WHERE "
            "[System.TeamProject] IN ('Proj1') AND (EVER ([System.AssignedTo] = 'John') OR EVER ([System.AssignedTo] = 'Jane')) "
            "ORDER BY [System.ChangedDate] DESC"
        )
        self.assertEqual(expected, query)


if __name__ == '__main__':
    unittest.main()
