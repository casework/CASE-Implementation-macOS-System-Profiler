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

from pathlib import Path
from typing import Set

import case_utils.ontology
from rdflib import Graph, URIRef
from rdflib.query import ResultRow


def test_example_output_with_sparql() -> None:
    srcdir = Path(__file__).parent
    graph = Graph()
    graph.parse(srcdir / "SPHardwareDataType.ttl")

    # Augment data graph with subclass hierarchy to look for all Devices.
    case_utils.ontology.load_subclass_hierarchy(graph)

    query = """\
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX uco-observable: <https://ontology.unifiedcyberontology.org/uco/observable/>
SELECT ?nDevice
WHERE {
  ?nDevice
    a/rdfs:subClassOf* uco-observable:Device ;
    .
}
"""
    n_devices: Set[URIRef] = set()
    for result in graph.query(query):
        assert isinstance(result, ResultRow)
        assert isinstance(result[0], URIRef)
        n_devices.add(result[0])
    assert len(n_devices) == 1
