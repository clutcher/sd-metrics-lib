import unittest
from datetime import datetime, timezone

from sd_metrics_lib.utils.worktime import SimpleWorkTimeExtractor
from sd_metrics_lib.utils.time import TimePolicy, TimeUnit, Duration


class TestSimpleWorkTimeExtractorCustomPolicy4x4x20(unittest.TestCase):
    def setUp(self):
        self.ext = SimpleWorkTimeExtractor()
        self.policy = TimePolicy(hours_per_day=4, days_per_week=4, days_per_month=20)
        self.start_mon_9 = datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc)

    def test_intraday_caps_to_4_hours_not_none(self):
        # given
        end_same_day_18_utc = datetime(2024, 1, 1, 18, 0, tzinfo=timezone.utc)
        # when
        calculated_hours_duration = self.ext.extract_time_from_period(self.start_mon_9, end_same_day_18_utc, time_policy=self.policy, result_unit=TimeUnit.HOUR)
        # then
        self.assertIsNotNone(calculated_hours_duration)

    def test_intraday_caps_to_4_hours_unit_is_hour(self):
        # given
        end_same_day_18_utc = datetime(2024, 1, 1, 18, 0, tzinfo=timezone.utc)
        # when
        calculated_hours_duration = self.ext.extract_time_from_period(self.start_mon_9, end_same_day_18_utc, time_policy=self.policy, result_unit=TimeUnit.HOUR)
        # then
        assert calculated_hours_duration is not None
        self.assertEqual(calculated_hours_duration.time_unit, TimeUnit.HOUR)

    def test_intraday_caps_to_4_hours_value_is_four(self):
        # given
        end_same_day_18_utc = datetime(2024, 1, 1, 18, 0, tzinfo=timezone.utc)
        # when
        calculated_hours_duration = self.ext.extract_time_from_period(self.start_mon_9, end_same_day_18_utc, time_policy=self.policy, result_unit=TimeUnit.HOUR)
        # then
        assert calculated_hours_duration is not None
        self.assertAlmostEqual(calculated_hours_duration.time_delta, 4.0, delta=1e-6)

    def test_multiday_counts_4_workdays_only_lower_bound(self):
        # given
        end_next_monday_at_10_utc = datetime(2024, 1, 8, 10, 0, tzinfo=timezone.utc)
        # when
        calculated_days_duration = self.ext.extract_time_from_period(self.start_mon_9, end_next_monday_at_10_utc, time_policy=self.policy, result_unit=TimeUnit.DAY)
        # then
        self.assertIsNotNone(calculated_days_duration)
        assert calculated_days_duration is not None
        self.assertGreaterEqual(calculated_days_duration.time_delta, 4.0)

    def test_multiday_counts_4_workdays_only_upper_bound(self):
        # given
        end_next_monday_at_10_utc = datetime(2024, 1, 8, 10, 0, tzinfo=timezone.utc)
        # when
        calculated_days_duration = self.ext.extract_time_from_period(self.start_mon_9, end_next_monday_at_10_utc, time_policy=self.policy, result_unit=TimeUnit.DAY)
        # then
        self.assertIsNotNone(calculated_days_duration)
        assert calculated_days_duration is not None
        self.assertLessEqual(calculated_days_duration.time_delta, 5.0)

    def test_month_conversion_uses_20_days(self):
        one_month_in_days = Duration.of(1, TimeUnit.MONTH).convert(TimeUnit.DAY, self.policy)
        self.assertAlmostEqual(one_month_in_days.time_delta, 20.0, delta=1e-6)


if __name__ == '__main__':
    unittest.main()
