"""
Unit tests for (some of) the tcpping utility functions.

TODO:
 - Achieve full test coverage of all functions using mocking when necessary.
 - Provide real world end-user functional tests.
"""

import unittest

from tcpping import statistics, suppress


class TestTcpPingParts(unittest.TestCase):

    def test_statistics_case_1(self):
        # taken from https://www.mathsisfun.com/data/mean-deviation.html
        data = [3.0, 6.0, 6.0, 7.0, 8.0, 11.0, 15.0, 16.0]
        expected = [3.0, 16.0, 9.0, 3.75]
        for exp, act in zip(expected, statistics(data)):
            self.assertAlmostEqual(exp, act)

    def test_statistics_case_2(self):
        # synthetic
        data = [
            8.606910705566406e-05,
            0.0001399517059326172,
            0.00013303756713867188,
            0.0001289844512939453,
            0.00013494491577148438,
            0.00013494491577148438,
            0.0001327991485595703,
            0.00013113021850585938,
            0.00022983551025390625,
            0.00011706352233886719,
        ]
        expected = [
            8.606910705566406e-05,
            0.00022983551025390625,
            0.00013687610626220704,
            1.920700073242188e-05,
        ]
        for exp, act in zip(expected, statistics(data)):
            self.assertAlmostEqual(exp, act)

    def test_suppress_case__suppress_zero_devision_error(self):
        with suppress(ZeroDivisionError):
            1 / 0

    def test_suppress_case__propagate_io_error(self):
        with self.assertRaises(ZeroDivisionError):
            with suppress(IOError):
                1 / 0


if __name__ == '__main__':
    unittest.main()
