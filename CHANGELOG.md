# CHANGELOG.md

This file contains all notable changes to the [tektronix][] project.

## Unreleased

### Added

- `just release-check`, which runs the refusals `just release` opens with and
  stops there: a dirty working tree, a branch other than `master`, a `master`
  behind its upstream, an empty `Unreleased` section. Asking whether a release
  can be cut no longer means starting one and reading the error.
- `just doc`, which searches pydoc for a given term.
- Ignore `.pypirc`. A copy holding a PyPI username and password predates the
  move to trusted publishing, which mints a short lived credential per
  release and leaves nothing on disk; nothing here needs the file, and
  ignoring it keeps a leftover from being committed by accident.

### Changed

- `read_csv_file` raises `UnknownFileTypeError` on a first cell it does not
  recognize, where it called `sys.exit(1)`. A library has no business ending
  the caller's process over a bad file: an application reading a directory of
  captures lost the run on the first stray one, with no way to catch it and
  skip. The new exception subclasses `ValueError` and is exported from the
  package. The `logging.error` that preceded the exit is gone, the message
  having moved onto the exception, where a caller who is not listening to
  logging can still read it.

- `just build` and `just release` depend on `cov` rather than `test`. CI runs
  pytest under coverage and fails below the `fail_under` floor in
  `pyproject.toml`, so the bare suite these recipes ran left that gate as one
  they never applied: a tree that passed locally could still be rejected on
  push, and `just release` could tag a version CI would then refuse to publish.
- The CHANGELOG parser that reads the `Unreleased` section moved out of
  `release` and into a private `unreleased` recipe. `release-check` and
  `release` both read it, one to refuse an empty section and the other to show
  what is about to ship, so it is written once rather than inlined in each.
- Bring the `LICENSE.txt` copyright range up to 2026. It had stopped at
  2022, years behind the work in the file.
- Widen the ruff per-file-ignores glob from `tests/*` to `tests/**`. The
  single star matches only the top level of `tests/`, so a test added in a
  subdirectory would have silently lost the `PLR2004` exemption the flat
  files rely on.
- Promote "Releasing to PyPI" in the README from a fourth level heading to a
  third. It had been nested under "Development Setup on macOS", which made
  releasing look like a macOS specific topic.

### Removed

- `AUTHORS.md`, and the "(see AUTHORS.md file)" clause in `LICENSE.txt` that
  pointed at it. It listed one author with "None at this time" under both
  Maintainers and Contributors, which `pyproject.toml` already records in
  its `authors` field.

## v0.5.0 - 2026-09-01

### Added

- Test, lint, and type check on every push through a [CI workflow][], across
  Python 3.12, 3.13, and 3.14. The `.travis.yml` that was here had been
  pointing at travis-ci.org, which shut down, so nothing had actually run
  against a push in years and the badge in the README linked to a service
  that no longer answers.
- Check the lowest dependency versions `pyproject.toml` allows in a job of
  its own. The version floors are a promise to anyone installing tektronix
  alongside something else that holds numpy back, and the matrix never
  tested them: it installs whatever `uv.lock` pins, which is the newest
  numpy rather than the oldest allowed one.
- Audit the workflows with [zizmor][] in CI and in `just lint`. They are the
  part of this repository that can mint a PyPI credential, and everything
  else here is linted on every push.
- Publish from a tag through a [release workflow][] using [trusted
  publishing][], which mints a short lived credential from the GitHub OIDC
  identity of the run, so there is no PyPI API token to store, rotate, or
  leak. That same identity signs a [PEP 740][] attestation for each
  distribution. The workflow waits on the whole CI workflow, checks the
  tagged commit is on `master`, checks the tag against the version in
  `pyproject.toml`, smoke tests the built wheel, and creates a GitHub
  release carrying this file's section for that version as its notes.
- Smoke test the built wheel from outside the source tree, in
  `scripts/smoke_test_wheel.py`. Every other check runs against `src/`, so a
  packaging mistake that left a module or `py.typed` out of the distribution
  would have passed all of them and shipped.
- Ship `py.typed` and annotate the public API, so that a project depending on
  tektronix type checks against real signatures rather than `Any`.
- Put the actions and the Python dependencies under Dependabot. The actions
  are pinned to commit SHAs, and a pin with nothing updating it is a decision
  to stay on one commit forever.
- Report coverage to Coveralls from CI, with a 100% floor enforced by
  `pytest --cov`. The floor is set at what the suite already covers, so
  uncovered code now has to arrive with either a test or a deliberate edit.
- Test that an unrecognized file type stops the read. The three recognized
  layouts are told apart by the first cell of the first row alone, and
  nothing had covered what happens to a file that matches none of them.

### Changed

- Replace the `invoke` tasks and `requirements.txt` with [uv][] and a
  [Just][] recipe file, and lock the dependencies in `uv.lock`. The
  requirements file was a `pip-chill` dump that pinned the dev tools without
  distinguishing them from the runtime dependency, and it named `nose`,
  which has not run on a supported Python in years.
- Cut releases with `just release`, which refuses to start against a dirty
  working tree, off `master`, on a `master` behind its upstream, with an
  empty Unreleased section, or when the tag it would create already exists.
  It then shows the entries waiting here beside the version each kind of
  bump would produce and asks which to cut. The `invoke release` task it
  replaces took the version as an argument and trusted it, and pushed the
  tag itself before anything had been checked.
- Lint and format with [ruff][] and type check with [pyright][], both pinned
  in `uv.lock` and reached through `uv run`, so a recipe and a CI job use the
  same version. The `black` and `pylint` configuration this replaces
  configured tools that were not installed, and the pyright section pointed
  at `src/web`, `src/sdk`, and `src/typestubs`, none of which exist here.
- Run the suite with pytest rather than `nose2`, and locate the sample data
  with `pathlib` rather than `unipath`, which was an undeclared dependency of
  the tests and has not been released since 2014.
- Split the CSV parser into named helpers, one per section of the file. It
  had been one function of 88 statements and 21 branches, in which the
  meaning of a row depended on how many `next(reader)` calls had already
  gone by.
- Require Python 3.12 and numpy 2.2. The package claimed 3.9 while the CI
  configuration tested 3.8, and neither is supported upstream any more.
- Date the entries below in ISO format, which is what the release workflow
  reads when it collects the notes for a GitHub release.

### Fixed

- `read_csv_file()` rebuilt the entire trace array inside the row loop,
  reallocating and recopying every point read so far on each of the up to
  2401 rows in a file. It is built once now, after the loop, which also
  means a file whose header claims no points at all returns an empty array
  rather than raising `NameError` on an unbound local.

### Removed

- `tasks.py`, `requirements.txt`, and `.travis.yml`, replaced by the
  `Justfile`, `uv.lock`, and the workflows under `.github/`.

## v0.4.1 - 2025-11-11

- Fixed reading `EMC-EMI 1` file formats.

## v0.4.0 - 2025-11-11

- Updated code to handle `EMC-EMI 1` in the first row of the CSV file.

## v0.3.1 - 2024-12-04

- Switched to hatch for build and deployment.
- Updated package requirements.

## v0.2.0 - 2024-11-20

- Added code and test for ver 1 of the RSA500 CSV file format.

## v0.1.0 - 2023-10-30

- Initial release for RSA500

[CI workflow]: https://github.com/questrail/tektronix/actions/workflows/ci.yml
[just]: https://just.systems/
[PEP 740]: https://peps.python.org/pep-0740/
[pyright]: https://microsoft.github.io/pyright/
[release workflow]: https://github.com/questrail/tektronix/blob/master/.github/workflows/release.yml
[ruff]: https://docs.astral.sh/ruff/
[tektronix]: https://github.com/questrail/tektronix
[trusted publishing]: https://docs.pypi.org/trusted-publishers/
[uv]: https://docs.astral.sh/uv/
[zizmor]: https://docs.zizmor.sh/
