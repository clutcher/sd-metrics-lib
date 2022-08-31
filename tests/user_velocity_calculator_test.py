import unittest

from src.calculators import UserVelocityCalculator
from src.data_providers.issue_provider import ProxyIssueProvider
from src.data_providers.jira import JiraCustomFieldStoryPointExtractor, JiraStatusChangeWorklogExtractor

TEST_USER = 'test_user'


class VelocityCalculatorTestCase(unittest.TestCase):

    def test_should_not_fail_on_empty_jira_issue(self):
        # given
        empty_issue = {}
        jql_issue_provider = ProxyIssueProvider([empty_issue])
        t_shirt_story_point_extractor = JiraCustomFieldStoryPointExtractor('customfield_00000')
        jira_worklog_extractor = JiraStatusChangeWorklogExtractor(['12207'],
                                                                  time_format='%Y-%m-%dT%H:%M:%S.%f%z')
        # when
        self.velocity_calculator = UserVelocityCalculator(issue_provider=jql_issue_provider,
                                                          story_point_extractor=t_shirt_story_point_extractor,
                                                          worklog_extractor=jira_worklog_extractor)

        velocity = self.velocity_calculator.calculate()

        # then
        self.assertEqual(0, len(velocity.keys()), 'Empty issue must not provide any velocity data')

    def test_should_calculate_velocity_for_one_worklog(self):
        # given
        histories = self.__create_history_entries_with_status_change()
        issue = self.__create_issue_with_log_data(histories)

        jql_issue_provider = ProxyIssueProvider([issue])
        t_shirt_story_point_extractor = JiraCustomFieldStoryPointExtractor('customfield_00000')
        jira_worklog_extractor = JiraStatusChangeWorklogExtractor(['12207'],
                                                                  time_format='%Y-%m-%dT%H:%M:%S.%f%z')

        # when
        self.velocity_calculator = UserVelocityCalculator(issue_provider=jql_issue_provider,
                                                          story_point_extractor=t_shirt_story_point_extractor,
                                                          worklog_extractor=jira_worklog_extractor)

        velocity = self.velocity_calculator.calculate()

        # then
        self.assertEqual(1, len(velocity.keys()), 'Missing calculated velocity data')
        self.assertEqual(24, velocity[TEST_USER], 'Must be calculated velocity for test user')

    def test_should_calculate_velocity_for_few_worklogs(self):
        # given
        histories = self.__create_history_entries_with_status_change()
        histories.extend(self.__create_history_entries_with_status_change())
        issue = self.__create_issue_with_log_data(histories)

        jql_issue_provider = ProxyIssueProvider([issue])
        t_shirt_story_point_extractor = JiraCustomFieldStoryPointExtractor('customfield_00000')
        jira_worklog_extractor = JiraStatusChangeWorklogExtractor(['12207'],
                                                                  time_format='%Y-%m-%dT%H:%M:%S.%f%z')

        # when
        self.velocity_calculator = UserVelocityCalculator(issue_provider=jql_issue_provider,
                                                          story_point_extractor=t_shirt_story_point_extractor,
                                                          worklog_extractor=jira_worklog_extractor)

        velocity = self.velocity_calculator.calculate()

        # then
        self.assertEqual(1, len(velocity.keys()), 'Missing calculated velocity data')
        self.assertEqual(12, velocity[TEST_USER], 'Must be calculated velocity for test user')

    def test_should_calculate_velocity_for_few_issues(self):
        # given
        issue = self.__create_issue_with_log_data(self.__create_history_entries_with_status_change())
        issue2 = self.__create_issue_with_log_data(self.__create_history_entries_with_status_change(), story_points=2)

        jql_issue_provider = ProxyIssueProvider([issue, issue2])
        t_shirt_story_point_extractor = JiraCustomFieldStoryPointExtractor('customfield_00000')
        jira_worklog_extractor = JiraStatusChangeWorklogExtractor(['12207'],
                                                                  time_format='%Y-%m-%dT%H:%M:%S.%f%z')

        # when
        self.velocity_calculator = UserVelocityCalculator(issue_provider=jql_issue_provider,
                                                          story_point_extractor=t_shirt_story_point_extractor,
                                                          worklog_extractor=jira_worklog_extractor)

        velocity = self.velocity_calculator.calculate()

        # then
        self.assertEqual(1, len(velocity.keys()), 'Missing calculated velocity data')
        self.assertEqual(20, velocity[TEST_USER], 'Must be calculated velocity for test user')

    def __create_issue_with_log_data(self, histories, story_points=3):
        issue = {}
        issue['fields'] = {}
        issue['fields']['customfield_00000'] = story_points
        issue['changelog'] = {}
        issue['changelog']['histories'] = histories
        return issue

    def __create_history_entries_with_status_change(self):
        end_date_history_entry_item = self.__create_status_change_history_entry_item(to_status='1',
                                                                                     from_status='12207')
        history_entry_end_date = {}
        history_entry_end_date['items'] = [end_date_history_entry_item]
        history_entry_end_date['created'] = '2022-02-01T11:00:00.000-0500'

        start_date_history_entry_item = self.__create_status_change_history_entry_item(to_status='12207',
                                                                                       from_status='1')
        assignee_change_history_entry_item = self.__create_assignee_change_history_entry_item()
        history_entry_start_date = {}
        history_entry_start_date['items'] = [start_date_history_entry_item, assignee_change_history_entry_item]
        history_entry_start_date['created'] = '2022-02-01T10:00:00.000-0500'
        histories = [history_entry_end_date, history_entry_start_date]
        return histories

    @staticmethod
    def __create_status_change_history_entry_item(to_status, from_status):
        return {'items': {}, 'fieldId': 'status', 'to': to_status, 'from': from_status}

    @staticmethod
    def __create_assignee_change_history_entry_item():
        return {'fieldId': 'assignee', 'to': TEST_USER, 'toString': TEST_USER}


if __name__ == '__main__':
    unittest.main()
