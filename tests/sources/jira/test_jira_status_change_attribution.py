import unittest
from datetime import datetime, timezone  # noqa: F401 (kept for consistency)

from sd_metrics_lib.sources.jira.worklog import JiraStatusChangeWorklogExtractor
from sd_metrics_lib.utils.time import Duration


class JiraStatusChangeAttributionTestCase(unittest.TestCase):

    @staticmethod
    def _history(created: str, items: list, author_account: str, author_name: str):
        return {
            'created': created,
            'author': {'accountId': author_account, 'displayName': author_name},
            'items': items,
        }

    @staticmethod
    def _status_item(to_: str, from_: str):
        return {'fieldId': 'status', 'to': to_, 'from': from_}

    @staticmethod
    def _assignee_item(to_: str, to_string: str):
        return {'fieldId': 'assignee', 'to': to_, 'toString': to_string}

    def _build_task_with_histories(self):
        # given: Jira returns newest-first histories
        histories = [
            self._history('2024-02-01T14:00:00.000+0000', [self._status_item('1', '12207')], 'userB', 'User B'),
            self._history('2024-02-01T12:00:00.000+0000', [self._assignee_item('userB', 'User B')], 'userB', 'User B'),
            self._history(
                '2024-02-01T10:00:00.000+0000',
                [self._status_item('12207', '1'), self._assignee_item('userA', 'User A')],
                'userA', 'User A'
            ),
        ]
        return {
            'fields': {'status': {'id': '1', 'name': 'Done'}},
            'changelog': {'histories': histories}
        }

    def _extract_per_user(self):
        task = self._build_task_with_histories()
        extractor = JiraStatusChangeWorklogExtractor(['12207'], use_status_codes=True,
                                                      time_format='%Y-%m-%dT%H:%M:%S.%f%z')
        return extractor.get_work_time_per_user(task)

    def test_per_user_contains_userA(self):
        # when
        per_user = self._extract_per_user()
        # then
        self.assertIn('userA', per_user)

    def test_per_user_contains_userB(self):
        # when
        per_user = self._extract_per_user()
        # then
        self.assertIn('userB', per_user)

    def test_per_user_values_are_duration_instances_userA(self):
        # when
        per_user = self._extract_per_user()
        # then
        self.assertIsInstance(per_user['userA'], Duration)

    def test_per_user_values_are_duration_instances_userB(self):
        # when
        per_user = self._extract_per_user()
        # then
        self.assertIsInstance(per_user['userB'], Duration)

    def test_per_user_userA_value_is_two_hours(self):
        # when
        per_user = self._extract_per_user()
        # then
        userA_seconds = per_user['userA'].to_seconds()
        self.assertAlmostEqual(userA_seconds, 2 * 3600, delta=60)

    def test_per_user_userB_value_is_two_hours(self):
        # when
        per_user = self._extract_per_user()
        # then
        userB_seconds = per_user['userB'].to_seconds()
        self.assertAlmostEqual(userB_seconds, 2 * 3600, delta=60)


if __name__ == '__main__':
    unittest.main()
