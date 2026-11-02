import re

from pydantic import ValidationError

from .colors import Color
from .enums import MapKey, MetadataKey, ZoneEnum
from .models import Connection, Hub, Network

from ..errors import MapParsingError, format_validation_error


def _parse_nb_drones(line: str) -> str:
    """Extract the drone count from a map declaration.

    Validate that the line follows the 'nb_drones: <positive_integer>'
    format.

    Args:
        line: Raw nb_drones declaration from the map file.

    Returns:
        The drone count as a string for subsequent model validation.

    Raises:
        MapParsingError: If the declaration has an invalid format.
    """
    if not re.fullmatch(rf"{MapKey.NB_DRONES}:\s*[1-9]\d*", line):
        raise MapParsingError(
            "Invalid nb_drones declaration: "
            "expected 'nb_drones: <positive_integer>'."
        )
    _, value = line.split(":", 1)
    return value.strip()


def _parse_metadata_item(
        item: str,
        is_regular_hub: bool,
        hub_name: str
) -> tuple[MetadataKey, str]:
    """Parse and validate a single hub metadata entry.

    Args:
        item: Metadata entry in 'key=value' format.
        is_regular_hub: Whether the hub is a regular hub rather
            than a start or end hub.
        hub_name: Name of the hub the metadata belongs to.

    Returns:
        A tuple containing the metadata key and its value.

    Raises:
        MapParsingError: If the metadata entry has an invalid format,
            contains an unknown key, or uses a restricted key for a
            start or end hub.
    """

    if "=" not in item:
        raise MapParsingError(
            f"Invalid metadata entry '{item}' for hub {hub_name}. "
            "Expected 'key=value'."
        )

    key, value = item.split('=', 1)
    if not key or not value:
        raise MapParsingError(
            f"Invalid metadata entry '{item}' for hub {hub_name}."
            "Expected 'key=value'."
        )
    try:
        key = MetadataKey(key)
    except ValueError:
        raise MapParsingError(f"Unknown hub metadata: {key}.")
    if key is MetadataKey.ZONE and not is_regular_hub:
        raise MapParsingError(
            "Metadata 'zone' is not allowed "
            f"for start or end hub '{hub_name}'."
        )
    return key, value


def _parse_hub_metadata(
        metadata: str | None,
        is_regular_hub: bool,
        hub_name: str
) -> dict[MetadataKey, str]:
    """Parse and validate all metadata entries for a hub.

    Args:
        metadata: Raw metadata string containing space-separated
            key=value entries.
        is_regular_hub: Whether the hub is a regular hub rather
            than a start or end hub.
        hub_name: Name of the hub the metadata belongs to.

    Returns:
        A dictionary mapping metadata keys to their values.

    Raises:
        MapParsingError: If a metadata entry is invalid, duplicated,
            or contains a key that is not allowed for hubs.
    """

    parsed_metadata: dict[MetadataKey, str] = {}

    if metadata is None:
        return parsed_metadata

    for item in metadata.split():
        key, value = _parse_metadata_item(item, is_regular_hub, hub_name)
        if key is MetadataKey.MAX_LINK_CAPACITY:
            raise MapParsingError(
                "Metadata 'max_link_capacity' "
                f"shouldn't appear for hub: {hub_name}."
            )
        if key in parsed_metadata:
            raise MapParsingError(
                f"Metadata {key} appeared twice for hub: {hub_name}."
            )
        parsed_metadata[key] = value

    return parsed_metadata


def _parse_hub(hub: str, is_regular_hub: bool = True) -> Hub:
    """Parse a hub declaration and create a Hub instance.

    Args:
        hub: Raw hub declaration containing its name, coordinates
            and optional metadata.
        is_regular_hub: Whether the hub is a regular hub rather
            than a start or end hub.

    Returns:
        A validated Hub instance.

    Raises:
        MapParsingError: If the hub declaration has an invalid format
            or contains invalid metadata.
        ValidationError: If the resulting Hub instance fails
        Pydantic validation.
    """

    match = re.fullmatch(
        "([a-zA-Z0-9_]+)\\s+(-?\\d+)\\s+(-?\\d+)\\s*(?:\\[(.*?)\\])?\\s*",
        hub
    )
    if not match:
        raise MapParsingError("Incorrect format for hub line. Expected "
                              "'<name> <integer> <integer> [metadata]'.")

    name, x, y, metadata = match.groups()

    hub_metadata = _parse_hub_metadata(metadata, is_regular_hub, name)

    return Hub(
        name=name,
        x=int(x),
        y=int(y),
        zone=ZoneEnum(hub_metadata.get(MetadataKey.ZONE, ZoneEnum.NORMAL)),
        color=hub_metadata.get(MetadataKey.COLOR, Color.RESET.name),
        max_drones=int(hub_metadata.get(MetadataKey.MAX_DRONES, 1))
    )


def _parse_connection(connection: str) -> Connection:
    """Parse a connection declaration and create a Connection instance.

    Args:
        connection: Raw connection declaration containing two hub names
            and optional metadata.

    Returns:
        A validated Connection instance.

    Raises:
        MapParsingError: If the connection declaration has an invalid
            format or contains unsupported metadata.
        ValidationError: If the resulting Connection instance fails
            Pydantic validation.
    """

    connection = connection.strip()

    match = re.fullmatch(
        "([a-zA-Z0-9_]+)-([a-zA-Z0-9_]+)\\s*(?:\\[(.*?)\\])?",
        connection
    )

    if not match:
        raise MapParsingError(
            "Incorrect format for connection line. Should be 'connection: "
            "<name>-<name> [metadata]'."
            )
    name1, name2, metadata = match.groups()
    max_link_capacity = 1

    if metadata is not None:
        items = metadata.split()
        if len(items) != 1:
            raise MapParsingError(
                "Invalid metadata for connection "
                f"'{name1}-{name2}'. Expected 'key=value'."
            )
        item = items[0]
        if "=" not in item:
            raise MapParsingError(
                f"Invalid metadata format: '{item}'. Expected 'key=value'."
            )
        key, value = item.split('=', 1)
        if key != MetadataKey.MAX_LINK_CAPACITY:
            raise MapParsingError(
                f"Unknown connection metadata: {key}."
            )
        max_link_capacity = int(value)
    return Connection(
        name1=name1,
        name2=name2,
        max_link_capacity=max_link_capacity
    )


def _register_hub(
        name: str,
        hub_names: set[str],
        coordinates: set[tuple[int, int]],
        coordinate: tuple[int, int]
) -> None:
    """Check hub name and coordinates for duplicates.

    Args:
        name: Name of the hub to check.
        hub_names: Set of previously registered hub names.
        coordinates: Set of previously registered hub coordinates.
        coordinate: Coordinates of the hub to check.

    Raises:
        MapParsingError: If the hub name or coordinates already exist.
    """

    if name in hub_names:
        raise MapParsingError(
            f"Duplicate hub name: {name}."
        )
    if coordinate in coordinates:
        raise MapParsingError(
            f"Duplicate zone coordinates: {coordinate}."
        )
    hub_names.add(name)
    coordinates.add(coordinate)


def read_map_file(file_name: str) -> Network:
    """Read a map file, parse its contents and create a Network instance.

    Args:
        file_name: Path to the map file.

    Returns:
        A validated Network instance containing the drones,
        hubs and connections.

    Raises:
        MapParsingError: If the file contains invalid declarations,
            duplicate entries, or an invalid configuration.
    """

    nb_drones = 0
    start_hub: Hub | None = None
    end_hub: Hub | None = None
    hubs: dict[str, Hub] = {}
    connections: list[Connection] = []

    hub_names: set[str] = set()
    coordinates: set[tuple[int, int]] = set()

    line_number = 0

    try:
        with open(file_name) as map_file:
            for line in map_file:
                line_number += 1
                line = line.split('#', 1)[0].strip()

                if not line:
                    continue
                if ':' not in line:
                    raise MapParsingError("Invalid line format.")

                key, _, value = line.partition(":")
                key = key.strip()
                value = value.strip()

                if nb_drones is None:
                    if key != MapKey.NB_DRONES:
                        raise MapParsingError(
                            "The first line should define the number of "
                            f"drones using {MapKey.NB_DRONES}: <number>."
                        )

                if key == MapKey.NB_DRONES:
                    if nb_drones is not None:
                        raise MapParsingError(
                            f"Duplicate configuration key: {MapKey.NB_DRONES}."
                        )
                    nb_drones = _parse_nb_drones(line)

                elif key in (MapKey.START_HUB, MapKey.END_HUB, MapKey.HUB):
                    if connections:
                        raise MapParsingError(
                            "Hubs should be before connection."
                        )
                    hub = _parse_hub(value, key == MapKey.HUB)
                    _register_hub(
                        hub.name,
                        hub_names,
                        coordinates,
                        (hub.x, hub.y)
                    )

                    if key == MapKey.START_HUB:
                        if start_hub is not None:
                            raise MapParsingError(
                                "Duplicate configuration "
                                f"key: {MapKey.START_HUB}."
                            )
                        start_hub = hub
                    elif key == MapKey.END_HUB:
                        if end_hub is not None:
                            raise MapParsingError(
                                "Duplicate configuration "
                                f"key: {MapKey.END_HUB}."
                            )
                        end_hub = hub
                    else:
                        hubs[hub.name] = hub
                elif key == MapKey.CONNECTION:
                    if start_hub is None and end_hub is None and not hubs:
                        raise MapParsingError(
                            "Connections should be after hubs."
                        )
                    connections.append(_parse_connection(value))
                else:
                    raise MapParsingError(f"Unknown configuration key: {key}.")
            if start_hub is None or end_hub is None:
                raise MapParsingError("Missed start_hub or end_hub.")
            return Network(
                nb_drones=int(nb_drones),
                start_hub=start_hub,
                end_hub=end_hub,
                hubs=hubs,
                connections=connections
            )
    except MapParsingError as e:
        raise MapParsingError(f"Error in line {line_number}: {e}")
    except ValidationError as e:
        raise MapParsingError(f"Error in line {line_number}: "
                              f"{format_validation_error(e)}") from e
    except ValueError as e:
        raise MapParsingError(f"Error in line {line_number}: {e}")
    except (FileNotFoundError, PermissionError, IsADirectoryError) as e:
        raise MapParsingError(str(e))
