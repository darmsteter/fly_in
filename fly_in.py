from config.parser import read_config_file
from errors import ConfigurationException
from graph_builder import build_graph
from find_path import find_path
from simulation import Simulation
import sys

if __name__ == "__main__":
	# if len(sys.argv) != 2:
	# 	print(
	# 		"Your program must be run with the following command: "
	# 		"python3 fly_in.py config.txt"
	# 	)
	# 	exit()
	try:
		# network = read_config_file(sys.argv[1])
		network = read_config_file("config.txt")
		graph = build_graph(network)
		paths = find_path(network, graph)
		simulation = Simulation(network, graph)
		while True:
			if not simulation.run_turn():
				continue			
			break
		print(simulation.turn)
	except ConfigurationException as e:
		print(e)
	except Exception as e:
		print(f"Something went wrong: {e}")