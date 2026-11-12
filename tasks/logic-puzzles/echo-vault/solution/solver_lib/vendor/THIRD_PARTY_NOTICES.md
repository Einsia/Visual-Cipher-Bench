# OR-Tools runtime: third-party notices

## Distribution and scope

This directory contains an unchanged subset of the official PyPI OR-Tools
9.15.6755 wheel for CPython 3.12 / Linux x86-64:

`ortools-9.15.6755-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl`

Wheel SHA-256: `033836c0eb33bc72697a299e0caedbb25fc9d1cee0b13832d69cb30405f57b3e`.
[Distribution and download](https://pypi.org/project/ortools/9.15.6755/#files).

All 110 bundled ELF libraries and five Python package files were compared
byte-for-byte with this wheel on 2026-11-13. No native binaries were rebuilt,
removed, or patched by Visual Cipher Bench. The original wheel's `METADATA`,
`WHEEL`, and `RECORD` are retained; `RECORD` describes the complete upstream
wheel, including files outside this selected subset. [sha256.json](sha256.json)
is the manifest of the files actually distributed here, excluding itself.

The two Python extensions load `libortools.so.9` and its linked libraries,
including backends not invoked by the Echo Vault solver. Their licenses still
apply to distribution. These components retain the following terms and are
excluded from the project's Apache-2.0 / CC BY 4.0 grants. Copyright and
permission notices are retained in the linked license texts and source.

## Native component inventory

Versions below follow the OR-Tools v9.15 dependency declarations, cross-checked
against the wheel and its library names. The number of files covers all 110
bundled ELF objects; build-time and embedded code is credited separately below.

| Component / upstream attribution | Bundled files | Version | License text |
| --- | --- | --- | --- |
| OR-Tools — Google LLC | `libortools.so.9`, `cp_model_helper`, `sorted_interval_list` (3) | 9.15.6755 | [Apache-2.0](LICENSE-ORTools) |
| Abseil — The Abseil Authors | All `libabsl_*.so*` in both library directories (91) | 20250814.1 | [Apache-2.0](LICENSE-ORTools) |
| Protocol Buffers — Google Inc. | `libprotobuf.so.33.1.0` (1) | 33.1 | [BSD-3-Clause](licenses/LICENSE-Protobuf.txt) |
| utf8_range — Yibo Cai and Google LLC | `libutf8_validity.so.33.1.0` (1) | bundled with Protobuf 33.1 | [MIT](licenses/LICENSE-UTF8-Range.txt) |
| RE2 — Google Inc. | `libre2.so.11` (1) | 2025-08-12 | [BSD-3-Clause](licenses/LICENSE-RE2.txt) |
| COIN-OR Cbc contributors | `libCbc.so.2`, `libCbcSolver.so.2`, `libOsiCbc.so.2` (3) | 2.10.12 | [EPL-1.0](licenses/LICENSE-EPL-1.0.txt); see scope below |
| COIN-OR Cgl contributors | `libCgl.so.0` (1) | 0.60.9 | [EPL-1.0](licenses/LICENSE-EPL-1.0.txt); see scope below |
| COIN-OR Clp contributors | `libClp.so.1`, `libClpSolver.so.1`, `libOsiClp.so.1` (3) | 1.17.10 | [EPL-1.0](licenses/LICENSE-EPL-1.0.txt); see scope below |
| COIN-OR CoinUtils contributors | `libCoinUtils.so.2` (1) | 2.11.12 | [EPL-1.0](licenses/LICENSE-EPL-1.0.txt); see scope below |
| COIN-OR Osi contributors | `libOsi.so.0` (1) | 0.108.11 | [EPL-1.0](licenses/LICENSE-EPL-1.0.txt); see scope below |
| HiGHS contributors | `libhighs.so.1` (1) | 1.12.0 | [MIT](licenses/LICENSE-HiGHS.txt) |
| SCIP — Zuse Institute Berlin and contributors | `libscip.so.10.0` (1) | 10.0.0 | [Apache-2.0](LICENSE-ORTools) |
| zlib — Jean-loup Gailly and Mark Adler | `libz.so.1` (1) | 1.3.1 | [zlib](licenses/LICENSE-zlib.txt) |
| bzip2 — Julian R Seward; Federico Mena Quintero; Micah Snyder | `libbz2.so.1` (1) | binary version string 1.1.0 | [bzip2-1.0.6](licenses/LICENSE-bzip2.txt) |

The pinned COIN-OR forks contain **EPL-1.0 in each component subdirectory** and
**EPL-2.0 at the repository root**. Both original texts are included. The table
uses the component license for the libraries; the root build material retains
[EPL-2.0](licenses/LICENSE-EPL-2.0.txt). These files are not relabeled Apache-2.0.

OR-Tools selected bzip2's development `master`, rather than an immutable tag.
The bundled library reports 1.1.0 and the copied upstream `COPYING` identifies
that development version. The precise source commit used by the wheel builder
is not recorded in its metadata; this notice does not claim to reconstruct it.

## Embedded and build-time components

The upstream build also uses the following header or embedded dependencies.
They may not appear as separate shared libraries. The notices cover the build
inputs and embedded components identified in that release.

| Component / attribution | Source version or location | License text |
| --- | --- | --- |
| Eigen contributors; Intel Corporation for its BSD code | Eigen 3.4.0, OR-Tools build sets `EIGEN_MPL2_ONLY=ON` | [MPL-2.0](licenses/LICENSE-Eigen-MPL-2.0.txt), [BSD](licenses/LICENSE-Eigen-BSD.txt) |
| pybind11 — The Pybind Development Team | 2.13.6 | [BSD-3-Clause](licenses/LICENSE-pybind11.txt) |
| pybind11_abseil — The Pybind Development Team | v202402.0 | [BSD-3-Clause notice](licenses/LICENSE-pybind11-abseil.txt) |
| pybind11_protobuf — The Pybind Development Team | f02a2b7653bc50eb5119d125842a3870db95d251 | [BSD-3-Clause notice](licenses/LICENSE-pybind11-protobuf.txt) |
| SoPlex — Zuse Institute Berlin and contributors | 8.0.0, compiled into SCIP | [Apache-2.0](LICENSE-ORTools) |
| Boost contributors | 1.87.0, multiprecision / serialization build dependencies | [BSL-1.0](licenses/LICENSE-Boost.txt) |
| TCLIQUE — Zuse Institute Berlin | SCIP `src/tclique` | [Copyright notice](licenses/NOTICE-TCLIQUE.txt), [Apache-2.0](LICENSE-ORTools) |
| TinyCThread — Marcus Geelnard and Evan Nemerson | SCIP `src/tinycthread` | [zlib-style notice](licenses/LICENSE-TinyCThread.txt) |
| fmt — Victor Zverovich | SoPlex `src/soplex/external/fmt` | [MIT notice](licenses/LICENSE-fmt.txt) |
| zstr — Matei David, Ontario Institute for Cancer Research | SoPlex `src/soplex/external/zstr`; HiGHS `extern/zstr` | [MIT](licenses/LICENSE-zstr.txt) |
| FilereaderLP — Michael Feldmeier | HiGHS `extern/filereaderlp` | [MIT](licenses/LICENSE-FilereaderLP.txt) |
| pdqsort — Orson Peters | HiGHS `extern/pdqsort` | [zlib-style notice](licenses/LICENSE-pdqsort.txt) |

The Linux C/C++ runtime libraries (`libc`, `libm`, `libdl`, `libpthread`, `librt`,
`libstdc++`, `libgcc_s`, and the ELF loader) are resolved from the execution
image and are not copied into this vendor directory.

## Obtaining the source

Source code for the bundled components is available without charge from the
versioned upstream links below. COIN-OR source is supplied under its EPL terms;
Eigen source is supplied under MPL-2.0 and its applicable per-file notices.
Retain those notices when redistributing source. The repository's project
licenses do not restrict recipients' rights under those component licenses.

OR-Tools' build applies upstream integration patches to some dependencies.
The source references below must be used together with the linked patches;
they are not a claim that the wheel was built from unpatched release archives.
Visual Cipher Bench has made no further changes to these binaries or sources.
The build configuration and all patches are available in the fixed
[OR-Tools source snapshot](https://github.com/google/or-tools/tree/551ad10d94835c99e5e1e684500d3db398c0e345),
including its
[dependency declarations](https://github.com/google/or-tools/blob/551ad10d94835c99e5e1e684500d3db398c0e345/cmake/dependencies/CMakeLists.txt).

| Component | Source | OR-Tools integration patch |
| --- | --- | --- |
| Abseil | [Source](https://github.com/abseil/abseil-cpp/tree/20250814.1) | [Patch](https://github.com/google/or-tools/blob/551ad10d94835c99e5e1e684500d3db398c0e345/patches/abseil-cpp-20250814.1.patch) |
| Protobuf / utf8_range | [Source](https://github.com/protocolbuffers/protobuf/tree/v33.1) | [Patch](https://github.com/google/or-tools/blob/551ad10d94835c99e5e1e684500d3db398c0e345/patches/protobuf-v33.1.patch) |
| RE2 | [Source](https://github.com/google/re2/tree/2025-08-12) | [Patch](https://github.com/google/or-tools/blob/551ad10d94835c99e5e1e684500d3db398c0e345/patches/re2-2025-08-12.patch) |
| HiGHS | [Source](https://github.com/ERGO-Code/HiGHS/tree/v1.12.0) | None listed |
| SCIP | [Source](https://github.com/scipopt/scip/tree/v10.0.0) | [Patch](https://github.com/google/or-tools/blob/551ad10d94835c99e5e1e684500d3db398c0e345/patches/scip-v10.0.0.patch) |
| SoPlex | [Source](https://github.com/scipopt/soplex/tree/v8.0.0) | [Patch](https://github.com/google/or-tools/blob/551ad10d94835c99e5e1e684500d3db398c0e345/patches/soplex-v8.0.0.patch) |
| Eigen | [Source](https://gitlab.com/libeigen/eigen/-/tree/3.4.0) | [Patch](https://github.com/google/or-tools/blob/551ad10d94835c99e5e1e684500d3db398c0e345/patches/eigen3-3.4.0.patch) |
| Boost | [Source](https://github.com/boostorg/boost/tree/boost-1.87.0) | [Patch](https://github.com/google/or-tools/blob/551ad10d94835c99e5e1e684500d3db398c0e345/patches/boost-1.87.0.patch) |
| zlib | [Source](https://github.com/madler/zlib/tree/v1.3.1) | [Patch](https://github.com/google/or-tools/blob/551ad10d94835c99e5e1e684500d3db398c0e345/patches/ZLIB-v1.3.1.patch) |
| bzip2 development line | [Source](https://gitlab.com/bzip2/bzip2/-/tree/master) | [Patch](https://github.com/google/or-tools/blob/551ad10d94835c99e5e1e684500d3db398c0e345/patches/bzip2.patch) |
| pybind11 | [Source](https://github.com/pybind/pybind11/tree/v2.13.6) | [Patch](https://github.com/google/or-tools/blob/551ad10d94835c99e5e1e684500d3db398c0e345/patches/pybind11-v2.13.6.patch) |
| pybind11_abseil | [Source](https://github.com/pybind/pybind11_abseil/tree/v202402.0) | [Patch](https://github.com/google/or-tools/blob/551ad10d94835c99e5e1e684500d3db398c0e345/patches/pybind11_abseil.patch) |
| pybind11_protobuf | [Source](https://github.com/pybind/pybind11_protobuf/tree/f02a2b7653bc50eb5119d125842a3870db95d251) | None listed |
| Cbc | [Source](https://github.com/Mizux/Cbc/tree/61358ddd277362186547caff464f2266c26ced10) | [Patch](https://github.com/google/or-tools/blob/551ad10d94835c99e5e1e684500d3db398c0e345/patches/cbc-2.10.patch) |
| Cgl | [Source](https://github.com/Mizux/Cgl/tree/75d3994612b992a48574d297479d8aede41611a2) | [Patch](https://github.com/google/or-tools/blob/551ad10d94835c99e5e1e684500d3db398c0e345/patches/cgl-0.60.patch) |
| Clp | [Source](https://github.com/Mizux/Clp/tree/14ab15c7dfc59b6bdb5455d42a2d5e9e1ec28a75) | [Patch](https://github.com/google/or-tools/blob/551ad10d94835c99e5e1e684500d3db398c0e345/patches/clp-1.17.patch) |
| CoinUtils | [Source](https://github.com/Mizux/CoinUtils/tree/6fc9606ffd6b2120ba211bfec6fe99ab3db5dfd6) | [Patch](https://github.com/google/or-tools/blob/551ad10d94835c99e5e1e684500d3db398c0e345/patches/coinutils-2.11.patch) |
| Osi | [Source](https://github.com/Mizux/Osi/tree/ab3d7568384854c7c2bcd53f608c7b4b31a3f033) | [Patch](https://github.com/google/or-tools/blob/551ad10d94835c99e5e1e684500d3db398c0e345/patches/osi-0.108.patch) |

The complete source trees above include the embedded notices for SCIP,
SoPlex, HiGHS, and the binding libraries. The copied license texts and their
upstream locations and SHA-256 digests are indexed in
[licenses/README.md](licenses/README.md).

The COIN-OR components are provided under the attached EPL licenses, including
their warranty disclaimers and liability exclusions. No additional warranty,
support obligation, or liability is offered on behalf of any contributor.
Any different terms offered by Visual Cipher Bench would be its own alone.
