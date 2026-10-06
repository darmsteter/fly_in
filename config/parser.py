from errors import ConfigurationException
from .models import ConfigKey, Hub, ZoneEnum
from pydantic import ValidationError

from typing import Any
import re

def store_config_value(values: dict[str, str], key: str, value: str) -> None:
	if not value:
		raise ConfigurationException(
			f"Expected a value after '{key}:'."
		)
	config_key = ConfigKey(key)
	if config_key in values:
		raise ConfigurationException(
			f"Duplivate configuration key: {key}. "
		)
	values[config_key] = value

def parse_config_lines(line: str, values: dict[str, Any]) -> None:
	if not values and not line.startswith(ConfigKey.NB_DRONES):
		raise ConfigurationException(
			"The first line must define the number of drones "
			"using nb_drones: <positive_integer>."
		)
	if re.findall(f"^{ConfigKey.NB_DRONES}:\\s+\\d+$", line):
		key, value = line.split(":", 1)
		value = value.strip()
		store_config_value(values, key, value)
	elif re.findall(f"^{ConfigKey.START_HUB}:\\s+[a-z]+\\s+\\d+\\s+\\d+\\s+\\[color=[a-z]+]$", line):
		key, value = line.split(":", 1)
		hub = parse_hub(line.replace(f"{ConfigKey.START_HUB}: ", ""))
		store_config_value(values, key, hub)
	elif re.findall(f"^{ConfigKey.END_HUB}:\\s+[a-z]+\\s+\\d+\\s+\\d+\\s+\\[color=[a-z]+]$", line):
		key, value = line.split(":", 1)
		hub = parse_hub(line.replace(f"{ConfigKey.END_HUB}: ", ""))
		store_config_value(values, key, hub)

def parse_hub(hub: str) -> Hub:
	color = None
	zone = ZoneEnum.NORMAL
	max_drones = 1

	hub = hub.replace("]", '')
	data = hub.split("[")
	name_and_coordinates = data[0].split(" ")
	splited_metadata = data[1].split(" ")
	for metadata in splited_metadata:
		key, value = metadata.split("=")
		if key == "color":
			color = value
		elif key == "zone":
			zone = value
		elif key == "max_drones":
			max_drones = value
		else:
			raise ConfigurationException(
				f"Wrong metadata: {hub}."
				)
		parsed_hub = Hub(name=name_and_coordinates[0],
			x=name_and_coordinates[1],
			y=name_and_coordinates[2],
			zone=zone,
			color=color,
			max_drones=max_drones)
		return parsed_hub

def parse_hubs(hubs: list[str]) -> list[Hub]:
	parsed_hubs: list[Hub] = []
	for hub in hubs:
		try:
			parsed_hubs.append(parse_hub(hub))
		except ValidationError as e:
			raise ConfigurationException(str(e))
		except ValueError:
			raise ConfigurationException(
				"Hub should be 'hub: <name> <x> <y> [metadata]'."
			)
	return parsed_hubs

def parse_connections(conections: list[str]):
	parsed_connections: list[tuple[str, str, int]] = []
	for conection in conections:
		max_link_capacity = 1
		if '[' in conection:
			conection, metadata = conection.split('[')
			if metadata.split("=")[0] == "max_link_capacity":
				max_link_capacity = metadata.split("=")[1]
			else:
				raise ConfigurationException("wrong metadata key.")
		start, goal = conection.split("-")
		parsed_connections.append((start, goal, max_link_capacity))
	print(parsed_connections)



def read_config_file(file_name: str) -> None:
	values: dict[str, Any] = {}
	hubs: list[str] = []
	conections: list[str] = []
	try:
		with open(file_name) as config_file:
			for line in config_file:
				line = line.strip()
				if line.startswith('#'):
					continue
				elif line.startswith(f"{ConfigKey.HUB}:"):
					hubs.append(line.replace(f"{ConfigKey.HUB}: ", ""))
				elif line.startswith("connection:"):
					conections.append(line.replace(f"{ConfigKey.CONNTCTION}: ", ""))
				else:
					parse_config_lines(line, values)
		parsed_hubs = parse_hubs(hubs)
		parse_connections(conections)
		print(parsed_hubs)
	except (FileNotFoundError, PermissionError, IsADirectoryError) as e:
		raise ConfigurationException(str(e))
	print(values)