from .models import Drone
from config.models import Network, Conection, Hub, ZoneEnum
from find_path import find_path
from errors import ConfigurationException
import copy

class Simulation:
	def __init__(self, network: Network, graph: dict[str, list[Conection]]) -> None:
		self.network = network
		self.graph = graph
		self.drones: dict[str, Drone] = self._init_drones()
		self.turn = 0
		self.positions: dict[int, str] = self._inii_positions()

	def _init_drones(self) -> dict[str, Drone]:
		drones: dict[str, Drone] = {}
		path = find_path(self.network, self.graph)
		for number in range(1, self.network.nb_drones + 1):
			drones[str(number)] = Drone(id=number, path=path, path_index=0)
		return drones

	def _inii_positions(self) -> dict[int, str]:
		positions: dict[int, str] = {}
		start = self.network.start_hub.name
		for _, drone in self.drones.items():
			positions[drone.id] = start
		return positions

	def _get_current_hub(self, drone: Drone) -> Hub:
		location = drone.path[drone.path_index]
		if location == self.network.start_hub.name:
			return self.network.start_hub
		elif location == self.network.end_hub.name:
			return self.network.end_hub
		else:
			return self.network.hubs[location]

	def _get_next_hub(self, drone: Drone) -> Hub | None:
		if not drone.finished:
			next_hub = drone.path[drone.path_index + 1]
			if next_hub == self.network.end_hub.name:
				return self.network.end_hub
			return self.network.hubs[next_hub]
		return None

	def _get_connection(self, current_hub_name: str, next_hub_name: str) -> Conection | None:
		for conection in self.network.conections:
			if conection.name1 == current_hub_name and conection.name2 == next_hub_name:
				return conection
		return None

	def _find_alternative_path(self, next_hub: Hub):
		new_network = copy.deepcopy(self.network)
		new_network.hubs[next_hub.name].zone = ZoneEnum.BLOCKED
		try:
			alternative_path = find_path(new_network, self.graph)
		except ConfigurationException:
			return None
		return alternative_path

	def _can_move(self, drone: Drone, next_hub: Hub) -> bool:
		max_hub_capacity = next_hub.max_drones
		drones_in_hub = list(self.positions.values()).count(next_hub.name)
		if drones_in_hub >= max_hub_capacity and next_hub is not self.network.end_hub:
			return False
		current_hub_name = self._get_current_hub(drone).name
		conection = self._get_connection(current_hub_name, next_hub.name)
		if conection is None:
			return False
		if conection.passed_in_turn >= conection.max_link_capacity:
			return False
		conection.passed_in_turn += 1
		return True
	
	def _apply_moves(self, planned_moves: list[tuple[Drone, Hub]]):
		for drone, next_hub in planned_moves:
			self.positions[drone.id] = next_hub.name
			print(f"D{drone.id}-{next_hub}", end=' ')
			drone.path_index += 1
			if drone.path_index == len(drone.path) - 1:
				drone.finished = True

	def run_turn(self):
		planned_moves: list[tuple[Drone, Hub]] = []
		for conection in self.network.conections:
			conection.passed_in_turn = 0
		for _, drone in self.drones.items():
			if drone.finished:
				continue
			next_hub = self._get_next_hub(drone)
			if next_hub is None:
				continue
			if self._can_move(drone, next_hub):
				planned_moves.append((drone, next_hub))
			else:
				alternative_path = self._find_alternative_path(next_hub)
				if alternative_path is None:
					continue
				drone.path = alternative_path
				if self._can_move(drone, next_hub):
					planned_moves.append((drone, next_hub))
		self._apply_moves(planned_moves)
		print()
		self.turn += 1
		