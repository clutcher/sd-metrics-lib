import unittest

from sd_metrics_lib.calculators.story_points import ProportionalStoryPointCalculator
from sd_metrics_lib.utils.time import Duration, TimeUnit


class ProportionalStoryPointCalculatorTestCase(unittest.TestCase):

    def test_shouldCalculateProportionalStoryPointsWhenDeveloperWorkedHalfOfTotalTime(self):
        # Given
        story_points = 10.0
        developer_time = Duration.of(4, TimeUnit.HOUR)
        total_time = Duration.of(8, TimeUnit.HOUR)

        # When
        result = ProportionalStoryPointCalculator.calculate(story_points, developer_time, total_time)

        # Then
        self.assertEqual(5.0, result)

    def test_shouldCalculateProportionalStoryPointsWhenDeveloperWorkedAllTime(self):
        # Given
        story_points = 8.0
        developer_time = Duration.of(16, TimeUnit.HOUR)
        total_time = Duration.of(16, TimeUnit.HOUR)

        # When
        result = ProportionalStoryPointCalculator.calculate(story_points, developer_time, total_time)

        # Then
        self.assertEqual(8.0, result)

    def test_shouldCalculateProportionalStoryPointsWhenDeveloperWorkedSmallPortion(self):
        # Given
        story_points = 12.0
        developer_time = Duration.of(2, TimeUnit.HOUR)
        total_time = Duration.of(6, TimeUnit.HOUR)

        # When
        result = ProportionalStoryPointCalculator.calculate(story_points, developer_time, total_time)

        # Then
        self.assertAlmostEqual(4.0, result)

    def test_shouldReturnNoneWhenStoryPointsAreMissing(self):
        # Given
        developer_time = Duration.of(4, TimeUnit.HOUR)
        total_time = Duration.of(8, TimeUnit.HOUR)

        # When
        result = ProportionalStoryPointCalculator.calculate(None, developer_time, total_time)

        # Then
        self.assertIsNone(result)

    def test_shouldReturnNoneWhenDeveloperTimeIsMissing(self):
        # Given
        story_points = 10.0
        total_time = Duration.of(8, TimeUnit.HOUR)

        # When
        result = ProportionalStoryPointCalculator.calculate(story_points, None, total_time)

        # Then
        self.assertIsNone(result)

    def test_shouldReturnNoneWhenTotalTimeIsMissing(self):
        # Given
        story_points = 10.0
        developer_time = Duration.of(4, TimeUnit.HOUR)

        # When
        result = ProportionalStoryPointCalculator.calculate(story_points, developer_time, None)

        # Then
        self.assertIsNone(result)

    def test_shouldReturnNoneWhenTotalTimeIsZero(self):
        # Given
        story_points = 10.0
        developer_time = Duration.of(4, TimeUnit.HOUR)
        total_time = Duration.zero()

        # When
        result = ProportionalStoryPointCalculator.calculate(story_points, developer_time, total_time)

        # Then
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
