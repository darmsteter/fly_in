from config.parser import read_config_file
from errors import ConfigurationException
import sys


if __name__ == "__main__":
	if len(sys.argv) != 2:
		print(
			"Your program must be run with the following command: "
			"python3 fly_in.py config.txt"
		)
		exit()
	try:
		read_config_file(sys.argv[1])
	except ConfigurationException as e:
		print(e)