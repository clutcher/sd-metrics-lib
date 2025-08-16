from abc import ABC, abstractmethod
from typing import Dict, Callable, Optional

from sd_metrics_lib.utils.attributes import get_attribute_by_path


class WorklogExtractor(ABC):

    @abstractmethod
    def get_work_time_per_user(self, task) -> Dict[str, int]:
        pass


class TaskTotalSpentTimeExtractor(ABC):

    @abstractmethod
    def get_total_spent_time(self, task) -> int:
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

    def __init__(self, func: Callable[[object], Optional[Dict[str, int]]]):
        self.func = func

    def get_work_time_per_user(self, task) -> Dict[str, int]:
        result = self.func(task)
        try:
            return {str(k): int(v) for k, v in (result or {}).items()}
        except Exception:
            return {}


class FunctionTotalSpentTimeExtractor(TaskTotalSpentTimeExtractor):

    def __init__(self, func: Callable[[object], Optional[int]]):
        self.func = func

    def get_total_spent_time(self, task) -> int:
        result = self.func(task)
        try:
            return int(result) if result is not None else 0
        except Exception:
            return 0


class AttributePathWorklogExtractor(WorklogExtractor):

    def __init__(self, attr_path: str):
        self._path = attr_path

    def get_work_time_per_user(self, task) -> Dict[str, int]:
        value = get_attribute_by_path(task, self._path, {})
        if isinstance(value, dict):
            try:
                return {str(k): int(v) for k, v in value.items()}
            except Exception:
                return {}
        return {}


class AttributePathTotalSpentTimeExtractor(TaskTotalSpentTimeExtractor):

    def __init__(self, attr_path: str, default: int = 0):
        self._path = attr_path
        self._default = default

    def get_total_spent_time(self, task) -> int:
        value = get_attribute_by_path(task, self._path, self._default)
        try:
            return int(value) if value is not None else self._default
        except Exception:
            return self._default
