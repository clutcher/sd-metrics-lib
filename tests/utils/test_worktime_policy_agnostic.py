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

    def test_all_hours_returns_calendar_seconds_not_none(self):
        # given
        # when
        extracted_seconds_duration = self.ext.extract_time_from_period(self.start, self.end_same_day, time_policy=TimePolicy.ALL_HOURS, result_unit=TimeUnit.SECOND)
        # then
        self.assertIsNotNone(extracted_seconds_duration)

    def test_all_hours_returns_calendar_seconds_unit_is_second(self):
        # given
        # when
        extracted_seconds_duration = self.ext.extract_time_from_period(self.start, self.end_same_day, time_policy=TimePolicy.ALL_HOURS, result_unit=TimeUnit.SECOND)
        # then
        assert extracted_seconds_duration is not None
        self.assertEqual(extracted_seconds_duration.time_unit, TimeUnit.SECOND)

    def test_all_hours_returns_calendar_seconds_value_matches(self):
        # given
        # when
        extracted_seconds_duration = self.ext.extract_time_from_period(self.start, self.end_same_day, time_policy=TimePolicy.ALL_HOURS, result_unit=TimeUnit.SECOND)
        # then
        assert extracted_seconds_duration is not None
        self.assertAlmostEqual(extracted_seconds_duration.time_delta, (self.end_same_day - self.start).total_seconds(), delta=1)

    def test_business_hours_default_policy_not_none(self):
        # given
        # when
        extracted_hours_duration = self.ext.extract_time_from_period(self.start, self.end_same_day, time_policy=TimePolicy.BUSINESS_HOURS, result_unit=TimeUnit.HOUR)
        # then
        self.assertIsNotNone(extracted_hours_duration)

    def test_business_hours_default_policy_unit_is_hour(self):
        # given
        # when
        extracted_hours_duration = self.ext.extract_time_from_period(self.start, self.end_same_day, time_policy=TimePolicy.BUSINESS_HOURS, result_unit=TimeUnit.HOUR)
        # then
        assert extracted_hours_duration is not None
        self.assertEqual(extracted_hours_duration.time_unit, TimeUnit.HOUR)

    def test_business_hours_default_policy_value_is_eight(self):
        # given
        # when
        extracted_hours_duration = self.ext.extract_time_from_period(self.start, self.end_same_day, time_policy=TimePolicy.BUSINESS_HOURS, result_unit=TimeUnit.HOUR)
        # then
        assert extracted_hours_duration is not None
        self.assertAlmostEqual(extracted_hours_duration.time_delta, 8.0, delta=1e-6)

    def test_custom_policy_all_hours_branch_independent_of_policy(self):
        # given
        custom_policy_6h_4d = TimePolicy(hours_per_day=6, days_per_week=4, days_per_month=20)
        # when
        extracted_all_hours = self.ext.extract_time_from_period(self.start, self.end_same_day, time_policy=TimePolicy.ALL_HOURS, result_unit=TimeUnit.HOUR)
        # then
        assert extracted_all_hours is not None
        self.assertAlmostEqual(extracted_all_hours.time_delta, 9.0, delta=1e-6)

    def test_custom_policy_business_hours_converts_using_custom_hours_per_day(self):
        # given
        custom_policy_6h_4d = TimePolicy(hours_per_day=6, days_per_week=4, days_per_month=20)
        # when
        extracted_business_seconds = self.ext.extract_time_from_period(self.start, self.end_same_day, time_policy=TimePolicy.BUSINESS_HOURS, result_unit=TimeUnit.SECOND)
        converted_hours_custom = extracted_business_seconds.convert(TimeUnit.HOUR, custom_policy_6h_4d)
        # then
        assert converted_hours_custom is not None
        self.assertAlmostEqual(converted_hours_custom.time_delta, 8.0, delta=1e-6)

    def test_multiday_counts_workdays_only_lower_bound(self):
        # given
        end_time_friday_morning_utc = datetime(2024, 1, 5, 10, 0, tzinfo=timezone.utc)
        # when
        extracted_business_days = self.ext.extract_time_from_period(self.start, end_time_friday_morning_utc, time_policy=TimePolicy.BUSINESS_HOURS, result_unit=TimeUnit.DAY)
        # then
        assert extracted_business_days is not None
        self.assertGreaterEqual(extracted_business_days.time_delta, 3.0)

    def test_multiday_counts_workdays_only_upper_bound(self):
        # given
        end_time_friday_morning_utc = datetime(2024, 1, 5, 10, 0, tzinfo=timezone.utc)
        # when
        extracted_business_days = self.ext.extract_time_from_period(self.start, end_time_friday_morning_utc, time_policy=TimePolicy.BUSINESS_HOURS, result_unit=TimeUnit.DAY)
        # then
        assert extracted_business_days is not None
        self.assertLessEqual(extracted_business_days.time_delta, 5.0)


if __name__ == '__main__':
    unittest.main()
