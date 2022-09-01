from typing import Dict

from data_providers import WorklogExtractor
from data_providers.issue_provider import IssueProvider
from data_providers.story_point_extractor import StoryPointExtractor
from data_providers.utils import VelocityTimeUnit

SECONDS_IN_HOUR = 3600
WORKING_HOURS_PER_DAY = 8
WORKING_DAYS_PER_WEEK = 5
WORKING_WEEKS_IN_MONTH = 4


class UserVelocityCalculator:

    def __init__(self, issue_provider: IssueProvider,
                 story_point_extractor: StoryPointExtractor,
                 worklog_extractor: WorklogExtractor) -> None:

        self.issue_provider = issue_provider
        self.story_point_extractor = story_point_extractor
        self.worklog_extractor = worklog_extractor

        self.velocity_per_user = {}
        self.resolved_story_points_per_user = {}
        self.time_in_seconds_spent_per_user = {}

    def calculate(self, velocity_time_unit=VelocityTimeUnit.DAY) -> Dict[str, float]:
        self._extract_data_from_issues()
        self._calculate_velocity(velocity_time_unit)
        return self.velocity_per_user

    def _extract_data_from_issues(self):
        issues = self.issue_provider.get_issues()
        for issue in issues:
            issue_story_points = self.story_point_extractor.get_story_points(issue)
            if issue_story_points is not None and issue_story_points > 0:
                time_user_worked_on_issue = self.worklog_extractor.get_work_time_per_user(issue)

                self._sum_story_points_and_worklog(issue_story_points, time_user_worked_on_issue)

    def _sum_story_points_and_worklog(self, issue_story_points, time_user_worked_on_issue):
        issue_total_spent_time = float(sum(time_user_worked_on_issue.values()))
        if issue_total_spent_time == 0:
            return

        for user in time_user_worked_on_issue.keys():
            if user not in self.resolved_story_points_per_user:
                self.resolved_story_points_per_user[user] = 0.
            if user not in self.time_in_seconds_spent_per_user:
                self.time_in_seconds_spent_per_user[user] = 0

        for user in time_user_worked_on_issue.keys():
            story_point_ratio = time_user_worked_on_issue[user] / issue_total_spent_time
            self.resolved_story_points_per_user[user] += issue_story_points * story_point_ratio
            self.time_in_seconds_spent_per_user[user] += time_user_worked_on_issue[user]

    def _calculate_velocity(self, time_unit: VelocityTimeUnit):
        for user in self.resolved_story_points_per_user:
            spent_time_in_seconds = self.time_in_seconds_spent_per_user[user]
            if spent_time_in_seconds != 0:
                spent_time = self._convert_spent_time(spent_time_in_seconds, time_unit)
                developer_velocity = self.resolved_story_points_per_user[user] / spent_time
                if developer_velocity != 0:
                    self.velocity_per_user[user] = developer_velocity

    @staticmethod
    def _convert_spent_time(spent_time_in_seconds: int, time_unit: VelocityTimeUnit):
        if time_unit == VelocityTimeUnit.HOUR:
            return spent_time_in_seconds / SECONDS_IN_HOUR
        elif time_unit == VelocityTimeUnit.DAY:
            return spent_time_in_seconds / SECONDS_IN_HOUR / WORKING_HOURS_PER_DAY
        elif time_unit == VelocityTimeUnit.WEEK:
            return spent_time_in_seconds / SECONDS_IN_HOUR / WORKING_HOURS_PER_DAY / WORKING_DAYS_PER_WEEK
        elif time_unit == VelocityTimeUnit.MONTH:
            return spent_time_in_seconds / SECONDS_IN_HOUR / WORKING_HOURS_PER_DAY / WORKING_DAYS_PER_WEEK / WORKING_WEEKS_IN_MONTH
        else:
            return spent_time_in_seconds
