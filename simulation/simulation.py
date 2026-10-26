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
		self.reserved: dict[str, set[int]] = {}

	def _init_drones(self) -> list[Drone]:
		drones: list[Drone] = []
		paths = find_path(self.network, self.graph)
		for number in range(1, self.network.nb_drones + 1):
			drones.append(Drone(id=number, path=paths[(number - 1) % len(paths)], path_index=0))
			print((number - 1) % len(paths))
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

	def _can_move(self, drone: Drone, next_hub: Hub) -> bool:
		current_positions = self.turns_history[self.turn]
		next_positions = self.turns_history[self.turn + 1]
		current_hub_name = drone.path[drone.path_index]
		next_hub_name = next_hub.name
		connection = self._get_connection(current_hub_name, next_hub_name)
		
		if connection is None:
			return False

		if next_hub_name in self.reserved and drone.id not in self.reserved[next_hub_name]:
			return False

		if current_positions[drone.id] == "connection":
			if drone.id in self.reserved.get(next_hub_name, set()):
				self.reserved[next_hub_name].remove(drone.id)
				if not self.reserved[next_hub_name]:
					self.reserved.pop(next_hub_name)
			next_positions[drone.id] = next_hub_name
			return True

		if connection.passed_in_turn >= connection.max_link_capacity:
			return False

		drones_in_hub = list(next_positions.values()).count(next_hub_name)
		reserved_drones = len(self.reserved.get(next_hub_name, set()))
		if drones_in_hub + reserved_drones >= next_hub.max_drones and next_hub is not self.network.end_hub:
			return False
		
		if next_hub.zone is ZoneEnum.RESTRICTED:
			self.reserved.setdefault(next_hub_name, set()).add(drone.id)
			connection.passed_in_turn += 1
			next_positions[drone.id] = "connection"
			return True

		connection.passed_in_turn += 1
		next_positions[drone.id] = next_hub_name
		return True
	
	def _apply_moves(self, planned_moves: list[tuple[Drone, Hub]]) -> None:
		for drone, next_hub in planned_moves:
			was_in_connection = self.turns_history[self.turn][drone.id] == "connection"
			if next_hub.zone is ZoneEnum.RESTRICTED and not was_in_connection:
				continue
			print(f"D{drone.id}-{next_hub}", end=" ")
			drone.path_index += 1
			if drone.path_index == len(drone.path) - 1:
				drone.finished = True

	def _end_simulation(self, drones: list[Drone]) -> bool:
		for drone in drones:
			if not drone.finished:
				return False
		return True

	def run_turn(self) -> bool:
		planned_moves: list[tuple[Drone, Hub]] = []
		waiting_drones: list[Drone] = []
		planned_ids: set[int] = set()
		if self.turn not in self.turns_history:
			self.turns_history[self.turn] = self._inii_positions()
		self.turns_history[self.turn + 1] = self.turns_history[self.turn].copy()
		for connection in self.network.conections:
			connection.passed_in_turn = 0
		for drone in self.drones:
			if drone.finished:
				continue
			next_hub = self._get_next_hub(drone)
			if next_hub is None:
				continue
			if self._can_move(drone, next_hub):
				planned_moves.append((drone, next_hub))
				planned_ids.add(drone.id)
			elif self.turns_history[self.turn][drone.id] != "connection":
				waiting_drones.append(drone)
		for drone in waiting_drones:
			if drone.id in planned_ids:
				continue
			next_hub = self._get_next_hub(drone)
			if next_hub is None:
				continue
			if self._can_move(drone, next_hub):
				planned_moves.append((drone, next_hub))
				planned_ids.add(drone.id)
		self._apply_moves(planned_moves)
		print()
		self.turn += 1
		return self._end_simulation(self.drones)