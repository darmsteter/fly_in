from .map_parser.models import Connection, Network
from .errors import PathFindingError

from math import inf
import heapq

def _get_hub_cost(network: Network, hub_name: str) -> float:
	"""Get the traversal cost of a hub.

	The start hub uses its configured traversal cost.
	The end hub always has a traversal cost of zero.

	Args:
	    network: Network containing all hubs.
	    hub_name: Name of the hub.

	Returns:
	    Traversal cost of the specified hub.
	"""

	if network.start_hub.name == hub_name:
		return network.start_hub.zone.get_traversal_cost()
	elif network.end_hub.name == hub_name:
		return 0
	return network.hubs[hub_name].zone.get_traversal_cost()

def _dijkstra(
		network: Network, 
		graph: dict[str, list[Connection]],
		start: str,
		end: str,
		banned_hubs: set[str],
		banned_connections: set[tuple[str, str]]
		) -> list[str] | None:
	"""Find the shortest path using Dijkstra's algorithm.

	Args:
	    network: Network containing hub information.
	    graph: Directed graph represented as adjacency lists.
	    start: Starting hub name.
	    end: Destination hub name.
	    banned_hubs: Hubs that cannot be visited.
	    banned_connections: Directed connections that cannot be used.

	Returns:
	    A list of hub names representing the shortest path,
	    or None if no path exists.
	"""

	if start in banned_hubs or end in banned_hubs:
		return None
	
	distances = {hub_name: inf for hub_name in graph}
	distances[start] = 0
	distances[end] = inf

	previous: dict[str, str] = {}

	queue: list[tuple[float, str]] = [(0, start)]

	while queue:
		distance, hub_name = heapq.heappop(queue)

		if distance > distances[hub_name]:
			continue

		if hub_name == end:
			break

		for connection in graph[hub_name]:
			if connection.max_link_capacity == 0:
				continue

			neighbor = connection.name2

			if neighbor in banned_hubs:
				continue

			if (hub_name, neighbor) in banned_connections:
				continue

			cost = _get_hub_cost(network, neighbor)

			if cost == inf:
				continue

			new_distance = distance + cost

			if new_distance < distances[neighbor]:
				distances[neighbor] = new_distance
				previous[neighbor] = hub_name
				heapq.heappush(queue, (new_distance, neighbor))

	if distances[end] == inf:
		return None
	path = []
	current = end

	while current != start:
		path.append(current)
		current = previous[current]

	path.append(start)
	path.reverse()

	return path


def _path_cost(network: Network, path: list[str]) -> float:
	"""Calculate the total traversal cost of a path.

	Args:
	    network: Network containing hub information.
	    path: Ordered list of hub names.

	Returns:
	    Sum of traversal costs of all hubs in the path.
	"""

	return sum(
		_get_hub_cost(network, hub_name)
		for hub_name in path
	)

def find_path(network: Network, graph: dict[str, list[Connection]]) -> list[list[str]]:
	"""Find the shortest path and one alternative path.

	Uses Yen's algorithm to generate an alternative path
	whose cost does not exceed 130% of the shortest path cost.

	Args:
	    network: Network containing hub information.
	    graph: Directed graph represented as adjacency lists.

	Returns:
	    A list containing the shortest path and, if available,
	    one alternative path.

	Raises:
	    MapParsingError: If the exit cannot be reached.
	"""

	start = network.start_hub.name
	end = network.end_hub.name

	main_path = _dijkstra(network, graph, start, end, set(), set())

	if main_path is None:
		raise PathFindingError("It is impossible to reach the exit.")

	max_cost = _path_cost(network, main_path) * 1.3

	candidates: list[tuple[float, tuple[str, ...]]] = []

	for i in range(len(main_path) - 1):
		root_path = main_path[:i + 1]
		spur_node = main_path[i]

		banned_connections = {(main_path[i], main_path[i + 1])}

		banned_hubs = set()
		for hub in root_path:
			if hub != spur_node:
				banned_hubs.add(hub)

		spur_path = _dijkstra(network, graph, spur_node, end, banned_hubs, banned_connections)

		if spur_path is None:
			continue

		total_path = root_path[:-1] + spur_path
		total_cost = _path_cost(network, total_path)
		if total_cost > max_cost:
			continue

		heapq.heappush(candidates, (total_cost, tuple(total_path)))

	if not candidates:
		return [main_path]

	_, alternative_path = heapq.heappop(candidates)

	return [main_path, list(alternative_path)]