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

def parse_hub(hub: str):
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
					seen_metadata.add(MetadataKey.ZONE)
					zone = value
				elif key == MetadataKey.MAX_DRONES:
					seen_metadata.add(MetadataKey.MAX_DRONES)
					max_drones = value
				else:
					raise ConfigurationException(
						f"Unknown hub metadata: {key}."
					)
		return name_and_coordinates[0].strip(), Hub(name=name_and_coordinates[0].strip(),
			x=name_and_coordinates[1],
			y=name_and_coordinates[2],
			zone=zone,
			color=color,
			max_drones=max_drones)
	except IndexError:
		raise ConfigurationException(
			f"Incorrect entry for hub: '{hub}', should be '<name> <x> <y> [metadata]'."
		)

def parse_connection(conection: list[str]):
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

def read_config_file(file_name: str) -> None:
	is_first_line = True
	nb_drones = None
	start_hub: Hub | None = None
	end_hub: Hub | None = None 
	hubs: dict[str, Hub] = {}
	connections: list[Conection] = []
	line_number = 0
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
						if start_hub is not None:
							raise ConfigurationException(
								f"Duplicate configuration key: {ConfigKey.START_HUB}."
							)
						_, start_hub = parse_hub(line.split(": ", 1)[1].strip())
					elif line.startswith(f"{ConfigKey.END_HUB}:"):
						if end_hub is not None:
							raise ConfigurationException(
								f"Duplicate configuration key: {ConfigKey.END_HUB}"
							)
						_, end_hub = parse_hub(line.split(": ", 1)[1].strip())
					elif line.startswith(f"{ConfigKey.HUB}:"):
						name, hub = parse_hub(line.split(": ", 1)[1].strip())
						if name in hubs:
							raise ConfigurationException(
								"Duplicate hub name."
							)
						hubs[name] = hub
					elif line.startswith(f"{ConfigKey.CONNTCTION}: "):
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
		raise ConfigurationException(f"Error in line {line_number}: " + str(e))
	except ValueError as e:
		raise ConfigurationException(f"Error in line {line_number}: " + str(e))
	except (ValidationError) as e:
		error_dict = e.errors()
		error_msg = "\n".join(
			f"Invalid hub field '{error['loc'][0]}': {error['msg']}."
			for error in error_dict
		)
		raise ConfigurationException(f"Error in line {line_number}: " +  error_msg)
	except (FileNotFoundError, PermissionError, IsADirectoryError) as e:
		raise ConfigurationException(str(e))
	