import unittest
from datetime import datetime, timezone, timedelta

from sd_metrics_lib.utils.worktime import SimpleWorkTimeExtractor
from sd_metrics_lib.utils.time import Duration, TimeUnit, TimePolicy


class TestSimpleWorkTimeExtractorPolicyAgnostic(unittest.TestCase):
    def setUp(self):
        self.ext = SimpleWorkTimeExtractor()
        self.start = datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc)
        self.end_same_day = datetime(2024, 1, 1, 18, 0, tzinfo=timezone.utc)
        self.end_next_day = datetime(2024, 1, 2, 18, 0, tzinfo=timezone.utc)

    def test_all_hours_returns_calendar_seconds(self):
        d = self.ext.extract_time_from_period(self.start, self.end_same_day, time_policy=TimePolicy.ALL_HOURS, result_unit=TimeUnit.SECOND)
        self.assertIsNotNone(d)
        self.assertEqual(d.time_unit, TimeUnit.SECOND)
        self.assertAlmostEqual(d.time_delta, (self.end_same_day - self.start).total_seconds(), delta=1)

    def test_business_hours_default_policy(self):
        d = self.ext.extract_time_from_period(self.start, self.end_same_day, time_policy=TimePolicy.BUSINESS_HOURS, result_unit=TimeUnit.HOUR)
        self.assertIsNotNone(d)
        self.assertEqual(d.time_unit, TimeUnit.HOUR)
        self.assertAlmostEqual(d.time_delta, 8.0, delta=1e-6)

    def test_custom_time_policy_hours_per_day_changes(self):
        # Create a custom business policy: 6 hours per day, 4 days per week
        custom = TimePolicy(hours_per_day=6, days_per_week=4, days_per_month=20)
        # Expect that ALL_HOURS branch is independent of custom policy
        d_all = self.ext.extract_time_from_period(self.start, self.end_same_day, time_policy=TimePolicy.ALL_HOURS, result_unit=TimeUnit.HOUR)
        self.assertAlmostEqual(d_all.time_delta, 9.0, delta=1e-6)
        d_business_sec = self.ext.extract_time_from_period(self.start, self.end_same_day, time_policy=TimePolicy.BUSINESS_HOURS, result_unit=TimeUnit.SECOND)
        converted_hours_custom = d_business_sec.convert(TimeUnit.HOUR, custom)
        self.assertAlmostEqual(converted_hours_custom.time_delta, 8.0, delta=1e-6)

    def test_multiday_counts_workdays_only(self):
        end = datetime(2024, 1, 5, 10, 0, tzinfo=timezone.utc)
        d = self.ext.extract_time_from_period(self.start, end, time_policy=TimePolicy.BUSINESS_HOURS, result_unit=TimeUnit.DAY)
        self.assertGreaterEqual(d.time_delta, 3.0)
        self.assertLessEqual(d.time_delta, 5.0)


if __name__ == '__main__':
    unittest.main()
