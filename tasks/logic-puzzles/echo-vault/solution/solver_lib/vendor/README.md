# Offline CP-SAT runtime

These unmodified native files are from the PyPI `ortools==9.15.6755` CPython 3.12 / manylinux_2_27_x86_64 wheel. The wheel's LICENSE, METADATA, WHEEL and RECORD accompany them. The `ortools/.libs` and `ortools.libs` trees contain the wheel's linked native dependencies. Source: https://github.com/google/or-tools (release 9.15); distribution: https://pypi.org/project/ortools/9.15.6755/ .

Only `cp_model_helper` and `sorted_interval_list` are used. `engine.py` constructs the documented model protobuf directly; it does not import the high-level pandas-based wrapper, install packages, fetch files or access the network. A `python -S` run with no site packages verifies this. The checked benchmark target is Linux x86-64, Python 3.12; other architectures/Python ABIs would require the matching official runtime, and have not been tested.

This is an explicit bundled implementation dependency, not a dependency expected to be installed in the solver environment. No proprietary puzzle data or solutions are included here. File hashes are in `sha256.json`.

## Licenses and source availability

[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) identifies every bundled native
component, embedded build dependencies, their licenses, and versioned source
and integration-patch links. Full upstream license texts are included in
[licenses/](licenses/README.md). The project license does not replace the
component licenses. All 110 native files and five Python files match the
official wheel byte-for-byte; the license documentation does not modify them.
