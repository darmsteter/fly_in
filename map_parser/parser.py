from errors import MapParsingError, format_validation_error
from .models import Hub, ZoneEnum, Connection, Network
from map_parser.enums import MapKey, MetadataKey
from pydantic import ValidationError
from .colors import Color
import re

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
	if not re.fullmatch(f"{MapKey.NB_DRONES}:\\s*\\d+$", line):
		raise MapParsingError(
			"Invalid nb_drones declaration: expected 'nb_drones: <positive_integer>'."
		)
	_, value = line.split(":", 1)
	return value.strip()

def _parse_metadata_item(item: str, is_regular: bool, hub_name: str) -> tuple[MetadataKey, str]:
	if "=" not in item:
		raise MapParsingError(
			f"Invalid metadata entry '{item}' for hub {hub_name}. "
			"Expected 'key=value'."
		)

	key, value = item.split('=', 1)
	if not key or not value:
		raise  MapParsingError(
			f"Invalid metadata entry '{item}' for hub {hub_name}."
			"Expected 'key=value'."
		)
	try:
		key = MetadataKey(key)
	except ValueError:
		raise MapParsingError(f"Unknown hub metadata: {key}.")

	if key is MetadataKey.ZONE and not is_regular:
		raise MapParsingError(
			f"Metadata 'zone' is not allowed for start or end hub '{hub_name}'."
		)
	return key, value

def _parse_hub_metadata(metadata: str | None, is_regular: bool, hub_name: str) -> dict[MetadataKey, str]:
	parsed_metadata: dict[MetadataKey, str] = {}

	if metadata is None:
		return parsed_metadata

	for item in metadata.split():
		key, value = _parse_metadata_item(item, is_regular, hub_name)
		if key is MetadataKey.MAX_LINK_CAPACITY:
			raise MapParsingError(
				f"Metadata 'max_link_capacity' for hub: {hub_name}."
			)
		if key in parsed_metadata:
			raise MapParsingError(
				f"Metadata {key} appeared twice for hub: {hub_name}."
			)
		parsed_metadata[key] = value

	return parsed_metadata

def _parse_hub(hub: str, is_regular: bool = True) -> Hub:

	match = re.fullmatch("\\s*([a-zA-Z0-9_]+)\\s+(-?\\d+)\\s+(-?\\d+)\\s*(?:\\[(.*?)\\])?\\s*", hub)
	if not match:
		raise MapParsingError("Incorrect format for hub line. Expected "
							  "'<name> <integer> <integer> [metadata]'.")

	name, x, y, metadata = match.groups()

	hub_metadata = _parse_hub_metadata(metadata, is_regular, name)

	return Hub(
		name=name,
		x=x,
		y=y,
		zone=hub_metadata.get(MetadataKey.ZONE, ZoneEnum.NORMAL),
		color=hub_metadata.get(MetadataKey.COLOR, Color.RESET.name),
		max_drones=hub_metadata.get(MetadataKey.MAX_DRONES, 1)
	)

def parse_connection(connection: str):
	match = re.fullmatch("([a-zA-Z0-9_]+)-([a-zA-Z0-9_]+)\\s*(?:\\[(.*?)\\])?\\s*", connection)

	if not match:
		raise MapParsingError(
			"Incorrect format for connection line. Should be 'hub_type: "
			"<name> <integer> <integer> [metadata]'."
			)
	name1, name2, metadata = match.groups()
	max_link_capacity = 1

	if metadata is not None:
		items = metadata.split()
		if len(items) > 1:
			raise MapParsingError(
				f"Metadata appeared twice for connection "
				f"'{name1}-{name2}'."
			)
		item = items[0]
		if "=" not in item:
			raise MapParsingError(
				f"Invalid metadata format: '{item}'. Expected 'key=value'."
			)
		key, value = item.split('=', 1)
		if key == MetadataKey.MAX_LINK_CAPACITY:
			max_link_capacity = value
		else:
			raise MapParsingError(
				f"Unknown connection metadata: {key}."
			)
	return Connection(
		name1=name1,
		name2=name2,
		max_link_capacity=max_link_capacity
	)

def check_duplicate(name: str, hub_names: list[str], coordinates: list[tuple[int, int]], coordinate: tuple[int, int]) -> None:
	if name in hub_names:
		raise MapParsingError(
			f"Duplicate hub name: {name}."
		)
	if coordinate in coordinates:
		raise MapParsingError(
			f"Duplicate zone coordinates: {coordinate}."
		)
	hub_names.append(name)
	coordinates.append(coordinate)

def read_config_file(file_name: str) -> Network:
	is_first_map_line = True
	nb_drones = None
	start_hub: Hub | None = None
	end_hub: Hub | None = None 
	hubs: dict[str, Hub] = {}
	connections: list[Connection] = []
	line_number = 0
	hub_names: list[str] = []
	coordinates: list[tuple[int, int]] = []
	is_hub = False
	is_conection = False
	try:
		with open(file_name) as config_file:
			for line in config_file:
				line_number += 1
				line = line.split('#', 1)[0].strip()
				if not line:
					continue
				elif line.startswith(f"{MapKey.NB_DRONES}:"):
					if nb_drones is not None:
						raise MapParsingError(
							f"Duplicate configuration key: {MapKey.NB_DRONES}."
						)
					nb_drones = _parse_nb_drones(line)
				else:
					if is_first_map_line:
						raise MapParsingError(
							f"The first line should define the number of drones using {MapKey.NB_DRONES}: <number>."
						)
					if line.startswith(f"{MapKey.START_HUB}:"):
						is_hub = True
						if is_conection:
							raise MapParsingError(
								"Hubs should be before conection."
							)
						if start_hub is not None:
							raise MapParsingError(
								f"Duplicate configuration key: {MapKey.START_HUB}."
							)
						start_hub = _parse_hub(line.split(": ", 1)[1].strip(), False)
						check_duplicate(start_hub.name, hub_names, coordinates, (start_hub.x, start_hub.y))
					elif line.startswith(f"{MapKey.END_HUB}:"):
						is_hub = True
						if is_conection:
							raise MapParsingError(
								"Hubs should be before conection."
							)
						if end_hub is not None:
							raise MapParsingError(
								f"Duplicate configuration key: {MapKey.END_HUB}"
							)
						end_hub = _parse_hub(line.split(": ", 1)[1].strip(), False)
						check_duplicate(end_hub.name, hub_names, coordinates, (end_hub.x, end_hub.y))
					elif line.startswith(f"{MapKey.HUB}:"):
						is_hub = True
						if is_conection:
							raise MapParsingError(
								"Hubs should be before conection."
							)
						hub = _parse_hub(line.split(": ", 1)[1].strip())
						hubs[hub.name] = hub
						check_duplicate(hub.name, hub_names, coordinates, (hub.x, hub.y))
					elif line.startswith(f"{MapKey.CONNECTION}: "):
						is_conection = True
						if not is_hub:
							raise MapParsingError(
								"Conections should be after hubs."
							)
						connections.append(parse_connection(line.split(": ", 1)[1].strip()))
				is_first_map_line = False
			return Network(
				nb_drones=nb_drones, 
				start_hub=start_hub,
				end_hub=end_hub,
				hubs=hubs,
				connections=connections
			)
	except MapParsingError as e:
		raise MapParsingError(f"Error in line {line_number}: {e}")
	except ValidationError as e:
		raise MapParsingError(f"Error in line {line_number}: {format_validation_error(e)}") from e
	except ValueError as e:
		raise MapParsingError(str(e))
	except (FileNotFoundError, PermissionError, IsADirectoryError) as e:
		raise MapParsingError(str(e))
