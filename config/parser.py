from errors import ConfigurationException
from .models import ConfigKey, Hub, ZoneEnum, Conection, Network, MetadataKey
from pydantic import ValidationError

from typing import Any
import re

def parse_nb_drones(line: str) -> str:
	if re.fullmatch(f"{ConfigKey.NB_DRONES}:\\s+\\d+$", line):
		_, value = line.split(":", 1)
		return value.strip()
	else:
		raise ConfigurationException(
			"Invalid nb_drones declaration: expected 'nb_drones: <positive_integer>'."
		)

def parse_hub(hub: str, is_regular: bool = True):
	if not re.findall(f"^\\s*[a-zA-Z0-9_]+\\s+-?\\d+\\s+-?\\d+\\s*\\[?.*\\]?$", hub):
		raise ConfigurationException(
			"Incorrect format for hub line. Should be 'hub_type: "
			"<name> <integer> <integer> [metadata]'."
			)
	try:
		seen_metadata = set()
		color = None
		zone = ZoneEnum.NORMAL
		max_drones = 1

		parts = hub.split("[", 1)
		name_and_coordinates = parts[0].split()
		if len(name_and_coordinates) > 3:
			raise ConfigurationException(
				f"Incorrect entry for hub: '{hub}', should be '<name> <x> <y> [metadata]'."
			)
		if len(parts) > 1:
			metadata = parts[1]
			if not metadata.endswith(']'):
				raise ConfigurationException(
					f"Invalid metadata format: 'hub: {hub}'."
				)
			metadata = metadata[:-1]
			for item in metadata.split():
				key, value = item.split('=')
				if key in seen_metadata:
						raise ConfigurationException(
							f"Metadata {key} appeared twice for hub {name_and_coordinates[0]}."
						)
				if key == MetadataKey.COLOR: 
					seen_metadata.add(MetadataKey.COLOR)
					color = value
				elif key == MetadataKey.ZONE:
					if not is_regular:
						raise ConfigurationException(
							f"Metadata 'zone' can't showed up for start or end hub, hub: '{hub}'."
						)
					seen_metadata.add(MetadataKey.ZONE)
					zone = value
				elif key == MetadataKey.MAX_DRONES:
					seen_metadata.add(MetadataKey.MAX_DRONES)
					max_drones = value
				else:
					raise ConfigurationException(
						f"Unknown hub metadata: {key}."
					)
		return Hub(name=name_and_coordinates[0].strip(),
			x=name_and_coordinates[1],
			y=name_and_coordinates[2],
			zone=zone,
			color=color,
			max_drones=max_drones)
	except IndexError:
		raise ConfigurationException(
			f"Incorrect entry for hub: '{hub}', should be '<name> <x> <y> [metadata]'."
		)

def parse_connection(conection: str):
	if not re.findall(f"^[a-zA-Z0-9_]+-[a-zA-Z0-9_]+\\s?\\[?[a-zA-Z_]*=?[0-9]*\\]?$", conection):
		raise ConfigurationException(
			"Incorrect format for hub line. Should be 'hub_type: "
			"<name> <integer> <integer> [metadata]'."
			)
	parts = conection.split('[', 1)
	names = parts[0].split('-', 1)
	max_link_capacity = '1'
	if len(parts) > 1:
		metadata = parts[1]
		if not metadata.endswith(']'):
			raise ConfigurationException(
				f"Invalid metadata format: 'conection: {conection}'"
			)
		metadata = metadata[:-1]
		for item in metadata.split():
			key, value = item.split('=')
			if key == MetadataKey.MAX_LINK_CAPACITY:
				max_link_capacity = value
			else:
				raise ConfigurationException(
					f"Unknown conection metadata: {key}."
				)
	return Conection(
		name1=names[0].strip(),
		name2=names[1].strip(),
		max_link_capacity=max_link_capacity
	)

def check_duplicate(name: str, hub_names: list[str], coordinates: list[tuple[int, int]], coordinate: tuple[int, int]) -> None:
	if name in hub_names:
		raise ConfigurationException(
			f"Duplicate hub name: {name}."
		)
	if coordinate in coordinates:
		raise ConfigurationException(
			f"Duplicate zone coordinates: {coordinate}."
		)
	hub_names.append(name)
	coordinates.append(coordinate)

def read_config_file(file_name: str) -> None:
	is_first_line = True
	nb_drones = None
	start_hub: Hub | None = None
	end_hub: Hub | None = None 
	hubs: dict[str, Hub] = {}
	connections: list[Conection] = []
	line_number = 0
	hub_names: list[str] = []
	coordinates: list[tuple[int, int]] = []
	is_hub = False
	is_conection = False
	try:
		with open(file_name) as config_file:
			for line in config_file:
				line_number += 1
				line = line.strip()
				if line.startswith('#') or line == "":
					continue
				elif line.startswith(f"{ConfigKey.NB_DRONES}:"):
					if nb_drones is not None:
						raise ConfigurationException(
							f"Duplicate configuration key: {ConfigKey.NB_DRONES}."
						)
					nb_drones = parse_nb_drones(line)
				else:
					if is_first_line:
						raise ConfigurationException(
							f"The first line should define the number of drones using {ConfigKey.NB_DRONES}: <number>."
						)
					if line.startswith(f"{ConfigKey.START_HUB}:"):
						is_hub = True
						if is_conection:
							raise ConfigurationException(
								"Hubs should be before conection."
							)
						if start_hub is not None:
							raise ConfigurationException(
								f"Duplicate configuration key: {ConfigKey.START_HUB}."
							)
						start_hub = parse_hub(line.split(": ", 1)[1].strip(), False)
						check_duplicate(start_hub.name, hub_names, coordinates, (start_hub.x, start_hub.y))
					elif line.startswith(f"{ConfigKey.END_HUB}:"):
						is_hub = True
						if is_conection:
							raise ConfigurationException(
								"Hubs should be before conection."
							)
						if end_hub is not None:
							raise ConfigurationException(
								f"Duplicate configuration key: {ConfigKey.END_HUB}"
							)
						end_hub = parse_hub(line.split(": ", 1)[1].strip(), False)
						check_duplicate(end_hub.name, hub_names, coordinates, (end_hub.x, end_hub.y))
					elif line.startswith(f"{ConfigKey.HUB}:"):
						is_hub = True
						if is_conection:
							raise ConfigurationException(
								"Hubs should be before conection."
							)
						hub = parse_hub(line.split(": ", 1)[1].strip())
						if hub.name in hubs:
							raise ConfigurationException(
								"Duplicate hub name."
							)
						hubs[hub.name] = hub
						check_duplicate(hub.name, hub_names, coordinates, (hub.x, hub.y))
					elif line.startswith(f"{ConfigKey.CONNTCTION}: "):
						is_conection = True
						if not is_hub:
							raise ConfigurationException(
								"Conections should be after hubs."
							)
						connections.append(parse_connection(line.split(": ", 1)[1].strip()))
				is_first_line = False
			return Network(
				nb_drones=nb_drones, 
				start_hub=start_hub,
				end_hub=end_hub,
				hubs=hubs,
				conections=connections
			)
	except ConfigurationException as e:
		raise ConfigurationException(str(e))
	except ValueError as e:
		raise ConfigurationException(str(e))
	except (ValidationError) as e:
		error_dict = e.errors()
		error_msg = "\n".join(
			f"Invalid hub field '{error['loc'][0]}': {error['msg']}."
			for error in error_dict
		)
		raise ConfigurationException(error_msg)
	except (FileNotFoundError, PermissionError, IsADirectoryError) as e:
		raise ConfigurationException(str(e))
	