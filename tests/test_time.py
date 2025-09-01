from datetime import datetime, timedelta

import pytest

from sd_metrics_lib.utils.time import TimeUnit, TimePolicy, Duration, SECONDS_IN_HOUR, WORKING_HOURS_PER_DAY, \
    WORKING_DAYS_PER_WEEK, WORKING_WEEKS_IN_MONTH


class TestTimePolicy:
    def test_all_hours_seconds_to_hour(self):
        all_hours_policy = TimePolicy.ALL_HOURS
        converted_seconds_to_hours = Duration.of(all_hours_policy.convert(SECONDS_IN_HOUR, TimeUnit.SECOND, TimeUnit.HOUR), TimeUnit.HOUR)
        expected_one_hour_duration = Duration.of(1.0, TimeUnit.HOUR)
        assert converted_seconds_to_hours == expected_one_hour_duration

    def test_all_hours_seconds_to_day(self):
        all_hours_policy = TimePolicy.ALL_HOURS
        converted_seconds_to_days = Duration.of(all_hours_policy.convert(SECONDS_IN_HOUR * 24, TimeUnit.SECOND, TimeUnit.DAY), TimeUnit.DAY)
        expected_one_day_duration = Duration.of(1.0, TimeUnit.DAY)
        assert converted_seconds_to_days == expected_one_day_duration

    def test_all_hours_day_to_seconds(self):
        all_hours_policy = TimePolicy.ALL_HOURS
        converted_one_day_to_seconds = Duration.of(all_hours_policy.convert(1, TimeUnit.DAY, TimeUnit.SECOND), TimeUnit.SECOND)
        expected_seconds_in_day = Duration.of(24 * SECONDS_IN_HOUR, TimeUnit.SECOND)
        assert converted_one_day_to_seconds == expected_seconds_in_day

    def test_all_hours_hours_to_day(self):
        all_hours_policy = TimePolicy.ALL_HOURS
        converted_24h_to_days = Duration.of(all_hours_policy.convert(24, TimeUnit.HOUR, TimeUnit.DAY), TimeUnit.DAY)
        expected_one_day = Duration.of(1.0, TimeUnit.DAY)
        assert converted_24h_to_days == expected_one_day

    def test_all_hours_week_to_day(self):
        all_hours_policy = TimePolicy.ALL_HOURS
        converted_week_to_days = Duration.of(all_hours_policy.convert(1, TimeUnit.WEEK, TimeUnit.DAY), TimeUnit.DAY)
        expected_seven_days = Duration.of(7, TimeUnit.DAY)
        assert converted_week_to_days == expected_seven_days

    def test_all_hours_month_to_day(self):
        all_hours_policy = TimePolicy.ALL_HOURS
        converted_month_to_days = Duration.of(all_hours_policy.convert(1, TimeUnit.MONTH, TimeUnit.DAY), TimeUnit.DAY)
        expected_thirty_days = Duration.of(30, TimeUnit.DAY)
        assert converted_month_to_days == expected_thirty_days

    def test_all_hours_identity(self):
        all_hours_policy = TimePolicy.ALL_HOURS
        converted_identity_hours = Duration.of(all_hours_policy.convert(3.14, TimeUnit.HOUR, TimeUnit.HOUR), TimeUnit.HOUR)
        expected_same_hours = Duration.of(3.14, TimeUnit.HOUR)
        assert converted_identity_hours == expected_same_hours

    def test_business_hours_hour_to_day(self):
        business_hours_policy = TimePolicy.BUSINESS_HOURS
        converted_working_hours_per_day_to_day = Duration.of(business_hours_policy.convert(WORKING_HOURS_PER_DAY, TimeUnit.HOUR, TimeUnit.DAY), TimeUnit.DAY)
        expected_one_business_day = Duration.of(1.0, TimeUnit.DAY)
        assert converted_working_hours_per_day_to_day == expected_one_business_day

    def test_business_hours_day_to_seconds(self):
        business_hours_policy = TimePolicy.BUSINESS_HOURS
        converted_business_day_to_seconds = Duration.of(business_hours_policy.convert(1, TimeUnit.DAY, TimeUnit.SECOND), TimeUnit.SECOND)
        expected_seconds_in_business_day = Duration.of(WORKING_HOURS_PER_DAY * SECONDS_IN_HOUR, TimeUnit.SECOND)
        assert converted_business_day_to_seconds == expected_seconds_in_business_day

    def test_business_hours_week_to_day(self):
        business_hours_policy = TimePolicy.BUSINESS_HOURS
        converted_business_week_to_days = Duration.of(business_hours_policy.convert(1, TimeUnit.WEEK, TimeUnit.DAY), TimeUnit.DAY)
        expected_working_days_per_week = Duration.of(WORKING_DAYS_PER_WEEK, TimeUnit.DAY)
        assert converted_business_week_to_days == expected_working_days_per_week

    def test_business_hours_month_to_day(self):
        business_hours_policy = TimePolicy.BUSINESS_HOURS
        converted_business_month_to_days = Duration.of(business_hours_policy.convert(1, TimeUnit.MONTH, TimeUnit.DAY), TimeUnit.DAY)
        expected_working_days_per_month = Duration.of(WORKING_DAYS_PER_WEEK * WORKING_WEEKS_IN_MONTH, TimeUnit.DAY)
        assert converted_business_month_to_days == expected_working_days_per_month

    @pytest.mark.parametrize("unit", list(TimeUnit))
    def test_business_hours_round_trip_via_day(self, unit):
        business_hours_policy = TimePolicy.BUSINESS_HOURS
        value = 13.7
        roundtrip_converted = Duration.of(business_hours_policy.convert(business_hours_policy.convert(value, unit, TimeUnit.DAY), TimeUnit.DAY, unit), unit)
        original_value_duration = Duration.of(value, unit)
        assert roundtrip_converted.sub(original_value_duration).is_zero(eps=1e-6)


class TestDuration:
    def test_zero_returns_false_bool(self):
        z = Duration.zero(TimeUnit.HOUR)
        assert not z

    def test_zero_keeps_unit_and_value(self):
        z = Duration.zero(TimeUnit.HOUR)
        assert z.time_delta == 0.0 and z.time_unit == TimeUnit.HOUR

    def test_of_constructs(self):
        d = Duration.of(2, TimeUnit.DAY)
        assert d and d.time_delta == 2.0 and d.time_unit == TimeUnit.DAY

    def test_difference_numeric(self):
        d = Duration.difference(10, 25.5, TimeUnit.HOUR)
        assert d == Duration.of(15.5, TimeUnit.HOUR)

    def test_datetime_difference_hours(self):
        start = datetime(2025, 1, 1, 0, 0, 0)
        end = start + timedelta(days=2, hours=6)
        d_hours = Duration.datetime_difference(start, end, TimeUnit.HOUR)
        assert d_hours == Duration.of(54.0, TimeUnit.HOUR)

    def test_datetime_difference_days(self):
        start = datetime(2025, 1, 1, 0, 0, 0)
        end = start + timedelta(days=2, hours=6)
        d_days = Duration.datetime_difference(start, end, TimeUnit.DAY)
        assert d_days == Duration.of(2.25, TimeUnit.DAY)

    def test_to_seconds_all_hours(self):
        d = Duration.of(2, TimeUnit.DAY)
        converted_two_days_to_seconds = Duration.of(d.to_seconds(TimePolicy.ALL_HOURS), TimeUnit.SECOND)
        expected_seconds = Duration.of(2 * 24 * SECONDS_IN_HOUR, TimeUnit.SECOND)
        assert converted_two_days_to_seconds == expected_seconds

    def test_convert_business_day_to_hours(self):
        d = Duration.of(2, TimeUnit.DAY)
        converted_business_days_to_hours = d.convert(TimeUnit.HOUR, TimePolicy.BUSINESS_HOURS)
        expected_business_hours = Duration.of(2 * WORKING_HOURS_PER_DAY, TimeUnit.HOUR)
        assert converted_business_days_to_hours == expected_business_hours

    def test_convert_business_hours_to_days(self):
        h = Duration.of(16, TimeUnit.HOUR)
        converted_hours_to_business_days = h.convert(TimeUnit.DAY, TimePolicy.BUSINESS_HOURS)
        expected_two_business_days = Duration.of(2.0, TimeUnit.DAY)
        assert converted_hours_to_business_days == expected_two_business_days

    def test_is_zero_exact_zero(self):
        assert Duration.zero(TimeUnit.SECOND).is_zero()

    def test_is_zero_with_epsilon_seconds(self):
        tiny = Duration.of(0.5, TimeUnit.SECOND)
        assert tiny.is_zero(eps=1.0)

    def test_is_zero_with_epsilon_hour_equivalent(self):
        tiny_h = Duration.of(1 / SECONDS_IN_HOUR * 0.5, TimeUnit.HOUR)
        assert tiny_h.is_zero(eps=1.0)

    def test_is_zero_eps_zero_means_exact(self):
        assert not Duration.of(1e-12, TimeUnit.SECOND).is_zero(eps=0.0)

    def test_add_default_policy(self):
        a = Duration.of(1, TimeUnit.DAY)
        b = Duration.of(4, TimeUnit.HOUR)
        c = a + b
        assert c == Duration.of(1 + 4 / 24, TimeUnit.DAY)

    def test_sub_default_policy(self):
        a = Duration.of(1, TimeUnit.DAY)
        b = Duration.of(4, TimeUnit.HOUR)
        d = a - b
        assert d == Duration.of(1 - 4 / 24, TimeUnit.DAY)

    def test_add_with_business_hours_target_hour(self):
        a = Duration.of(1, TimeUnit.DAY)
        b = Duration.of(4, TimeUnit.HOUR)
        c2 = a.add(b, policy=TimePolicy.BUSINESS_HOURS, unit=TimeUnit.HOUR)
        assert c2 == Duration.of(WORKING_HOURS_PER_DAY + 4, TimeUnit.HOUR)

    def test_scalar_operations_multiplication_division(self):
        b = Duration.of(4, TimeUnit.HOUR)
        e = (b * 2.5) / 5
        assert e == Duration.of(2.0, TimeUnit.HOUR)

    def test_equality_cross_units(self):
        two_days = Duration.of(2, TimeUnit.DAY)
        forty_eight_hours = Duration.of(48, TimeUnit.HOUR)
        assert two_days == forty_eight_hours or (
                    not (two_days < forty_eight_hours) and not (two_days > forty_eight_hours))

    def test_le_ge_cross_units(self):
        two_days = Duration.of(2, TimeUnit.DAY)
        forty_eight_hours = Duration.of(48, TimeUnit.HOUR)
        assert two_days <= forty_eight_hours and two_days >= forty_eight_hours

    def test_week_greater_than_six_days(self):
        one_week = Duration.of(1, TimeUnit.WEEK)
        six_days = Duration.of(6, TimeUnit.DAY)
        assert one_week > six_days

    def test_sum_mixed_units_all_hours_hours(self):
        items = [
            Duration.of(1, TimeUnit.DAY),
            Duration.of(4, TimeUnit.HOUR),
            Duration.of(30, TimeUnit.MINUTE) if hasattr(TimeUnit, 'MINUTE') else Duration.of(0.5, TimeUnit.HOUR),
        ]
        total = Duration.sum(items, policy=TimePolicy.ALL_HOURS, unit=TimeUnit.HOUR)
        assert total == Duration.of(28.5, TimeUnit.HOUR)

    def test_sum_mixed_units_business_days(self):
        items = [
            Duration.of(1, TimeUnit.DAY),
            Duration.of(4, TimeUnit.HOUR),
            Duration.of(30, TimeUnit.MINUTE) if hasattr(TimeUnit, 'MINUTE') else Duration.of(0.5, TimeUnit.HOUR),
        ]
        total_b = Duration.sum(items, policy=TimePolicy.BUSINESS_HOURS, unit=TimeUnit.DAY)
        assert total_b == Duration.of((WORKING_HOURS_PER_DAY + 4 + 0.5) / WORKING_HOURS_PER_DAY, TimeUnit.DAY)
