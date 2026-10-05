from errors import ConfigurationException
from .models import ConfigKey
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
	print(value)
	values[config_key] = value

def parse_config_lines(line: str, values: dict[str, str]) -> None:
	if not values and not line.startswith(ConfigKey.NB_DRONES):
		raise ConfigurationException(
			"The first line must define the number of drones "
			"using nb_drones: <positive_integer>."
		)
	if re.findall(f"^{ConfigKey.NB_DRONES}:\\s+\\d+$", line):
		key, value = line.split(":", 1)
		value = value.strip()
		store_config_value(values, key, value)
	elif re.findall(f"^{ConfigKey.START_HUB}:\s+[a-z]+\s+\d+\s+\d+\s+\[color=[a-z]+]$", line):
		key, value = line.split(":", 1)
		value = value.strip()
		store_config_value(values, key, value)
	elif re.findall(f"^{ConfigKey.END_HUB}:\s+[a-z]+\s+\d+\s+\d+\s+\[color=[a-z]+]$", line):
		key, value = line.split(":", 1)
		value = value.strip()
		store_config_value(values, key, value)

def read_config_file(file_name: str):
	values: dict[str, str] = {}
	try:
		with open(file_name) as config_file:
			for line in config_file:
				line = line.strip()
				if line.startswith('#'):
					continue
				parse_config_lines(line, values)
	except (FileNotFoundError, PermissionError, IsADirectoryError) as e:
		raise ConfigurationException(str(e))
	print(values)