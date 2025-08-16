from abc import ABC, abstractmethod
from typing import Callable, Optional, TypeVar

from sd_metrics_lib.utils.attributes import get_attribute_by_path

T = TypeVar('T')


class StoryPointExtractor(ABC):

    @abstractmethod
    def get_story_points(self, task) -> float | None:
        pass


class ConstantStoryPointExtractor(StoryPointExtractor):

    def __init__(self, story_point_amount=1):
        self.value = story_point_amount

    def get_story_points(self, task) -> float | None:
        return self.value


class FunctionStoryPointExtractor(StoryPointExtractor):

    def __init__(self, func: Callable[[T], Optional[float]]):
        self.func = func

    def get_story_points(self, task: T) -> float | None:
        return self.func(task)


class AttributePathStoryPointExtractor(StoryPointExtractor):

    def __init__(self, attr_path: str, default: Optional[float] = None):
        self._path = attr_path
        self._default = default

    def get_story_points(self, task) -> float | None:
        value = get_attribute_by_path(task, self._path, self._default)
        if value is None:
            return None
        try:
            return float(value)
        except Exception:
            return self._default
