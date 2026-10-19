from config.models import Network, Conection
from math import inf
import heapq
from errors import ConfigurationException

def find_path(network: Network, graph: dict[str, list[Conection]]) -> list[list[str]]:
	start = network.start_hub

	distances = {hub_name: inf for hub_name in graph}
	distances[start.name] = 0
	distances[network.end_hub.name] = inf

	previous: dict[str, str] = {}

	queue: list[tuple[float, str]] = []
	heapq.heappush(queue, (0, start.name))

	while queue:
		distance, hub_name = heapq.heappop(queue)
		if distance > distances[hub_name]:
			continue
		if hub_name == network.end_hub.name:
			break
		conections = graph[hub_name]
		for conection in conections:
			neighbor = conection.name2
			if neighbor == network.end_hub.name: 
				new_distance = distance + network.end_hub.zone.get_distance()
			else:
				new_distance = distance + network.hubs[neighbor].zone.get_distance()
			if new_distance == inf:
				continue
			if distances[neighbor] > new_distance:
				heapq.heappush(queue, (new_distance, neighbor))
				distances[neighbor] = new_distance
				previous[neighbor] = hub_name
	if distances[network.end_hub.name] != inf:
		path = []
		current = network.end_hub.name
		while current != start.name:
			path.append(current)
			current = previous[current]
		path.append(start.name)
		path.reverse()
		return path
	else:
		raise ConfigurationException(
			"It is impossible to reach the exit."
		)
