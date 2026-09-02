# Copyright (c) 2013-2026 The tektronix developers. All rights reserved.
# Project site: https://github.com/questrail/tektronix
# Use of this source code is governed by a MIT-style license that
# can be found in the LICENSE.txt file for the project.
"""Read a CSV file saved by a RSA500 Spectrum Analyzer"""

# Standard module imports
import csv
import logging
import os
from collections.abc import Callable, Iterator
from typing import Any

# Data analysis related imports
import numpy as np
import numpy.typing as npt

# A library configures no handlers and sets no levels: basicConfig() here ran
# at import and reconfigured the root logger for whatever application imported
# this module. Logging to a module logger instead leaves that choice where it
# belongs, with the application.
_log = logging.getLogger(__name__)


class UnknownFileTypeError(ValueError):
    """The first cell of the file names a layout this module cannot read."""


# The first cell of the first row is the only thing that says which layout a
# file has, and everything after it indexes into rows whose shape depends on
# that answer. Each entry maps the cell to the (version, measurement type)
# pair it stands for.
_FILE_TYPES = {
    "Spectrum": (0, "spectrum"),
    "Spectrum 1": (1, "spectrum"),
    "EMC-EMI 1": (1, "emc-emi"),
}

# A ver 1 file repeats section labels that also appear as plain text
# elsewhere, so the rows below are matched on their width as well as their
# label.
_CENTER_FREQ_ROW_WIDTH = 3
_EMC_EMI_FREQ_ROW_WIDTH = 5

# The dtype every trace is read into, named here so that the empty case and
# the populated one cannot drift apart.
_TRACE_DTYPE = np.dtype(
    {
        "names": ("frequency", "amplitude"),
        "formats": ("f8", "f8"),
    }
)

Row = list[str]
Reader = Iterator[Row]
Header = dict[str, Any]


def _read_until(reader: Reader, match: Callable[[Row], bool]) -> Row:
    """Advance the reader to the first row `match` accepts and return it.

    Args:
        reader: A csv reader positioned above the row being looked for.
        match: Predicate applied to each row in turn.

    Returns:
        The first row the predicate accepts.
    """
    while True:
        row = next(reader)
        if match(row):
            return row


def _read_ver0_frequency_header(reader: Reader, header: Header) -> None:
    """Read the center frequency and reference level of a ver 0 file.

    A ver 0 file has a fixed preamble, so the rows are counted off rather
    than searched for.

    Args:
        reader: A csv reader positioned below the file type row.
        header: The header dict, updated in place.
    """
    next(reader)
    row = next(reader)
    header["center_freq"] = float(row[1])
    header["center_freq_units"] = row[2]
    row = next(reader)
    header["ref_level"] = float(row[1])
    header["ref_level_units"] = row[2]


def _read_ver1_frequency_header(reader: Reader, header: Header) -> None:
    """Read the center frequency and reference level of a ver 1 file.

    The preamble of a ver 1 file varies in length, so the center frequency
    is searched for rather than counted off. The reference level follows it.

    Args:
        reader: A csv reader positioned below the file type row.
        header: The header dict, updated in place.
    """
    row = _read_until(
        reader,
        lambda row: len(row) == _CENTER_FREQ_ROW_WIDTH and row[0] == "Center Frequency",
    )
    header["center_freq"] = float(row[1])
    header["center_freq_units"] = row[2]
    row = next(reader)
    header["ref_level"] = float(row[1])
    header["ref_level_units"] = row[2]


def _read_spectrum_parameters(reader: Reader, header: Header) -> None:
    """Read the [Parameters] section of a spectrum measurement.

    Args:
        reader: A csv reader positioned below the [Parameters] row.
        header: The header dict, updated in place.
    """
    row = next(reader)
    header["span_freq"] = float(row[1])
    header["span_freq_units"] = row[2]
    row = next(reader)
    header["resolution_bw"] = float(row[1])
    header["resolution_bw_units"] = row[2]
    row = next(reader)
    header["rbw_window_type"] = row[1]


def _read_emc_emi_parameters(reader: Reader, header: Header) -> None:
    """Read the [Parameters] section of an EMC-EMI measurement.

    An EMC-EMI measurement gives a start and stop frequency where a spectrum
    measurement gives a span, and carries them one column further right.

    Args:
        reader: A csv reader positioned below the [Parameters] row.
        header: The header dict, updated in place.
    """
    row = _read_until(
        reader,
        lambda row: len(row) == _EMC_EMI_FREQ_ROW_WIDTH and row[0] == "Start Frequency",
    )
    header["start_freq"] = float(row[2])
    header["start_freq_units"] = row[3]
    row = next(reader)
    header["stop_freq"] = float(row[2])
    header["stop_freq_units"] = row[3]
    row = next(reader)
    header["resolution_bw"] = float(row[2])
    header["resolution_bw_units"] = row[3]


def _read_trace_header(reader: Reader, header: Header, msr_type: str) -> int:
    """Read the [Traces] section down to the first data row.

    Args:
        reader: A csv reader positioned above the [Traces] row.
        header: The header dict, updated in place.
        msr_type: Either 'spectrum' or 'emc-emi'.

    Returns:
        The number of points the file says the trace holds.
    """
    _read_until(reader, lambda row: len(row) == 1 and row[0] == "[Traces]")
    next(reader)
    next(reader)
    row = next(reader)
    num_points = int(row[1])
    header["num_points"] = num_points
    # FIXME(mdr): I need an example file with multiple traces to determine
    # how to parse more than just a single trace.
    header["num_traces"] = 1
    row = next(reader)
    if msr_type == "spectrum":
        header["frequency_unit"] = row[2]
        next(reader)
    else:
        header["frequency_unit"] = row[1]
    return num_points


def _read_trace_data(
    reader: Reader, num_points: int, msr_type: str
) -> npt.NDArray[np.void]:
    """Read `num_points` rows of trace data.

    A spectrum measurement gives amplitude before frequency, and an EMC-EMI
    one gives them the other way round; both are stored frequency first.

    Args:
        reader: A csv reader positioned on the first data row.
        num_points: How many rows to read.
        msr_type: Either 'spectrum' or 'emc-emi'.

    Returns:
        A 1D numpy structured array with fields 'frequency' and 'amplitude'.
    """
    data: list[tuple[float, float]] = []
    for _ in range(num_points):
        row = next(reader)
        if msr_type == "spectrum":
            data.append((float(row[1]), float(row[0])))
        else:
            data.append((float(row[0]), float(row[1])))
    # Built once, after the loop. Building it inside meant reallocating and
    # recopying the whole trace on every row, and left the array unbound for
    # a file whose header claims no points at all.
    return np.array(data, dtype=_TRACE_DTYPE)


def read_csv_file(
    filename: str | os.PathLike[str],
) -> tuple[Header, npt.NDArray[np.void]]:
    """Read csv file into a numpy array

    Three file layouts are recognized, told apart by the first cell of the
    first row: `Spectrum` (ver 0), `Spectrum 1` (ver 1), and `EMC-EMI 1`
    (ver 1). The header keys differ between a spectrum measurement, which
    carries a span, and an EMC-EMI one, which carries a start and stop
    frequency instead.

    Args:
        filename: Path to a CSV file saved by an RSA500 spectrum analyzer.

    Returns:
        A two element tuple of the header dict and a 1D numpy structured
        array with fields 'frequency' and 'amplitude'.

    Raises:
        UnknownFileTypeError: The first cell names a layout this module does
            not read.
    """
    header: Header = {}

    with open(filename, newline="", encoding="utf8") as infile:
        reader = csv.reader((line.replace("\0", "") for line in infile), delimiter=",")
        header["file"] = os.path.basename(filename)
        row = next(reader)
        if row[0] not in _FILE_TYPES:
            raise UnknownFileTypeError(f"Unknown csv filetype: {row[0]!r}")
        ver, msr_type = _FILE_TYPES[row[0]]
        _log.info("RSA500 CSV ver %s", ver)
        header["timestamp"] = row[1]

        if ver == 0:
            _read_ver0_frequency_header(reader, header)
        else:
            _read_ver1_frequency_header(reader, header)

        _read_until(reader, lambda row: len(row) == 1 and row[0] == "[Parameters]")
        if msr_type == "spectrum":
            _read_spectrum_parameters(reader, header)
        else:
            _read_emc_emi_parameters(reader, header)

        num_points = _read_trace_header(reader, header, msr_type)
        data = _read_trace_data(reader, num_points, msr_type)

    return (header, data)
