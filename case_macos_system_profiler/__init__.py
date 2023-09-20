#!/usr/bin/env python3

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

__version__ = "0.0.1"


def suffixed_bytes_number_to_integer(suffixed_number: str) -> int:
    """
    >>> suffixed_bytes_number_to_integer("1 KB")
    1024
    """
    parts = suffixed_number.split(" ")
    multiplier = {
        "KB": 2**10,
        "MB": 2**20,
        "GB": 2**30,
        "TB": 2**40,
    }[parts[1]]
    lhs = int(parts[0])
    return lhs * multiplier
