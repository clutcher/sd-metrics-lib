from abc import ABC, abstractmethod


class StoryPointExtractor(ABC):

    @abstractmethod
    def get_story_points(self, task) -> float | None:
        pass


class ConstantStoryPointExtractor(StoryPointExtractor):

    def __init__(self, story_point_amount=1):
        self.value = story_point_amount

    def get_story_points(self, task) -> float | None:
        return self.value
