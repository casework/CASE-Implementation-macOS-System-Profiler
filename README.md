# CASE Implementation: macOS System Profiler

[![Continuous Integration](https://github.com/casework/CASE-Implementation-macOS-System-Profiler/actions/workflows/ci.yml/badge.svg)](https://github.com/casework/CASE-Implementation-macOS-System-Profiler/actions/workflows/ci.yml)
![CASE Version](https://img.shields.io/badge/CASE%20Version-1.2.0-green)


## Disclaimer

Participation by NIST in the creation of the documentation of mentioned software is not intended to imply a recommendation or endorsement by the National Institute of Standards and Technology, nor is it intended to imply that any specific software is necessarily the best available for the purpose.


## Usage

To install this software, clone this repository, and run `pip install .` from within this directory.  (You might want to do this in a virtual environment.)

This provides a standalone command:

```bash
case_macos_system_profiler output.json
```

If provided no arguments, the default behavior is to invoke `system_profiler` and render its observations about the current operating system environment.

For testing purposes, runtime modes are available to review specific data types from recorded `system_profiler` output.  E.g. this pipeline, exercised under [`tests/cli`](tests/cli/), reviews the `SPHardwareDataType` output:

```bash
system_profiler \
  -detailLevel full \
  -json \
  SPHardwareDataType \
  > tmp.json
case_macos_system_profiler \
  --SPHardwareDataType-json tmp.json \
  output.json
```

Tests are run on sanitized sample JSON files.


## Versioning

This project follows [SEMVER 2.0.0](https://semver.org/) where versions are declared.


## Make targets

Some `make` targets are defined for this repository:
* `all` - Installs `pre-commit` for this cloned repository instance.
* `check` - Run unit tests.  *NOTE*: The tests entail an installation of this project's source tree, including prerequisites downloaded from PyPI.
* `clean` - Remove test build files.


## Licensing

This repository is licensed under the Apache 2.0 License. See [LICENSE](LICENSE).

Portions of this repository contributed by NIST are governed by the [NIST Software Licensing Statement](THIRD_PARTY_LICENSES.md#nist-software-licensing-statement).
