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

import argparse
import collections
import json
import logging
import subprocess
from typing import Any, DefaultDict, Dict, Optional, Set

import case_utils
from case_utils.inherent_uuid import get_facet_uriref
from case_utils.local_uuid import local_uuid
from case_utils.namespace import (
    NS_RDF,
    NS_RDFS,
    NS_UCO_CORE,
    NS_UCO_IDENTITY,
    NS_UCO_OBSERVABLE,
    NS_XSD,
)
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.util import guess_format

NS_WD = Namespace("http://www.wikidata.org/entity/")


class SystemProfileMapper:
    def __init__(
        self,
        *args: Any,
        kb_prefix: str = "kb",
        kb_prefix_iri: str = "http://example.org/kb/",
        n_device: Optional[URIRef] = None,
        n_manufacturer: Optional[URIRef] = NS_WD.Q312,
        use_deterministic_uuids: bool = False,
        **kwargs: Any,
    ) -> None:
        """
        :param n_manufacturer: If not set to None, this URIRef will be assigned as the manufacturer of the device.  If not specified, the Wikidata IRI for Apple is used.
        :param n_device: If provided, this URIRef will be assumed to be defined (i.e. typed) in a graph external to this process.
        """
        self._ns_kb = Namespace(kb_prefix_iri)

        self._graph = Graph()
        self.graph.bind("kb", self.ns_kb)
        self.graph.bind("uco-core", NS_UCO_CORE)
        self.graph.bind("uco-identity", NS_UCO_IDENTITY)
        self.graph.bind("uco-observable", NS_UCO_OBSERVABLE)
        self.graph.bind("wd", NS_WD)
        self.graph.bind("xsd", NS_XSD)

        self._use_deterministic_uuids = use_deterministic_uuids

        self._reviewed_sp_data_types: Set[str] = set()

        # This dictionary caches Facet references, necessary for when
        # deterministic UUIDs are NOT requested.
        # Key: URIRef of UcoObject.
        # Value: Dictionary.
        #   Key: Specific class of Facet.
        #   Key: URIRef of Facet for the outer-keyed UcoObject.
        self._n_uco_object_facet_by_class: DefaultDict[
            URIRef, Dict[URIRef, URIRef]
        ] = collections.defaultdict(dict)

        self._n_device: Optional[URIRef] = None
        if n_device is not None:
            self._n_device = n_device

        if n_manufacturer is not None:
            # Link Apple as hardware and operating system manufacturer.
            self.graph.add((n_manufacturer, NS_RDF.type, NS_UCO_IDENTITY.Organization))
            self.graph.add(
                (
                    n_manufacturer,
                    NS_RDFS.label,
                    Literal("Apple Computer, Inc.", lang="en"),
                )
            )
            n_device_facet = self.get_uco_object_facet(
                self.n_device, NS_UCO_OBSERVABLE.DeviceFacet
            )
            self.graph.add(
                (n_device_facet, NS_UCO_OBSERVABLE.manufacturer, n_manufacturer)
            )

    def map_SPHardwareDataType(
        self, filepath: Optional[str] = None, *args: Any, **kwargs: Any
    ) -> None:
        """
        Expected values for the machine_model key might be listed on this page:
        https://support.apple.com/en-us/HT201300
        """
        obj = self.retrieve_datatype_object("SPHardwareDataType", filepath)

        _SPHardwareDataType_items: Dict[str, str] = obj["SPHardwareDataType"][0]
        n_device_facet = self.get_uco_object_facet(
            self.n_device, NS_UCO_OBSERVABLE.DeviceFacet
        )
        self.graph.add(
            (
                n_device_facet,
                NS_RDFS.seeAlso,
                URIRef("https://support.apple.com/en-us/HT201300"),
            )
        )
        self.graph.add(
            (
                n_device_facet,
                NS_UCO_OBSERVABLE.deviceType,
                Literal(_SPHardwareDataType_items["machine_name"]),
            )
        )
        self.graph.add(
            (
                n_device_facet,
                NS_UCO_OBSERVABLE.model,
                Literal(_SPHardwareDataType_items["machine_model"]),
            )
        )
        self.graph.add(
            (
                n_device_facet,
                NS_UCO_OBSERVABLE.serialNumber,
                Literal(_SPHardwareDataType_items["serial_number"]),
            )
        )
        # TODO - These other keys of the JSON dictionary were observed,
        # but not yet mapped, and are trimmed from test samples pending
        # testing infrastructure.
        #
        # activation_lock_status
        # boot_rom_version
        # cpu_type
        # current_processor_speed
        # l2_cache_core
        # l3_cache
        # number_processors
        # os_loader_version
        # packages
        # physical_memory
        # platform_cpu_htt
        # platform_UUID
        # provisioning_UDID

    def get_uco_object_facet(
        self, n_uco_object: URIRef, n_facet_class: URIRef
    ) -> URIRef:
        if n_facet_class not in self._n_uco_object_facet_by_class[n_uco_object]:
            # See if graph already has the Facet defined, to avoid second definition.
            found = False
            n_facet: URIRef
            for n_object in self.graph.objects(n_uco_object, NS_UCO_CORE.hasFacet):
                assert isinstance(n_object, URIRef)
                n_facet = n_object
                for triple in self.graph.triples((n_facet, NS_RDF.type, n_facet_class)):
                    self._n_uco_object_facet_by_class[n_uco_object][
                        n_facet_class
                    ] = n_facet
                if found:
                    break
            if n_facet_class not in self._n_uco_object_facet_by_class[n_uco_object]:
                # Define new Facet node according to whether deterministic UUIDs were requested.
                if self.use_deterministic_uuids:
                    n_facet = get_facet_uriref(
                        n_uco_object, n_facet_class, namespace=self.ns_kb
                    )
                else:
                    facet_fragment = n_facet_class.fragment
                    if facet_fragment == "":
                        facet_fragment = n_facet_class.split("/")[-1]
                    n_facet = self.ns_kb[facet_fragment + "-" + local_uuid()]

            # Idempotently type and link Facet.
            self.graph.add((n_facet, NS_RDF.type, n_facet_class))
            self.graph.add((n_uco_object, NS_UCO_CORE.hasFacet, n_facet))

            # Encache.
            self._n_uco_object_facet_by_class[n_uco_object][n_facet_class] = n_facet
        return self._n_uco_object_facet_by_class[n_uco_object][n_facet_class]

    def retrieve_datatype_object(
        self,
        sp_datatype: str,
        filepath: Optional[str] = None,
        *args: Any,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        :param filepath: If provided, is assumed to be the recorded output of the system_profiler that would be run if this were not provided.  The loaded JSON dictionary is checked to confirm it does contain the requested key.
        """
        self._reviewed_sp_data_types.add(sp_datatype)
        if filepath is None:
            # TODO Tie provenance as subprocess.
            completed_process = subprocess.run(
                ["system_profiler", "-json", "-detailLevel", "full", sp_datatype],
                stdout=subprocess.PIPE,
                text=True,
            )
            assert completed_process.returncode == 0
            obj = json.loads(completed_process.stdout)
        else:
            with open(filepath, "r") as in_fh:
                obj = json.load(in_fh)
        assert isinstance(obj, dict)
        assert sp_datatype in obj
        for key in obj.keys():
            assert isinstance(key, str)
        return obj

    @property
    def graph(self) -> Graph:
        """No setter."""
        return self._graph

    @property
    def n_device(self) -> URIRef:
        """
        The system that is the inspected subject of the system_profiler command.

        No setter.  Initialized on first access.  Can instead be initialized to preferred value in SystemProfileMapper constructor.
        """
        if self._n_device is None:
            self._n_device = self.ns_kb["AppleDevice-" + local_uuid()]
            self.graph.add((self.n_device, NS_RDF.type, NS_UCO_OBSERVABLE.AppleDevice))
            self.graph.add((self.n_device, NS_RDF.type, NS_UCO_OBSERVABLE.Computer))
        return self._n_device

    @property
    def ns_kb(self) -> Namespace:
        """
        Knolwedge base namespace.

        No setter.  Can be initialized to preferred value in SystemProfileMapper constructor.
        """
        return self._ns_kb

    @property
    def use_deterministic_uuids(self) -> bool:
        """No setter."""
        return self._use_deterministic_uuids


def main() -> None:
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument("--debug", action="store_true")
    argument_parser.add_argument(
        "--SPHardwareDataType-json", help="Path to cached SPHardwareDataType JSON file."
    )
    argument_parser.add_argument(
        "--device-iri",
        help="IRI to use for the subject AppleDevice.  If not provided, an IRI will be generated.",
    )
    argument_parser.add_argument(
        "--kb-prefix",
        default="kb",
        help="Prefix label to use for knowledge-base individuals.  E.g. with defaults, 'http://example.org/kb/Thing-1' would compact to 'kb:Thing-1'.",
    )
    argument_parser.add_argument(
        "--kb-prefix-iri",
        default="http://example.org/kb/",
        help="Prefix IRI to use for knowledge-base individuals.  E.g. with defaults, 'http://example.org/kb/Thing-1' would compact to 'kb:Thing-1'.",
    )
    argument_parser.add_argument(
        "--output-format", help="Override extension-based format guesser."
    )
    argument_parser.add_argument(
        "--use-deterministic-uuids",
        action="store_true",
        help="Use UUIDs computed using the case_utils.inherent_uuid module.",
    )
    argument_parser.add_argument(
        "out_graph",
        help="A self-contained RDF graph file, in the format either requested by --output-format or guessed based on extension.",
    )
    args = argument_parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)

    case_utils.local_uuid.configure()

    system_profile_mapper = SystemProfileMapper(
        kb_prefix=args.kb_prefix,
        kb_prefix_iri=args.kb_prefix_iri,
        n_device=args.device_iri,
        use_deterministic_uuids=args.use_deterministic_uuids is True,
    )

    system_profile_mapper.map_SPHardwareDataType(args.SPHardwareDataType_json)

    # Write output file.
    output_format = (
        guess_format(args.out_graph)
        if args.output_format is None
        else args.output_format
    )

    system_profile_mapper.graph.serialize(args.out_graph, format=output_format)


if __name__ == "__main__":
    main()
