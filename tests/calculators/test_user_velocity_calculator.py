import unittest

from sd_metrics_lib.calculators.velocity import UserVelocityCalculator
from sd_metrics_lib.sources.jira.story_points import JiraCustomFieldStoryPointExtractor
from sd_metrics_lib.sources.jira.worklog import JiraStatusChangeWorklogExtractor
from sd_metrics_lib.sources.tasks import ProxyTaskProvider

TEST_USER = 'test_user'


class VelocityCalculatorTestCase(unittest.TestCase):

    def test_should_not_fail_on_empty_jira_task(self):
        # given
        empty_task = {}
        task_provider = ProxyTaskProvider([empty_task])
        t_shirt_story_point_extractor = JiraCustomFieldStoryPointExtractor('customfield_00000')
        jira_worklog_extractor = JiraStatusChangeWorklogExtractor(['12207'],
                                                                  time_format='%Y-%m-%dT%H:%M:%S.%f%z')
        # when
        self.velocity_calculator = UserVelocityCalculator(task_provider=task_provider,
                                                          story_point_extractor=t_shirt_story_point_extractor,
                                                          worklog_extractor=jira_worklog_extractor)

        velocity = self.velocity_calculator.calculate()

        # then
        self.assertEqual(0, len(velocity.keys()), 'Empty task must not provide any velocity data')

    def test_should_calculate_velocity_for_one_worklog(self):
        # given
        histories = self.__create_history_entries_with_status_change()
        task = self.__create_task_with_log_data(histories)

        task_provider = ProxyTaskProvider([task])
        t_shirt_story_point_extractor = JiraCustomFieldStoryPointExtractor('customfield_00000')
        jira_worklog_extractor = JiraStatusChangeWorklogExtractor(['12207'],
                                                                  time_format='%Y-%m-%dT%H:%M:%S.%f%z',
                                                                  use_status_codes=True)

        # when
        self.velocity_calculator = UserVelocityCalculator(task_provider=task_provider,
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
        task = self.__create_task_with_log_data(histories)

        task_provider = ProxyTaskProvider([task])
        t_shirt_story_point_extractor = JiraCustomFieldStoryPointExtractor('customfield_00000')
        jira_worklog_extractor = JiraStatusChangeWorklogExtractor(['12207'],
                                                                  time_format='%Y-%m-%dT%H:%M:%S.%f%z',
                                                                  use_status_codes=True)

        # when
        self.velocity_calculator = UserVelocityCalculator(task_provider=task_provider,
                                                          story_point_extractor=t_shirt_story_point_extractor,
                                                          worklog_extractor=jira_worklog_extractor)

        velocity = self.velocity_calculator.calculate()

        # then
        self.assertEqual(1, len(velocity.keys()), 'Missing calculated velocity data')
        self.assertEqual(12, velocity[TEST_USER], 'Must be calculated velocity for test user')

    def test_should_calculate_velocity_for_few_tasks(self):
        # given
        task = self.__create_task_with_log_data(self.__create_history_entries_with_status_change())
        task2 = self.__create_task_with_log_data(self.__create_history_entries_with_status_change(), story_points=2)

        task_provider = ProxyTaskProvider([task, task2])
        t_shirt_story_point_extractor = JiraCustomFieldStoryPointExtractor('customfield_00000')
        jira_worklog_extractor = JiraStatusChangeWorklogExtractor(['12207'],
                                                                  time_format='%Y-%m-%dT%H:%M:%S.%f%z',
                                                                  use_status_codes=True)

        # when
        self.velocity_calculator = UserVelocityCalculator(task_provider=task_provider,
                                                          story_point_extractor=t_shirt_story_point_extractor,
                                                          worklog_extractor=jira_worklog_extractor)

        velocity = self.velocity_calculator.calculate()

        # then
        self.assertEqual(1, len(velocity.keys()), 'Missing calculated velocity data')
        self.assertEqual(20, velocity[TEST_USER], 'Must be calculated velocity for test user')

    @staticmethod
    def __create_task_with_log_data(histories, story_points=3):
        task = {}
        task['fields'] = {}
        task['fields']['customfield_00000'] = story_points
        task['changelog'] = {}
        task['changelog']['histories'] = histories
        return task

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
