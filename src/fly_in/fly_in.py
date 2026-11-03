from .map_parser import read_map_file
from .errors import MapParsingError
from .graph_builder import build_graph
from .simulation import Simulation

import sys


def main() -> None:
    if len(sys.argv) != 2:
        print(
            "Your program must be run with the following command: "
            "python3 fly_in.py map.txt"
        )
        exit()
    try:
        network = read_map_file(sys.argv[1])
        graph = build_graph(network)
        simulation = Simulation(network, graph)
        while True:
            if not simulation.run_turn():
                continue
            break
    except MapParsingError as e:
        print(e)
    except Exception as e:
        print(f"Something went wrong: {e}")
