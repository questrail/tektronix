# -*- coding: utf-8 -*-
# Copyright (c) 2013-2022 The tektronix developers. All rights reserved.
# Project site: https://github.com/questrail/tektronix
# Use of this source code is governed by a MIT-style license that
# can be found in the LICENSE.txt file for the project.
"""Unit tests for tektronix/rsa500.py.
"""
import unittest
import logging

import numpy.testing as npt

from unipath import Path

from tektronix import rsa500

TEST_DIR = Path(__file__).ancestor(1)


# Setup logging
logging.basicConfig(
    level=logging.DEBUG, format=" %(asctime)s -  %(levelname)s - %(message)s"
)


class TestReadingCSVFiles(unittest.TestCase):
    def setUp(self):
        test_csv_file = Path(TEST_DIR, "sample_data", "1M-11M.csv")
        print(test_csv_file)
        (self.header, self.data) = rsa500.read_csv_file(test_csv_file)

    def test_header_when_reading_csv_file(self):
        self.assertEqual(self.header["file"], "1M-11M.csv")
        self.assertEqual(self.header["center_freq"], 6_000_000.0)
        self.assertEqual(self.header["span_freq"], 10_000_000.0)
        self.assertEqual(self.header["resolution_bw"], 9_000.0)
        self.assertEqual(self.header["resolution_bw_units"], "Hz")
        self.assertEqual(self.header["num_traces"], 1)
        self.assertEqual(self.header["num_points"], 801)

    def test_data_when_reading_csv_file(self):
        self.assertEqual(self.data.shape, (801,))
        self.assertEqual(self.data["amplitude"].shape, (801,))
        freq_data = [
            (self.data["frequency"][0], 1_000_000.0),
            (self.data["frequency"][1], 1_012_500.0),
            (self.data["frequency"][799], 10_987_500.0),
            (self.data["frequency"][800], 11_000_000.0),
            (self.data["frequency"][-2], 10_987_500.0),
            (self.data["frequency"][-1], 11_000_000.0),
        ]
        for actual, desired in freq_data:
            npt.assert_almost_equal(actual, desired)
        amp_data = [
            (self.data["amplitude"][0], 57.427009582519531),
            (self.data["amplitude"][1], 40.868099212646484),
            (self.data["amplitude"][-2], 17.863529205322266),
            (self.data["amplitude"][-1], 20.075450897216797),
        ]
        for actual, desired in amp_data:
            npt.assert_almost_equal(actual, desired)


if __name__ == "__main__":
    unittest.main()
