from map_parser.models import Network, Connection
from errors import ConfigurationException


def build_graph(network: Network):
	graph: dict[str, list[Connection]] = {}
	graph[network.start_hub.name] = []

	for hub_name in network.hubs:
		if hub_name != network.start_hub.name:
			graph[hub_name] = []

	
	for connection in network.connections:
		if connection.name1 not in graph and connection.name1 != network.end_hub.name:
			raise ConfigurationException(
				f"Unknown hub name '{connection.name1}' in conection: {connection}."
			)
		if connection.name2 not in graph and connection.name2 != network.end_hub.name:
			raise ConfigurationException(
				f"Unknown hub name '{connection.name2}' in conection: {connection}."
			)
		for connections in graph.values():
			if any(connection.conflicts_with(existing) for existing in connections):
				raise ConfigurationException(
					f"Duplicate link between two hubs: "
					f"{connection.name1} and {connection.name2}."
				)
		graph[connection.name1].append(connection)
	return graph