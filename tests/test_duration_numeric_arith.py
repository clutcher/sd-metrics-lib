import unittest
from sd_metrics_lib.utils.time import Duration, TimeUnit


class TestDurationNumericArithmetic(unittest.TestCase):
    def test_add_number_on_right_adds_in_same_unit(self):
        duration_two_hours = Duration.of(2, TimeUnit.HOUR)
        self.assertEqual(duration_two_hours + 3, Duration.of(5, TimeUnit.HOUR))

    def test_add_number_on_left_adds_in_same_unit(self):
        duration_two_hours = Duration.of(2, TimeUnit.HOUR)
        self.assertEqual(3 + duration_two_hours, Duration.of(5, TimeUnit.HOUR))

    def test_sub_number_on_right_subtracts_in_same_unit(self):
        duration_two_hours = Duration.of(2, TimeUnit.HOUR)
        self.assertEqual(duration_two_hours - 0.5, Duration.of(1.5, TimeUnit.HOUR))

    def test_sub_number_on_left_subtracts_duration_from_number(self):
        duration_two_hours = Duration.of(2, TimeUnit.HOUR)
        self.assertEqual(2.5 - duration_two_hours, Duration.of(0.5, TimeUnit.HOUR))

    def test_iadd_with_number_returns_new_instance_sum(self):
        duration_one_day = Duration.of(1, TimeUnit.DAY)
        duration_one_day = duration_one_day.__iadd__(2)
        self.assertEqual(duration_one_day, Duration.of(3, TimeUnit.DAY))

    def test_isub_with_number_returns_new_instance_difference(self):
        duration_three_days = Duration.of(3, TimeUnit.DAY)
        duration_three_days = duration_three_days.__isub__(1.5)
        self.assertEqual(duration_three_days, Duration.of(1.5, TimeUnit.DAY))

    def test_mul_right_by_number_multiplies_value(self):
        duration_four_hours = Duration.of(4, TimeUnit.HOUR)
        self.assertEqual(duration_four_hours * 2, Duration.of(8, TimeUnit.HOUR))

    def test_mul_left_by_number_multiplies_value(self):
        duration_four_hours = Duration.of(4, TimeUnit.HOUR)
        self.assertEqual(2 * duration_four_hours, Duration.of(8, TimeUnit.HOUR))

    def test_div_right_by_number_divides_value(self):
        duration_four_hours = Duration.of(4, TimeUnit.HOUR)
        self.assertEqual((duration_four_hours / 4), Duration.of(1, TimeUnit.HOUR))

    def test_division_duration_by_duration_equal_returns_ratio_one(self):
        duration_forty_eight_hours = Duration.of(48, TimeUnit.HOUR)
        duration_two_days = Duration.of(2, TimeUnit.DAY)
        self.assertAlmostEqual(duration_forty_eight_hours / duration_two_days, 1.0, places=12)

    def test_division_duration_by_duration_different_values_returns_ratio_two(self):
        duration_forty_eight_hours = Duration.of(48, TimeUnit.HOUR)
        duration_one_day = Duration.of(1, TimeUnit.DAY)
        self.assertAlmostEqual(duration_forty_eight_hours / duration_one_day, 2.0, places=12)

    def test_number_divided_by_duration_raises_type_error(self):
        duration_two_hours = Duration.of(2, TimeUnit.HOUR)
        with self.assertRaises(TypeError):
            5 / duration_two_hours  # type: ignore[operator]

    def test_add_duration_with_mixed_units_uses_default_policy_result_in_days(self):
        duration_one_day = Duration.of(1, TimeUnit.DAY)
        duration_four_hours = Duration.of(4, TimeUnit.HOUR)
        summed_in_days = duration_one_day + duration_four_hours
        self.assertEqual(summed_in_days, Duration.of(1 + 4 / 24, TimeUnit.DAY))

    def test_sub_duration_with_mixed_units_uses_default_policy_result_in_days(self):
        duration_one_day = Duration.of(1, TimeUnit.DAY)
        duration_four_hours = Duration.of(4, TimeUnit.HOUR)
        difference_in_days = duration_one_day - duration_four_hours
        self.assertEqual(difference_in_days, Duration.of(1 - 4 / 24, TimeUnit.DAY))


if __name__ == '__main__':
    unittest.main()
