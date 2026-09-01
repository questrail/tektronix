# tektronix

[![PyPI Version][pypi ver image]][pypi ver link]
[![Python Versions][pyversions image]][pypi ver link]
[![CI Status][ci image]][ci link]
[![Coverage Status][coveralls image]][coveralls link]
[![License Badge][license image]][LICENSE.txt]

[tektronix][] is a Python 3.12+ package providing modules and helpers to work
with data files saved by [Tektronix][tek] test equipment.

## Installation

You can install [tektronix][] either via the Python Package Index (PyPI) or
from source.

To add it to a project managed with [uv][], which records it in your
`pyproject.toml` and lock file:

```bash
$ uv add tektronix
```

Or to install it with pip:

```bash
$ pip install tektronix
```

**Source:** https://github.com/questrail/tektronix

## Supported Tektronix Equipment

Below are the modules available in the tektronix package and the compatible
equipment for each module:

- `rsa500`: RSA500 series spectrum analyzers

### Usage

`rsa500.read_csv_file()` returns the file's header as a dict and its trace as
a 1D numpy structured array with `frequency` and `amplitude` fields:

```python
from tektronix import rsa500

header, data = rsa500.read_csv_file("1M-11M.csv")
print(header["center_freq"], header["center_freq_units"])
print(data["frequency"][0], data["amplitude"][0])
```

Three file layouts are recognized, told apart by the first cell of the first
row: `Spectrum` (ver 0), `Spectrum 1` (ver 1), and `EMC-EMI 1` (ver 1). A
spectrum measurement carries a span frequency in its header, while an EMC-EMI
one carries a start and stop frequency instead.

### Sample CSV and other data files

The sample files under `tests/sample_data` are the ones the parser is tested
against, and they all come from an RSA500. If you have data files saved from
another piece of Tektronix test equipment and are willing to share them,
please open an issue or submit a pull request to let us know.

## Dependencies

See the `pyproject.toml` and `uv.lock` files for the dependency requirements.

## Contributing

Contributions are welcome! To contribute please:

1. Fork the repository
2. Create a feature branch
3. Add code and tests
4. Pass lint and tests
5. Submit a [pull request][]

## Development Setup

### Development Setup Using uv

#### Development Setup on macOS

```bash
$ brew install uv just
```

With [uv][] and [Just][] installed, development has been simplified to simply
running [Just][] to see the available commands.

```bash
$ just
```

[ruff][] and [pyright][] are deliberately absent from that line. Both are dev
dependencies pinned in `uv.lock` and reached through `uv run`, so every recipe
and every CI job uses the same version. A `brew install ruff` would put a
second, unpinned copy on the path for an editor to find, and ruff releases
change how code is formatted: the editor would then reformat code that
`ruff format --check` rejects on the next run.

#### Releasing to PyPI

`just release` cuts the release. It first checks that a release is possible at
all, then lints, type checks, and tests, then shows the entries waiting under
Unreleased and the version each kind of bump would produce, and asks which to
cut. Once answered it bumps the version, closes out the CHANGELOG, updates the
lock file, commits, and tags. Pushing the tag is what publishes.

```bash
$ just release

Releasing from 0.4.1, with these entries under Unreleased:

    ### Fixed

    - `read_csv_file()` rebuilt the whole trace array on every row.

    1) patch   0.4.1 -> 0.4.2
    2) minor   0.4.1 -> 0.5.0
    3) major   0.4.1 -> 1.0.0
    q) cancel

Which release? [1] 2

Tagged v0.5.0. Publish it with:

    git push --follow-tags
```

The entries decide the bump, so the prompt puts them next to the versions they
would produce rather than leaving the choice to memory. Answering `q`, or
anything unrecognized, changes nothing.

The tag push runs the [release workflow][], which waits on the whole [CI
workflow][ci link] before it does anything else: the 3.12, 3.13, and 3.14
matrix and the dependency floor job. `git push --follow-tags` starts both at
once, so without that wait an upload could go out while 3.14 was still running,
or already red. It then checks that the tagged commit is on `master`, since a
tag is only a pointer and one placed anywhere else would otherwise publish
whatever it points at, rechecks the tag against the version in `pyproject.toml`,
and builds.

Every check to that point runs against the source tree, so the workflow then
installs the wheel it just built somewhere `src/` is not on the path and imports
it there, which is the only step that can catch a packaging mistake that left
something out of the distribution. It uploads once that passes. There is no PyPI
API token anywhere: the workflow authenticates with [trusted publishing][], which
mints a short lived credential from the GitHub OIDC identity of that run. That
same identity signs a [PEP 740][] attestation for each distribution, which PyPI
serves beside the file it attests: trusted publishing establishes who uploaded,
and the attestation establishes what was uploaded and which workflow built it.
The upload skips anything PyPI already holds, so a run that uploaded one
distribution and then failed on the other can be retried instead of stranding a
version number that PyPI will never allow to be reused.

Uploading is followed by a [GitHub release][releases] for the tag, carrying the
CHANGELOG section for that version as its notes and the built distributions as
its assets. The notes are collected before the upload rather than after, so that
a CHANGELOG with no section for the version being released stops the release
while stopping it is still possible.

Pushing the tag is the point of no return, since PyPI never lets a version
number be reused. Everything `just release` does is local and amendable until
then, and it refuses to start against a dirty working tree, off `master`, on a
`master` behind its upstream, with a CHANGELOG whose Unreleased section is
empty, or when the tag it would create already exists. Those refusals come
before the lint and test run, so a release that cannot happen is turned away at
once rather than after the suite. A refusal leaves the version and the CHANGELOG
untouched.

`just build` runs the same checks and produces the same distributions without
releasing anything, which is the way to inspect what CI would upload.

This depends on one piece of configuration that lives outside the repository. A
[trusted publisher][trusted publishing] has to be registered for `tektronix` on
PyPI, pointing at the `questrail/tektronix` repository, the `release.yml`
workflow, and the `pypi` environment. It is a one time setup per project.

## License

[tektronix][] is released under the MIT license. Please see the
[LICENSE.txt][] file for more information.

[ci image]: https://github.com/questrail/tektronix/actions/workflows/ci.yml/badge.svg?branch=master
[ci link]: https://github.com/questrail/tektronix/actions/workflows/ci.yml
[coveralls image]: https://coveralls.io/repos/github/questrail/tektronix/badge.svg?branch=master
[coveralls link]: https://coveralls.io/github/questrail/tektronix?branch=master
[just]: https://just.systems/
[LICENSE.txt]: https://github.com/questrail/tektronix/blob/master/LICENSE.txt
[license image]: https://img.shields.io/pypi/l/tektronix.svg
[PEP 740]: https://peps.python.org/pep-0740/
[pull request]: https://help.github.com/articles/using-pull-requests
[pypi ver image]: https://img.shields.io/pypi/v/tektronix.svg
[pypi ver link]: https://pypi.python.org/pypi/tektronix
[pyright]: https://microsoft.github.io/pyright/
[pyversions image]: https://img.shields.io/pypi/pyversions/tektronix.svg
[release workflow]: https://github.com/questrail/tektronix/blob/master/.github/workflows/release.yml
[releases]: https://github.com/questrail/tektronix/releases
[ruff]: https://docs.astral.sh/ruff/
[tek]: https://www.tek.com/
[tektronix]: https://github.com/questrail/tektronix
[trusted publishing]: https://docs.pypi.org/trusted-publishers/
[uv]: https://docs.astral.sh/uv/
