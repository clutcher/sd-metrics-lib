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

    def test_mixed_items_and_user_only_change(self):
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

        task = {
            'fields': {'status': {'id': '1', 'name': 'Done'}},
            'changelog': {'histories': histories}
        }

        extractor = JiraStatusChangeWorklogExtractor(['12207'], use_status_codes=True,
                                                      time_format='%Y-%m-%dT%H:%M:%S.%f%z')
        per_user = extractor.get_work_time_per_user(task)

        # Expect 2 hours for userA (10:00 -> 12:00) and 2 hours for userB (12:00 -> 14:00)
        self.assertIn('userA', per_user)
        self.assertIn('userB', per_user)
        self.assertIsInstance(per_user['userA'], Duration)
        self.assertIsInstance(per_user['userB'], Duration)

        userA_seconds = per_user['userA'].to_seconds()
        userB_seconds = per_user['userB'].to_seconds()
        self.assertAlmostEqual(userA_seconds, 2 * 3600, delta=60)
        self.assertAlmostEqual(userB_seconds, 2 * 3600, delta=60)


if __name__ == '__main__':
    unittest.main()
