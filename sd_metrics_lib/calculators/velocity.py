from abc import ABC, abstractmethod
from typing import Dict

from sd_metrics_lib.calculators.metrics import MetricCalculator
from sd_metrics_lib.utils.enums import VelocityTimeUnit
from sd_metrics_lib.utils import time as timeutil
from sd_metrics_lib.sources.story_points import StoryPointExtractor
from sd_metrics_lib.sources.tasks import TaskProvider
from sd_metrics_lib.sources.worklog import WorklogExtractor, TaskTotalSpentTimeExtractor


class AbstractMetricCalculator(MetricCalculator, ABC):

    def __init__(self) -> None:
        self.data_fetched = False

    def calculate(self, velocity_time_unit=VelocityTimeUnit.DAY) -> Dict[str, float]:
        if not self.is_data_fetched():
            self._extract_data_from_tasks()
            self.mark_data_fetched()
        self._calculate_metric(velocity_time_unit)
        return self.get_metric()

    def mark_data_fetched(self):
        self.data_fetched = True

    def is_data_fetched(self):
        return self.data_fetched is True

    @abstractmethod
    def _calculate_metric(self, time_unit: VelocityTimeUnit):
        pass

    @abstractmethod
    def _extract_data_from_tasks(self):
        pass

    @abstractmethod
    def get_metric(self):
        pass


class UserVelocityCalculator(AbstractMetricCalculator):

    def __init__(self, task_provider: TaskProvider,
                 story_point_extractor: StoryPointExtractor,
                 worklog_extractor: WorklogExtractor) -> None:
        super().__init__()
        self.task_provider = task_provider
        self.story_point_extractor = story_point_extractor
        self.worklog_extractor = worklog_extractor

        self.velocity_per_user = {}
        self.resolved_story_points_per_user = {}
        self.time_in_seconds_spent_per_user = {}

    def _calculate_metric(self, time_unit: VelocityTimeUnit):
        for user in self.resolved_story_points_per_user:
            spent_time_in_seconds = self.time_in_seconds_spent_per_user[user]
            if spent_time_in_seconds != 0:
                spent_time = timeutil.convert_time(spent_time_in_seconds, time_unit)
                developer_velocity = self.resolved_story_points_per_user[user] / spent_time
                if developer_velocity != 0:
                    self.velocity_per_user[user] = developer_velocity

    def _extract_data_from_tasks(self):
        tasks = self.task_provider.get_tasks()
        for task in tasks:
            task_story_points = self.story_point_extractor.get_story_points(task)
            if task_story_points is not None and task_story_points > 0:
                time_user_worked_on_task = self.worklog_extractor.get_work_time_per_user(task)

                self._sum_story_points_and_worklog(task_story_points, time_user_worked_on_task)

    def get_metric(self):
        return self.velocity_per_user

    def get_story_points(self):
        return self.resolved_story_points_per_user

    def get_spent_time(self):
        return self.time_in_seconds_spent_per_user

    def _sum_story_points_and_worklog(self, task_story_points, time_user_worked_on_task):
        task_total_spent_time = float(sum(time_user_worked_on_task.values()))
        if task_total_spent_time == 0:
            return

        for user in time_user_worked_on_task.keys():
            if user not in self.resolved_story_points_per_user:
                self.resolved_story_points_per_user[user] = 0.
            if user not in self.time_in_seconds_spent_per_user:
                self.time_in_seconds_spent_per_user[user] = 0

        for user in time_user_worked_on_task.keys():
            story_point_ratio = time_user_worked_on_task[user] / task_total_spent_time
            self.resolved_story_points_per_user[user] += task_story_points * story_point_ratio
            self.time_in_seconds_spent_per_user[user] += time_user_worked_on_task[user]


class GeneralizedTeamVelocityCalculator(AbstractMetricCalculator):

    def __init__(self, task_provider: TaskProvider,
                 story_point_extractor: StoryPointExtractor,
                 time_extractor: TaskTotalSpentTimeExtractor) -> None:
        super().__init__()
        self.total_resolved_story_points = 0
        self.total_spent_time_in_seconds = 0
        self.velocity = None

        self.task_provider = task_provider
        self.story_point_extractor = story_point_extractor
        self.time_extractor = time_extractor

    def _calculate_metric(self, time_unit: VelocityTimeUnit):
        spent_time = timeutil.convert_time(self.total_spent_time_in_seconds, time_unit)
        story_points = self.total_resolved_story_points

        if spent_time == 0:
            self.velocity = 0
        else:
            self.velocity = story_points / spent_time

    def _extract_data_from_tasks(self):
        tasks = self.task_provider.get_tasks()
        for task in tasks:
            task_story_points = self.story_point_extractor.get_story_points(task)
            if task_story_points is not None and task_story_points > 0:
                time_spent_on_task = self.time_extractor.get_total_spent_time(task)

                self._sum_story_points_and_worklog(task_story_points, time_spent_on_task)

    def get_metric(self):
        return self.velocity

    def get_story_points(self):
        return self.total_resolved_story_points

    def get_spent_time(self):
        return self.total_spent_time_in_seconds

    def _sum_story_points_and_worklog(self, task_story_points: float, task_total_spent_time: int):
        if task_total_spent_time == 0:
            return

        self.total_resolved_story_points += task_story_points
        self.total_spent_time_in_seconds += task_total_spent_time
