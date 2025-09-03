import unittest
from sd_metrics_lib.utils.time import Duration, TimeUnit


class TestDurationNumericArithmetic(unittest.TestCase):
    def test_add_number_on_right_adds_in_same_unit(self):
        # given
        duration_two_hours = Duration.of(2, TimeUnit.HOUR)
        number_to_add = 3
        # when
        added_duration = duration_two_hours + number_to_add
        # then
        self.assertEqual(added_duration, Duration.of(5, TimeUnit.HOUR))

    def test_add_number_on_left_adds_in_same_unit(self):
        # given
        duration_two_hours = Duration.of(2, TimeUnit.HOUR)
        number_to_add = 3
        # when
        added_duration = number_to_add + duration_two_hours
        # then
        self.assertEqual(added_duration, Duration.of(5, TimeUnit.HOUR))

    def test_sub_number_on_right_subtracts_in_same_unit(self):
        # given
        duration_two_hours = Duration.of(2, TimeUnit.HOUR)
        number_to_subtract = 0.5
        # when
        difference_duration = duration_two_hours - number_to_subtract
        # then
        self.assertEqual(difference_duration, Duration.of(1.5, TimeUnit.HOUR))

    def test_sub_number_on_left_subtracts_duration_from_number(self):
        # given
        duration_two_hours = Duration.of(2, TimeUnit.HOUR)
        number_to_subtract_from = 2.5
        # when
        difference_duration = number_to_subtract_from - duration_two_hours
        # then
        self.assertEqual(difference_duration, Duration.of(0.5, TimeUnit.HOUR))

    def test_iadd_with_number_returns_new_instance_sum(self):
        # given
        duration_one_day = Duration.of(1, TimeUnit.DAY)
        number_to_add = 2
        # when
        result_duration = duration_one_day.__iadd__(number_to_add)
        # then
        self.assertEqual(result_duration, Duration.of(3, TimeUnit.DAY))

    def test_isub_with_number_returns_new_instance_difference(self):
        # given
        duration_three_days = Duration.of(3, TimeUnit.DAY)
        number_to_subtract = 1.5
        # when
        result_duration = duration_three_days.__isub__(number_to_subtract)
        # then
        self.assertEqual(result_duration, Duration.of(1.5, TimeUnit.DAY))

    def test_mul_right_by_number_multiplies_value(self):
        # given
        duration_four_hours = Duration.of(4, TimeUnit.HOUR)
        multiplier = 2
        # when
        product_duration = duration_four_hours * multiplier
        # then
        self.assertEqual(product_duration, Duration.of(8, TimeUnit.HOUR))

    def test_mul_left_by_number_multiplies_value(self):
        # given
        duration_four_hours = Duration.of(4, TimeUnit.HOUR)
        multiplier = 2
        # when
        product_duration = multiplier * duration_four_hours
        # then
        self.assertEqual(product_duration, Duration.of(8, TimeUnit.HOUR))

    def test_div_right_by_number_divides_value(self):
        # given
        duration_four_hours = Duration.of(4, TimeUnit.HOUR)
        divisor = 4
        # when
        quotient_duration = duration_four_hours / divisor
        # then
        self.assertEqual(quotient_duration, Duration.of(1, TimeUnit.HOUR))

    def test_division_duration_by_duration_equal_returns_ratio_one(self):
        # given
        duration_forty_eight_hours = Duration.of(48, TimeUnit.HOUR)
        duration_two_days = Duration.of(2, TimeUnit.DAY)
        # when
        ratio = duration_forty_eight_hours / duration_two_days
        # then
        self.assertAlmostEqual(ratio, 1.0, places=12)

    def test_division_duration_by_duration_different_values_returns_ratio_two(self):
        # given
        duration_forty_eight_hours = Duration.of(48, TimeUnit.HOUR)
        duration_one_day = Duration.of(1, TimeUnit.DAY)
        # when
        ratio = duration_forty_eight_hours / duration_one_day
        # then
        self.assertAlmostEqual(ratio, 2.0, places=12)

    def test_number_divided_by_duration_raises_type_error(self):
        # given
        duration_two_hours = Duration.of(2, TimeUnit.HOUR)
        # when / then
        with self.assertRaises(TypeError):
            5 / duration_two_hours  # type: ignore[operator]

    def test_add_duration_with_mixed_units_uses_default_policy_result_in_days(self):
        # given
        duration_one_day = Duration.of(1, TimeUnit.DAY)
        duration_four_hours = Duration.of(4, TimeUnit.HOUR)
        # when
        summed_in_days = duration_one_day + duration_four_hours
        # then
        self.assertEqual(summed_in_days, Duration.of(1 + 4 / 24, TimeUnit.DAY))

    def test_sub_duration_with_mixed_units_uses_default_policy_result_in_days(self):
        duration_one_day = Duration.of(1, TimeUnit.DAY)
        duration_four_hours = Duration.of(4, TimeUnit.HOUR)
        difference_in_days = duration_one_day - duration_four_hours
        self.assertEqual(difference_in_days, Duration.of(1 - 4 / 24, TimeUnit.DAY))


if __name__ == '__main__':
    unittest.main()
