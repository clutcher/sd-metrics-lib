from typing import Dict

from sd_metrics_lib.sources.story_points import StoryPointExtractor


class JiraCustomFieldStoryPointExtractor(StoryPointExtractor):

    def __init__(self, custom_field_name, default_story_points_value=None) -> None:
        self.custom_field_name = custom_field_name
        self.default_value = default_story_points_value

    def get_story_points(self, task) -> float | None:
        story_points = self._extract_field_value(task)

        if isinstance(story_points, int) or isinstance(story_points, float):
            return story_points
        if story_points is None:
            return self.default_value
        if story_points.isdigit():
            return int(story_points)

        return self.default_value

    def _extract_field_value(self, task):
        try:
            return task['fields'][self.custom_field_name]
        except:
            return None


class JiraTShirtStoryPointExtractor(JiraCustomFieldStoryPointExtractor):

    def __init__(self, custom_field_name, story_point_mapping: Dict[str, int], default_story_points_value=0) -> None:
        super().__init__(custom_field_name, default_story_points_value)
        self.story_point_mapping = story_point_mapping

    def get_story_points(self, task) -> float | None:
        story_points = self._extract_field_value(task)
        if isinstance(story_points, int) or isinstance(story_points, float):
            return story_points
        if story_points is None:
            return self.default_value
        if story_points.isdigit():
            return int(story_points)

        story_points_lower = story_points.lower()
        return self.story_point_mapping.get(story_points_lower, self.default_value)
