from config.models import Network, Conection
from math import inf
import heapq
from errors import ConfigurationException

def _get_hub_cost(network: Network, hub_name: str) -> float:
	if network.start_hub.name == hub_name:
		return network.start_hub.zone.get_distance()
	elif network.end_hub.name == hub_name:
		return 0
	return network.hubs[hub_name].zone.get_distance()

def _dijkstra(
		network: Network, 
		graph: dict[str, list[Conection]],
		start: str,
		end: str,
		banned_hubs: list[str],
		banned_connections: set[tuple[str, str]]
		) -> list[str] | None:
	if start in banned_hubs or end in banned_hubs:
		return None
	
	distances = {hub_name: inf for hub_name in graph}
	distances[start] = 0
	distances[end] = inf
	previous: dict[str, str] = {}

	queue: list[tuple[float, str]] = []
	heapq.heappush(queue, (0, start))

	while queue:
		distance, hub_name = heapq.heappop(queue)
		if distance > distances[hub_name]:
			continue
		if hub_name == end:
			break
		conections = graph[hub_name]
		for conection in conections:
			if conection.max_link_capacity == 0:
				continue
			neighbor = conection.name2
			if neighbor in banned_hubs:
				continue
			if (hub_name, neighbor) in banned_connections:
				continue
			cost = _get_hub_cost(network, neighbor)
			if cost == inf:
				continue
			new_distance = distance + cost
			if distances[neighbor] > new_distance:
				heapq.heappush(queue, (new_distance, neighbor))
				distances[neighbor] = new_distance
				previous[neighbor] = hub_name
	if distances[end] != inf:
		path = []
		current = end
		while current != start:
			path.append(current)
			current = previous[current]
		path.append(start)
		path.reverse()
		return path
	return None

def _path_cost(network: Network, path: list[str]) -> float:
	return sum(
		_get_hub_cost(network, hub_name)
		for hub_name in path
	)

def find_path(network: Network, graph: dict[str, list[Conection]]) -> list[list[str]]:
	start = network.start_hub.name
	end = network.end_hub.name

	main_path = _dijkstra(network, graph, start, end, set(), set())
	if main_path is None:
		raise ConfigurationException(
			"It is impossible to reach the exit."
		)
	main_path_cost = _path_cost(network, main_path)
	max_cost = main_path_cost * 1.3
	paths: list[list[str]] = [main_path]
	candidates: list[tuple[float, tuple[str, ...]]] = []
	candidate_paths: set[tuple[str, ...]] = set()
	previous_path = paths[len(paths) - 1]

	for i in range(len(previous_path) - 1):
		root_path = []
		for j in range(i + 1):
			root_path.append(previous_path[j])
		spur_node = previous_path[i]
		b_connections: set[tuple[str, str]] = set()
		for path in paths:
			if len(path) > i + 1 and path[:i + 1] == root_path:
				b_connections.add((path[i], path[i + 1]))
		b_hubs = set()
		for hub in root_path:
			if hub != spur_node:
				b_hubs.add(hub)
		spur_path = _dijkstra(network, graph, spur_node, end, b_hubs, b_connections)
		if spur_path is None:
			continue
		total_path = []
		for j in range(len(root_path) - 1):
			total_path.append(root_path[j])
		for hub in spur_path:
			total_path.append(hub)
		total_cost = _path_cost(network, total_path)
		if total_cost > max_cost:
			continue
		path_key = tuple(total_path)
		if (path_key in candidate_paths or total_path in paths):
			continue
		heapq.heappush(candidates, (total_cost, path_key))
		candidate_paths.add(path_key)

	if candidates:
		_, next_path = heapq.heappop(candidates)
		candidate_paths.remove(next_path)
		paths.append(list(next_path))

	return paths	