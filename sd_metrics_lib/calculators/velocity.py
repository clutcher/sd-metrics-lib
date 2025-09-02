from abc import ABC, abstractmethod
from typing import Dict

from sd_metrics_lib.calculators.metrics import MetricCalculator
from sd_metrics_lib.utils.time import TimeUnit, Duration, TimePolicy
from sd_metrics_lib.sources.story_points import StoryPointExtractor
from sd_metrics_lib.sources.tasks import TaskProvider
from sd_metrics_lib.sources.worklog import WorklogExtractor, TaskTotalSpentTimeExtractor


class AbstractMetricCalculator(MetricCalculator, ABC):

    def __init__(self) -> None:
        self.data_fetched = False

    def calculate(self, velocity_time_unit: TimeUnit = TimeUnit.DAY, time_policy: TimePolicy | None = None) -> Dict[str, float]:
        policy_used = time_policy or TimePolicy.BUSINESS_HOURS
        if not self.is_data_fetched():
            self._extract_data_from_tasks()
            self.mark_data_fetched()
        self._calculate_metric(velocity_time_unit, time_policy=policy_used)
        return self.get_metric()

    def mark_data_fetched(self):
        self.data_fetched = True

    def is_data_fetched(self):
        return self.data_fetched is True

    @abstractmethod
    def _calculate_metric(self, time_unit: TimeUnit, time_policy: TimePolicy):
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
        self.spent_time_per_user: Dict[str, Duration] = {}

    def _calculate_metric(self, time_unit: TimeUnit, time_policy: TimePolicy):
        for user in self.resolved_story_points_per_user:
            spent_duration = self.spent_time_per_user.get(user)
            if spent_duration and not spent_duration.is_zero():
                spent_time_in_unit = spent_duration.convert(time_unit, time_policy).time_delta
                developer_velocity = self.resolved_story_points_per_user[user] / spent_time_in_unit
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
        return self.spent_time_per_user

    def _sum_story_points_and_worklog(self, task_story_points, time_user_worked_on_task: Dict[str, Duration]):
        total_spent_time_on_task = Duration.sum(list(time_user_worked_on_task.values()), unit=TimeUnit.SECOND)
        if total_spent_time_on_task.is_zero():
            return

        for user in time_user_worked_on_task.keys():
            if user not in self.resolved_story_points_per_user:
                self.resolved_story_points_per_user[user] = 0.0
            if user not in self.spent_time_per_user:
                self.spent_time_per_user[user] = Duration.zero()

        for user, user_spent_time_on_task in time_user_worked_on_task.items():
            story_point_ratio = user_spent_time_on_task.convert(TimeUnit.SECOND).time_delta / total_spent_time_on_task.time_delta
            self.resolved_story_points_per_user[user] += task_story_points * story_point_ratio
            self.spent_time_per_user[user] = self.spent_time_per_user[user].add(user_spent_time_on_task, unit=TimeUnit.SECOND)


class GeneralizedTeamVelocityCalculator(AbstractMetricCalculator):

    def __init__(self, task_provider: TaskProvider,
                 story_point_extractor: StoryPointExtractor,
                 time_extractor: TaskTotalSpentTimeExtractor) -> None:
        super().__init__()
        self.total_resolved_story_points = 0.0
        self.total_spent_time: Duration = Duration.zero()
        self.velocity = None

        self.task_provider = task_provider
        self.story_point_extractor = story_point_extractor
        self.time_extractor = time_extractor

    def _calculate_metric(self, time_unit: TimeUnit, time_policy: TimePolicy):
        spent_time = self.total_spent_time.convert(time_unit, time_policy).time_delta
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
        return self.total_spent_time

    def _sum_story_points_and_worklog(self, task_story_points: float, task_total_spent_time: Duration):
        if not task_total_spent_time or task_total_spent_time.is_zero():
            return

        self.total_resolved_story_points += task_story_points
        self.total_spent_time = self.total_spent_time.add(task_total_spent_time, unit=TimeUnit.SECOND)
