from typing import Optional

from sd_metrics_lib.utils.time import Duration


class ProportionalStoryPointCalculator:

    @staticmethod
    def calculate(
        story_points: Optional[float],
        developer_time: Optional[Duration],
        total_time: Optional[Duration]
    ) -> Optional[float]:
        if story_points is None:
            return None
        if developer_time is None or total_time is None:
            return None
        if total_time.is_zero():
            return None

        ratio = developer_time.time_delta / total_time.time_delta
        return story_points * ratio
