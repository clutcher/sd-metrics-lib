from typing import Optional

from sd_metrics_lib.sources.story_points import StoryPointExtractor


class AzureStoryPointExtractor(StoryPointExtractor):

    def __init__(self, field_name: str = 'Microsoft.VSTS.Scheduling.StoryPoints',
                 default_story_points_value: Optional[float] = None) -> None:
        self.field_name = field_name
        self.default_value = default_story_points_value

    def get_story_points(self, task) -> float | None:
        value = self._extract_field_value(task)
        if isinstance(value, (int, float)):
            return float(value)
        if value is None:
            return self.default_value
        try:
            return float(str(value))
        except Exception:
            return self.default_value

    def _extract_field_value(self, task):
        return task.fields.get(self.field_name)