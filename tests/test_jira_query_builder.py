import datetime
import unittest

from data_providers.jira.query_builder import JiraSearchQueryBuilder


class JiraSearchQueryBuilderTestCase(unittest.TestCase):

    def test_empty_builder_returns_empty_string(self):
        # given
        builder = JiraSearchQueryBuilder()
        # when
        query = builder.build_query()
        # then
        self.assertEqual('', query)

    def test_full_query_build_with_all_filters_and_order_by(self):
        # given
        builder = JiraSearchQueryBuilder(
            projects=['PRJ'],
            statuses=['In Progress', 'Done'],
            task_types=['Story', 'Bug'],
            teams=['Team A', 'Team B'],
            resolution_dates=(datetime.date(2022, 1, 1), datetime.date(2022, 1, 31)),
            last_modified_dates=(None, datetime.date(2022, 2, 1)),
            raw_queries=['assignee = currentUser()', 'priority = High', '   ', None],
            order_by='updated DESC'
        )
        # when
        query = builder.build_query()
        # then
        expected = (
            "project IN (PRJ)"
            " AND status in (\"In Progress\", \"Done\")"
            " AND resolutiondate >= '2022-01-01' and resolutiondate <= '2022-01-31'"
            " AND issuetype in (\"Story\", \"Bug\")"
            " AND Team[Team] in (\"Team A\", \"Team B\")"
            " AND updated <= '2022-02-01'"
            " AND assignee = currentUser()"
            " AND priority = High"
            " ORDER BY updated DESC"
        )
        self.assertEqual(expected, query)

    def test_order_by_only_returns_only_order_by(self):
        # given
        builder = JiraSearchQueryBuilder(order_by='created ASC')
        # when
        query = builder.build_query()
        # then
        self.assertEqual('ORDER BY created ASC', query)


if __name__ == '__main__':
    unittest.main()
