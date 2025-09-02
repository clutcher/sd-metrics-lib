import unittest
from sd_metrics_lib.utils.time import Duration, TimeUnit


class TestDurationNumericComparison(unittest.TestCase):
    def test_eq_number_in_same_unit_matches_value(self):
        duration_two_hours = Duration.of(2, TimeUnit.HOUR)
        self.assertEqual(duration_two_hours, 2)

    def test_ne_number_in_same_unit_is_false_when_equal(self):
        duration_two_hours = Duration.of(2, TimeUnit.HOUR)
        self.assertFalse(duration_two_hours != 2)

    def test_gt_number_in_same_unit_when_greater(self):
        duration_two_hours = Duration.of(2, TimeUnit.HOUR)
        self.assertTrue(duration_two_hours > 1.5)

    def test_ge_number_in_same_unit_when_equal(self):
        duration_two_hours = Duration.of(2, TimeUnit.HOUR)
        self.assertTrue(duration_two_hours >= 2)

    def test_lt_number_in_same_unit_when_less(self):
        duration_two_hours = Duration.of(2, TimeUnit.HOUR)
        self.assertTrue(duration_two_hours < 3)

    def test_le_number_in_same_unit_when_equal(self):
        duration_two_hours = Duration.of(2, TimeUnit.HOUR)
        self.assertTrue(duration_two_hours <= 2)

    def test_eq_number_uses_duration_unit_semantics(self):
        duration_twenty_four_hours = Duration.of(24, TimeUnit.HOUR)
        self.assertEqual(duration_twenty_four_hours, 24)

    def test_number_comparison_from_left_is_not_reflected_but_right_side_works(self):
        duration_three_hours = Duration.of(3, TimeUnit.HOUR)
        self.assertTrue(duration_three_hours > 2)


if __name__ == '__main__':
    unittest.main()
