#!/usr/bin/make -f

# Portions of this file contributed by NIST are governed by the
# following statement:
#
# This software was developed at the National Institute of Standards
# and Technology by employees of the Federal Government in the course
# of their official duties. Pursuant to Title 17 Section 105 of the
# United States Code, this software is not subject to copyright
# protection within the United States. NIST assumes no responsibility
# whatsoever for its use by other parties, and makes no guarantees,
# expressed or implied, about its quality, reliability, or any other
# characteristic.
#
# We would appreciate acknowledgement if the software is used.

SHELL := /bin/bash

top_srcdir := $(shell cd ../.. ; pwd)

all: \
  SPHardwareDataType.ttl

.PHONY: \
  check-pytest

EXAMPLE-system_profiler-SPHardwareDataType.json:
	@echo "ERROR:$@ not found.  To avoid accidental commits of device-identifying information, please modify this Makefile to remove the following, halting 'exit'; run 'make' again; and carefully review and/or sanitize the generated JSON file before committing." >&2
	exit 1
	rm -f _$@ __$@
	system_profiler \
	  -detailLevel full \
	  -json \
	  SPHardwareDataType \
	  > __$@
	python3 -m json.tool \
	  __$@ \
	  _$@
	rm __$@
	mv _$@ $@

SPHardwareDataType.ttl: \
  EXAMPLE-system_profiler-SPHardwareDataType.json \
  $(top_srcdir)/case_macos_system_profiler/__init__.py \
  $(top_srcdir)/case_macos_system_profiler/cli.py \
  $(top_srcdir)/tests/.venv.done.log
	export CASE_DEMO_NONRANDOM_UUID_BASE="$(top_srcdir)" \
	  && source $(top_srcdir)/tests/venv/bin/activate \
	    && case_macos_system_profiler \
	      --SPHardwareDataType-json $< \
	      --use-deterministic-uuids \
	      _$@
	source $(top_srcdir)/tests/venv/bin/activate \
	  && case_validate \
	    --allow-infos \
	    _$@
	mv _$@ $@

check: \
  check-pytest

check-pytest: \
  all
	source $(top_srcdir)/tests/venv/bin/activate \
	  && pytest \
	    --log-level=DEBUG

clean:
	@rm -rf \
	  *.ttl \
	  .pytest_cache
