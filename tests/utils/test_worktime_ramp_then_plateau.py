import unittest
from datetime import datetime, timedelta, timezone

from sd_metrics_lib.utils.worktime import SimpleWorkTimeExtractor
from sd_metrics_lib.utils.time import TimeUnit, TimePolicy


class TestSimpleWorkTimeExtractorRampThenPlateau(unittest.TestCase):
    def setUp(self):
        self.ext = SimpleWorkTimeExtractor()
        self.monday_midnight = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)

    def _business_hours_for_span(self, calendar_hours: float):
        end = self.monday_midnight + timedelta(hours=calendar_hours)
        extracted = self.ext.extract_time_from_period(
            self.monday_midnight, end, time_policy=TimePolicy.BUSINESS_HOURS, result_unit=TimeUnit.HOUR)
        return extracted.time_delta if extracted is not None else None

    def test_should_return_none_when_span_below_minimum_trackable(self):
        # given
        end = self.monday_midnight + timedelta(minutes=10)
        # when
        extracted = self.ext.extract_time_from_period(
            self.monday_midnight, end, time_policy=TimePolicy.BUSINESS_HOURS, result_unit=TimeUnit.HOUR)
        # then
        self.assertIsNone(extracted)

    def test_should_return_raw_hours_when_span_below_one_business_day(self):
        # given
        # when
        business_hours = self._business_hours_for_span(3)
        # then
        self.assertAlmostEqual(business_hours, 3.0, delta=1e-6)

    def test_should_cap_at_business_day_when_same_calendar_day_exceeds_workday(self):
        # given
        # when
        business_hours = self._business_hours_for_span(9)
        # then
        self.assertAlmostEqual(business_hours, 8.0, delta=1e-6)

    def test_should_credit_one_business_day_when_span_is_exactly_one_calendar_day(self):
        # given
        # when
        business_hours = self._business_hours_for_span(24)
        # then
        self.assertAlmostEqual(business_hours, 8.0, delta=1e-6)

    def test_should_plateau_within_second_calendar_chunk_when_span_is_44_calendar_hours(self):
        # given
        # when
        business_hours = self._business_hours_for_span(44)
        # then
        self.assertAlmostEqual(business_hours, 16.0, delta=1e-6)

    def test_should_credit_two_business_days_when_span_is_exactly_two_calendar_days(self):
        # given
        # when
        business_hours = self._business_hours_for_span(48)
        # then
        self.assertAlmostEqual(business_hours, 16.0, delta=1e-6)

    def test_should_ramp_into_third_chunk_when_span_is_50_calendar_hours(self):
        # given
        # when
        business_hours = self._business_hours_for_span(50)
        # then
        self.assertAlmostEqual(business_hours, 18.0, delta=1e-6)

    def test_should_ramp_into_third_chunk_when_span_is_52_calendar_hours(self):
        # given
        # when
        business_hours = self._business_hours_for_span(52)
        # then
        self.assertAlmostEqual(business_hours, 20.0, delta=1e-6)

    def test_should_ramp_into_third_chunk_when_span_is_54_calendar_hours(self):
        # given
        # when
        business_hours = self._business_hours_for_span(54)
        # then
        self.assertAlmostEqual(business_hours, 22.0, delta=1e-6)

    def test_should_complete_third_business_day_when_span_is_56_calendar_hours(self):
        # given
        # when
        business_hours = self._business_hours_for_span(56)
        # then
        self.assertAlmostEqual(business_hours, 24.0, delta=1e-6)

    def test_should_plateau_within_third_chunk_when_span_is_60_calendar_hours(self):
        # given
        # when
        business_hours = self._business_hours_for_span(60)
        # then
        self.assertAlmostEqual(business_hours, 24.0, delta=1e-6)

    def test_should_credit_three_business_days_when_span_is_exactly_three_calendar_days(self):
        # given
        # when
        business_hours = self._business_hours_for_span(72)
        # then
        self.assertAlmostEqual(business_hours, 24.0, delta=1e-6)

    def test_should_ramp_into_fourth_chunk_when_span_is_74_calendar_hours(self):
        # given
        # when
        business_hours = self._business_hours_for_span(74)
        # then
        self.assertAlmostEqual(business_hours, 26.0, delta=1e-6)

    def test_should_count_only_weekday_hours_when_span_crosses_into_weekend(self):
        # given
        friday_morning = datetime(2024, 1, 5, 9, 0, tzinfo=timezone.utc)
        sunday_late_morning = datetime(2024, 1, 7, 11, 0, tzinfo=timezone.utc)
        # when
        extracted = self.ext.extract_time_from_period(
            friday_morning, sunday_late_morning, time_policy=TimePolicy.BUSINESS_HOURS, result_unit=TimeUnit.HOUR)
        # then
        self.assertAlmostEqual(extracted.time_delta, 8.0, delta=1e-6)

    def test_should_sum_weekday_hours_across_weekend_gap(self):
        # given
        friday_morning = datetime(2024, 1, 5, 9, 0, tzinfo=timezone.utc)
        next_monday_morning = datetime(2024, 1, 8, 9, 0, tzinfo=timezone.utc)
        # when
        extracted = self.ext.extract_time_from_period(
            friday_morning, next_monday_morning, time_policy=TimePolicy.BUSINESS_HOURS, result_unit=TimeUnit.HOUR)
        # then
        self.assertAlmostEqual(extracted.time_delta, 8.0, delta=1e-6)

    def test_should_return_raw_calendar_duration_when_policy_is_all_hours(self):
        # given
        end = self.monday_midnight + timedelta(hours=50)
        # when
        extracted = self.ext.extract_time_from_period(
            self.monday_midnight, end, time_policy=TimePolicy.ALL_HOURS, result_unit=TimeUnit.HOUR)
        # then
        self.assertAlmostEqual(extracted.time_delta, 50.0, delta=1e-6)

    def test_should_return_zero_effort_when_policy_has_no_working_days(self):
        # given
        zero_working_days_policy = TimePolicy(hours_per_day=8, days_per_week=0, days_per_month=20)
        wednesday_end = self.monday_midnight + timedelta(hours=48)
        # when
        extracted = self.ext.extract_time_from_period(
            self.monday_midnight, wednesday_end, time_policy=zero_working_days_policy, result_unit=TimeUnit.HOUR)
        # then
        self.assertAlmostEqual(extracted.time_delta, 0.0, delta=1e-6)

    def test_should_count_weekend_hours_when_policy_includes_all_seven_days(self):
        # given
        seven_day_policy = TimePolicy(hours_per_day=8, days_per_week=7, days_per_month=30)
        saturday_start = datetime(2024, 1, 6, 0, 0, tzinfo=timezone.utc)
        sunday_start = datetime(2024, 1, 7, 0, 0, tzinfo=timezone.utc)
        # when
        extracted = self.ext.extract_time_from_period(
            saturday_start, sunday_start, time_policy=seven_day_policy, result_unit=TimeUnit.HOUR)
        # then
        self.assertAlmostEqual(extracted.time_delta, 8.0, delta=1e-6)

    def test_should_stay_non_decreasing_as_end_time_advances_hour_by_hour(self):
        # given
        previous_business_hours = 0.0
        # when
        # then
        for calendar_hours in range(0, 81):
            business_hours = self._business_hours_for_span(calendar_hours)
            current_business_hours = business_hours if business_hours is not None else 0.0
            self.assertGreaterEqual(current_business_hours + 1e-9, previous_business_hours,
                                    msg=f"output dropped at {calendar_hours}h")
            previous_business_hours = current_business_hours


if __name__ == '__main__':
    unittest.main()
