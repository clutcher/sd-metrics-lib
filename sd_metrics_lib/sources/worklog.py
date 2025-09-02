from abc import ABC, abstractmethod
from typing import Dict, Callable, Optional, TypeVar

from sd_metrics_lib.utils.time import Duration, TimeUnit

from sd_metrics_lib.utils.attributes import get_attribute_by_path

T = TypeVar('T')


class WorklogExtractor(ABC):

    @abstractmethod
    def get_work_time_per_user(self, task) -> Dict[str, 'Duration']:
        pass


class TaskTotalSpentTimeExtractor(ABC):

    @abstractmethod
    def get_total_spent_time(self, task) -> 'Duration':
        pass


class ChainedWorklogExtractor(WorklogExtractor):

    def __init__(self, worklog_extractor_list: list[WorklogExtractor]) -> None:
        self.worklog_extractor_list = worklog_extractor_list

    def get_work_time_per_user(self, task):
        for worklog_extractor in self.worklog_extractor_list:
            work_time = worklog_extractor.get_work_time_per_user(task)
            if work_time is not None and len(work_time.keys()) != 0:
                return work_time
        return {}


class FunctionWorklogExtractor(WorklogExtractor):

    def __init__(self, func: Callable[[T], Optional[Dict[str, Duration]]]):
        self.func = func

    def get_work_time_per_user(self, task: T) -> Dict[str, Duration]:
        result = self.func(task)
        try:
            return {str(k): v for k, v in (result or {}).items()}
        except Exception:
            return {}


class FunctionTotalSpentTimeExtractor(TaskTotalSpentTimeExtractor):

    def __init__(self, func: Callable[[T], Optional[Duration]]):
        self.func = func

    def get_total_spent_time(self, task: T) -> Duration:
        result = self.func(task)
        try:
            return result if isinstance(result, Duration) else Duration.zero()
        except Exception:
            return Duration.zero()


class AttributePathWorklogExtractor(WorklogExtractor):

    def __init__(self, attr_path: str):
        self._path = attr_path

    def get_work_time_per_user(self, task) -> Dict[str, Duration]:
        value = get_attribute_by_path(task, self._path, {})
        if isinstance(value, dict):
            try:
                return {str(k): v for k, v in value.items()}
            except Exception:
                return {}
        return {}


class AttributePathTotalSpentTimeExtractor(TaskTotalSpentTimeExtractor):

    def __init__(self, attr_path: str, default_seconds: float = 0):
        self._path = attr_path
        self._default = Duration.of(default_seconds, TimeUnit.SECOND)

    def get_total_spent_time(self, task) -> Duration:
        value = get_attribute_by_path(task, self._path, self._default)
        try:
            return value if isinstance(value, Duration) else self._default
        except Exception:
            return self._default
