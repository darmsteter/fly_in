from config.parser import read_config_file
from errors import ConfigurationException
from config.models import Conection
from graph_builder import build_graph
from find_path import find_path
from simulation import Simulation
import sys

def print_graph(graph: dict[str, list[Conection]]) -> None:
    print("Graph:")

    for hub_name, connections in graph.items():
        print(f"\n{hub_name}")

        for i, connection in enumerate(connections):
            if i == len(connections) - 1:
                print(f"└──→ {connection.name2}")
            else:
                print(f"├──→ {connection.name2}")

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
		path = find_path(network, graph)
		simulation = Simulation(network, graph)
		for _ in range(20):
			simulation.run_turn()
	except ConfigurationException as e:
		print(e)