import dataclasses
from typing import Dict, List, Optional, Set, Union

import radix

from .status import RouteEntry, RPKIStatus


def validate(
    route: RouteEntry,
    roa_tree: radix.Radix,
    communities_expected_invalid: Set[str],
    verbose=False,
) -> Optional[
    Dict[
        str,
        Union[RPKIStatus, Dict[str, Union[str, int]], List[Dict[str, Union[str, int]]]],
    ]
]:
    """
    Validate a provided RouteEntry, using the roa's in a radix tree.
    If the route is invalid, or verbose is set, returns a dictionary
    with the details of the status, route, and all relevant ROAs.
    Returns None otherwise.
    """
    status = RPKIStatus.invalid

    rnodes = roa_tree.search_covering(route.prefix)
    if not rnodes:
        status = RPKIStatus.not_found

    for rnode in rnodes:
        for roa in rnode.data["roas"]:
            prefix_length = int(route.prefix.split("/")[1])
            if route.origin and route.origin == roa["asn"] and prefix_length <= roa["max_length"]:
                status = RPKIStatus.valid

    if status == RPKIStatus.invalid and route.communities.intersection(
        communities_expected_invalid
    ):
        status = RPKIStatus.invalid_expected

    if status == RPKIStatus.invalid or verbose:
        roa_dicts = []
        for rnode in rnodes:
            for roa in rnode.data["roas"]:
                roa_dicts.append(
                    {
                        "prefix": rnode.prefix,
                        "asn": roa["asn"],
                        "max_length": roa["max_length"],
                    }
                )
        return {
            "status": status,
            "route": dataclasses.asdict(route),
            "roas": roa_dicts,
        }
    return None
