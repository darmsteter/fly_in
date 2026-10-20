from .models import Drone
from config.models import Network, Conection, Hub, ZoneEnum
from find_path import find_path
import copy

class Simulation:
	def __init__(self, network: Network, graph: dict[str, list[Conection]]) -> None:
		self.network = network
		self.graph = graph
		self.drones: list[Drone] = self._init_drones()
		self.turn = 0
		self.turns_history: dict[int, dict[int, str]] = {}

	def _init_drones(self) -> list[Drone]:
		drones: list[Drone] = []
		paths = find_path(self.network, self.graph)
		for number in range(1, self.network.nb_drones + 1):
			drones.append(Drone(id=number, path=paths[number % len(paths)], path_index=0))
		return drones

	def _inii_positions(self) -> dict[int, str]:
		positions: dict[int, str] = {}
		start = self.network.start_hub.name
		end = self.network.end_hub.name
		for drone in self.drones:
			if drone.finished:
				positions[drone.id] = end
			else:
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

	def _get_positions(self, next_hub: Hub) -> dict[int, str]:
		if next_hub.zone is ZoneEnum.RESTRICTED:
			return self.turns_history[self.turn + 1]
		return self.turns_history[self.turn]

	def _can_move(self, drone: Drone, next_hub: Hub) -> bool:
		if self.turn > 0 and self.turns_history[self.turn - 1][drone.id] == "connection":
			conection = self._get_connection(drone.path[drone.path_index], drone.path[drone.path_index + 1])
			conection.passed_in_turn += 1
			return True
		max_hub_capacity = next_hub.max_drones
		drones_in_hub = list(self._get_positions(next_hub).values()).count(next_hub.name)
		if drones_in_hub >= max_hub_capacity and next_hub is not self.network.end_hub:
			return False
		current_hub_name = self._get_current_hub(drone).name
		conection = self._get_connection(current_hub_name, next_hub.name)
		if conection is None:
			return False
		if conection.passed_in_turn >= conection.max_link_capacity:
			return False
		conection.passed_in_turn += 1
		self._get_positions(next_hub)[drone.id] = next_hub.name
		if next_hub.zone is ZoneEnum.RESTRICTED:
			self.turns_history[self.turn][drone.id] = "connection"
			return False
		return True
	
	def _apply_moves(self, planned_moves: list[tuple[Drone, Hub]]):
		for drone, next_hub in planned_moves:
			print(f"D{drone.id}-{next_hub}", end=' ')
			drone.path_index += 1
			if drone.path_index == len(drone.path) - 1:
				drone.finished = True

	def _end_simulation(self, drones: list[Drone]) -> bool:
		for drone in drones:
			if not drone.finished:
				return False
		return True

	def run_turn(self):
		planned_moves: list[tuple[Drone, Hub]] = []
		waiting_drones: list[Drone] = []
		if self.turn not in self.turns_history:
			self.turns_history[self.turn] = self._inii_positions()
		if self.turn + 1 not in self.turns_history:
			self.turns_history[self.turn + 1] = self._inii_positions()
		for conection in self.network.conections:
			conection.passed_in_turn = 0
		for drone in self.drones:
			if drone.finished:
				continue
			next_hub = self._get_next_hub(drone)
			if next_hub is None:
				continue
			if self._can_move(drone, next_hub):
				planned_moves.append((drone, next_hub))
				continue
			if not self.turns_history[self.turn][drone.id] == "connection":
				waiting_drones.append(drone)
		for drone in waiting_drones:
			next_hub = self._get_next_hub(drone)
			if next_hub is None:
				continue
			if self._can_move(drone, next_hub):
				planned_moves.append((drone, next_hub))
		self._apply_moves(planned_moves)
		print()
		# self.turns_history[self.turn] = copy.deepcopy(self.positions)
		self.turn += 1
		return self._end_simulation(self.drones)