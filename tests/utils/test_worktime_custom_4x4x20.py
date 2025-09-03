import unittest
from datetime import datetime, timezone

from sd_metrics_lib.utils.worktime import SimpleWorkTimeExtractor
from sd_metrics_lib.utils.time import TimePolicy, TimeUnit, Duration


class TestSimpleWorkTimeExtractorCustomPolicy4x4x20(unittest.TestCase):
    def setUp(self):
        self.ext = SimpleWorkTimeExtractor()
        self.policy = TimePolicy(hours_per_day=4, days_per_week=4, days_per_month=20)
        self.start_mon_9 = datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc)

    def test_intraday_caps_to_4_hours(self):
        end_same_day_18 = datetime(2024, 1, 1, 18, 0, tzinfo=timezone.utc)
        d = self.ext.extract_time_from_period(self.start_mon_9, end_same_day_18, time_policy=self.policy, result_unit=TimeUnit.HOUR)
        self.assertIsNotNone(d)
        self.assertEqual(d.time_unit, TimeUnit.HOUR)
        self.assertAlmostEqual(d.time_delta, 4.0, delta=1e-6)

    def test_multiday_counts_4_workdays_only(self):
        end_next_mon = datetime(2024, 1, 8, 10, 0, tzinfo=timezone.utc)
        d = self.ext.extract_time_from_period(self.start_mon_9, end_next_mon, time_policy=self.policy, result_unit=TimeUnit.DAY)
        self.assertIsNotNone(d)
        self.assertGreaterEqual(d.time_delta, 4.0)
        self.assertLessEqual(d.time_delta, 5.0)

    def test_month_conversion_uses_20_days(self):
        one_month_in_days = Duration.of(1, TimeUnit.MONTH).convert(TimeUnit.DAY, self.policy)
        self.assertAlmostEqual(one_month_in_days.time_delta, 20.0, delta=1e-6)


if __name__ == '__main__':
    unittest.main()
