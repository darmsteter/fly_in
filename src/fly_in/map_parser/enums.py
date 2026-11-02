from enum import StrEnum
from math import inf


class MapKey(StrEnum):
    """Keys identifying directives in the map file."""

    NB_DRONES = "nb_drones"
    START_HUB = "start_hub"
    END_HUB = "end_hub"
    HUB = "hub"
    CONNECTION = "connection"


class MetadataKey(StrEnum):
    """Keys identifying metadata attributes in the map file."""

    COLOR = "color"
    ZONE = "zone"
    MAX_DRONES = "max_drones"
    MAX_LINK_CAPACITY = "max_link_capacity"


class ZoneEnum(StrEnum):
    """Types of zones and their associated traversal costs."""

    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"

    def get_traversal_cost(self) -> float:
        """Return the cost of traversing this zone.

        Blocked zones have infinite cost and cannot be traversed.
        """
        return {
            ZoneEnum.NORMAL: 1.0,
            ZoneEnum.BLOCKED: inf,
            ZoneEnum.RESTRICTED: 2.0,
            ZoneEnum.PRIORITY: 0.99,
        }[self]
