# Copyright (c) 2013-2026 The tektronix developers. All rights reserved.
# Project site: https://github.com/questrail/tektronix
# Use of this source code is governed by a MIT-style license that
# can be found in the LICENSE.txt file for the project.
"""Unit tests for tektronix/rsa500.py."""

import pathlib

import numpy.testing as npt
import pytest

from tektronix import rsa500

SAMPLE_DATA = pathlib.Path(__file__).parent / "sample_data"


@pytest.fixture
def spectrum_ver0():
    """An RSA500 `Spectrum` (ver 0) csv file."""
    return rsa500.read_csv_file(SAMPLE_DATA / "1M-11M.csv")


@pytest.fixture
def spectrum_ver1():
    """An RSA500 `Spectrum 1` (ver 1) csv file."""
    return rsa500.read_csv_file(SAMPLE_DATA / "Cab 200k-30M Monopole 10kHz TN2.csv")


@pytest.fixture
def emc_emi_ver1():
    """An RSA500 `EMC-EMI 1` (ver 1) csv file."""
    return rsa500.read_csv_file(SAMPLE_DATA / "EMC-EMI v1 Example.csv")


class TestReadingCSVVer0Files:
    """Test reading an RSA500 csv ver 0 data file."""

    def test_header_when_reading_csv_file(self, spectrum_ver0):
        """Test reading the header info of an RSA500 csv data file."""
        header, _ = spectrum_ver0
        assert header["file"] == "1M-11M.csv"
        assert header["center_freq"] == 6_000_000.0
        assert header["span_freq"] == 10_000_000.0
        assert header["resolution_bw"] == 9_000.0
        assert header["resolution_bw_units"] == "Hz"
        assert header["num_traces"] == 1
        assert header["num_points"] == 801

    def test_data_when_reading_csv_file(self, spectrum_ver0):
        """Test reading the trace data of an RSA500 csv data file."""
        _, data = spectrum_ver0
        assert data.shape == (801,)
        assert data["amplitude"].shape == (801,)
        freq_data = [
            (data["frequency"][0], 1_000_000.0),
            (data["frequency"][1], 1_012_500.0),
            (data["frequency"][799], 10_987_500.0),
            (data["frequency"][800], 11_000_000.0),
            (data["frequency"][-2], 10_987_500.0),
            (data["frequency"][-1], 11_000_000.0),
        ]
        for actual, desired in freq_data:
            npt.assert_almost_equal(actual, desired)
        amp_data = [
            (data["amplitude"][0], 57.427009582519531),
            (data["amplitude"][1], 40.868099212646484),
            (data["amplitude"][-2], 17.863529205322266),
            (data["amplitude"][-1], 20.075450897216797),
        ]
        for actual, desired in amp_data:
            npt.assert_almost_equal(actual, desired)


class TestReadingCSVVer1Files:
    """Test reading an RSA500 csv ver 1 data file."""

    def test_header_when_reading_csv_file(self, spectrum_ver1):
        """Test reading the header info of an RSA500 csv data file."""
        header, _ = spectrum_ver1
        assert header["file"] == "Cab 200k-30M Monopole 10kHz TN2.csv"
        assert header["center_freq"] == 15_100_000.0
        assert header["span_freq"] == 29_800_000.0
        assert header["resolution_bw"] == 10_000.0
        assert header["resolution_bw_units"] == "Hz"
        assert header["num_traces"] == 1
        assert header["num_points"] == 2401

    def test_data_when_reading_csv_file(self, spectrum_ver1):
        """Test reading the trace data of an RSA500 csv data file."""
        _, data = spectrum_ver1
        assert data.shape == (2401,)
        assert data["amplitude"].shape == (2401,)
        freq_data = [
            (data["frequency"][0], 200_000.0),
            (data["frequency"][3], 237_250.0),
        ]
        for actual, desired in freq_data:
            npt.assert_almost_equal(actual, desired)
        amp_data = [
            (data["amplitude"][0], 82.783210754394531),
            (data["amplitude"][1], 86.962478637695313),
            (data["amplitude"][-2], 43.837810516357422),
            (data["amplitude"][-1], 43.746368408203125),
        ]
        for actual, desired in amp_data:
            npt.assert_almost_equal(actual, desired)


class TestReadingEMCEMICSVVer1Files:
    """Test reading an RSA500 EMC-EMI csv ver 1 data file."""

    def test_header_when_reading_csv_file(self, emc_emi_ver1):
        """Test reading the header info of an RSA500 csv data file."""
        header, _ = emc_emi_ver1
        assert header["file"] == "EMC-EMI v1 Example.csv"
        assert header["center_freq"] == 6_000_000.0
        assert header["resolution_bw"] == 9_000.0
        assert header["resolution_bw_units"] == "Hz"
        assert header["num_traces"] == 1
        assert header["num_points"] == 2401

    def test_data_when_reading_csv_file(self, emc_emi_ver1):
        """Test reading the trace data of an RSA500 csv data file."""
        _, data = emc_emi_ver1
        assert data.shape == (2401,)
        assert data["amplitude"].shape == (2401,)
        freq_data = [
            (data["frequency"][0], 1_000_000.0),
            (data["frequency"][3], 1_012_500.0),
        ]
        for actual, desired in freq_data:
            npt.assert_almost_equal(actual, desired)
        amp_data = [
            (data["amplitude"][0], 45.09005),
            (data["amplitude"][1], 44.83614),
            (data["amplitude"][-2], 13.39709),
            (data["amplitude"][-1], 13.50026),
        ]
        for actual, desired in amp_data:
            npt.assert_almost_equal(actual, desired)


class TestReadingUnknownCSVFiles:
    """Test reading a csv file the module does not recognize."""

    def test_unknown_filetype_raises(self, tmp_path):
        """An unrecognized first cell stops the read rather than mis-parsing.

        The three recognized layouts are told apart by that cell alone, and
        everything after it indexes into rows whose shape depends on which
        layout it is, so continuing past an unknown one would read a
        different file format as if it were an RSA500 trace.
        """
        unknown_csv = tmp_path / "unknown.csv"
        unknown_csv.write_text("Waveform,2025-11-11T00:00:00\n")

        with pytest.raises(rsa500.UnknownFileTypeError, match="Waveform"):
            rsa500.read_csv_file(unknown_csv)

    def test_unknown_filetype_leaves_the_caller_running(self, tmp_path):
        """The read used to call sys.exit, ending the caller's process.

        Catching what it raises has to be enough to carry on, which is the
        whole difference between a library reporting a bad file and one
        deciding the program is over.
        """
        unknown_csv = tmp_path / "unknown.csv"
        unknown_csv.write_text("Waveform,2025-11-11T00:00:00\n")

        carried_on = False
        try:
            rsa500.read_csv_file(unknown_csv)
        except rsa500.UnknownFileTypeError:
            carried_on = True

        assert carried_on

    def test_the_error_is_a_value_error(self, tmp_path):
        """Anyone already catching ValueError around a read keeps working."""
        unknown_csv = tmp_path / "unknown.csv"
        unknown_csv.write_text("Waveform,2025-11-11T00:00:00\n")

        with pytest.raises(ValueError, match="Unknown csv filetype"):
            rsa500.read_csv_file(unknown_csv)
