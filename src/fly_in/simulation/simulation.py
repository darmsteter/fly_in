from .models import Drone

from ..map_parser.models import Network, Connection, Hub
from ..map_parser.enums import ZoneEnum
from ..find_path import find_path
from ..errors import SimulationException


class Simulation:
    """Simulate drones moving through a network of hubs."""

    def __init__(
            self,
            network: Network,
            graph: dict[str, list[Connection]]
    ) -> None:
        """Initialize the simulation and assign a path to each drone.

        Args:
        network: Map configuration, including hubs, connections,
            and drone count.
        graph: Directed graph used to find routes between hubs.
        """

        self._network = network
        self._graph = graph
        self._drones: list[Drone] = self._create_drones()
        self.turn = 0
        self._turns_history: dict[int, dict[int, str]] = {}
        self._reserved: dict[str, set[int]] = {}

    def run_turn(self) -> bool:
        """Execute one simulation turn.

        Prepare the next turn's state, plan drone movements, retry moves
        that were initially blocked, and apply the planned movements.
        Returns:
        True if all drones have reached the destination; otherwise, False.
        """

        self._prepare_turn()

        planned_moves: list[tuple[Drone, Hub]] = []
        waiting_drones = self._plan_initial_moves(planned_moves)

        self._retry_waiting_drones(waiting_drones, planned_moves)
        self._apply_planned_moves(planned_moves)

        print()
        self.turn += 1

        return self._all_drones_finished(self._drones)

    def _create_drones(self) -> list[Drone]:
        """Create drones and distribute the available routes among them.

        Routes are assigned cyclically if there are fewer routes than drones.

        Returns:
            A list of initialized drones, each starting at the beginning
            of its path.
        """

        drones: list[Drone] = []
        paths = find_path(self._network, self._graph)
        for number in range(1, self._network.nb_drones + 1):
            drones.append(Drone(
                id=number,
                path=paths[(number - 1) % len(paths)],
                path_index=0)
            )
        return drones

    def _get_initial_positions(self) -> dict[int, str]:
        """Build the initial position map for all drones.

        Active drones are placed at the start hub. Finished drones are placed
        at the destination hub.

        Returns:
            A mapping from drone IDs to hub names.
        """

        positions: dict[int, str] = {}
        start = self._network.start_hub.name
        end = self._network.end_hub.name
        for drone in self._drones:
            if drone.finished:
                positions[drone.id] = end
            else:
                positions[drone.id] = start
        return positions

    def _prepare_turn(self) -> None:
        """Initialize the state for the current turn and reset
        connection usage.

        Preserve the current positions as the basis for the next turn and
        reset each connection's per-turn capacity counter.
        """

        if self.turn not in self._turns_history:
            self._turns_history[self.turn] = self._get_initial_positions()

        self._turns_history[self.turn + 1] = (
            self._turns_history[self.turn].copy()
        )

        for connection in self._network.connections:
            connection.passed_in_turn = 0

    def _plan_initial_moves(
            self,
            planned_moves: list[tuple[Drone, Hub]]
    ) -> list[Drone]:
        """Plan each active drone's next move.

         Drones that cannot move are collected for a second attempt, unless
         they are already traveling through a connection.

         Args:
             planned_moves: List of movements successfully planned so far.

         Returns:
             Drones eligible for a second movement attempt.
         """

        waiting_drones: list[Drone] = []

        for drone in self._drones:
            if drone.finished:
                continue

            next_hub = self._get_next_hub(drone)
            if next_hub is None:
                continue

            if self._try_plan_move(drone, next_hub, planned_moves):
                continue

            current_position = self._turns_history[self.turn][drone.id]
            if current_position != "connection":
                waiting_drones.append(drone)

        return waiting_drones

    def _retry_waiting_drones(
            self,
            waiting_drones: list[Drone],
            planned_moves: list[tuple[Drone, Hub]]
    ) -> None:
        """Retry movement planning for drones that were previously blocked.

        Successful movements are appended to planned_moves. Drones that still
        cannot move remain in their current positions.
        """

        for drone in waiting_drones:
            next_hub = self._get_next_hub(drone)
            if next_hub is None:
                continue

            self._try_plan_move(drone, next_hub, planned_moves)

    def _try_plan_move(
            self,
            drone: Drone,
            next_hub: Hub,
            planned_moves: list[tuple[Drone, Hub]]
    ) -> bool:
        """Attempt to reserve a movement for a drone.

        The movement is added to planned_moves only if _try_move accepts it.

        Returns:
            True if the movement was planned; otherwise, False.
        """

        if not self._try_move(drone, next_hub):
            return False

        planned_moves.append((drone, next_hub))
        return True

    def _try_move(self, drone: Drone, next_hub: Hub) -> bool:
        """Validate and register a drone's next movement.

        Reject the movement if the directed connection does not exist, the
        destination is reserved for another drone, the connection is at
        capacity, or the destination hub has no available capacity.

        Entering a restricted hub reserves a place for the drone and records
        it on the connection for the intermediate turn. A drone already on a
        connection completes its traversal to the next hub.

        This method updates movement-related state when a movement is accepted.

        Returns:
            True if the movement is accepted; otherwise, False.
        """

        current_positions = self._turns_history[self.turn]
        current_hub_name = drone.path[drone.path_index]
        next_hub_name = next_hub.name

        connection = self._get_connection(current_hub_name, next_hub_name)

        if connection is None:
            return False

        if self._is_reserved_for_other_drone(next_hub_name, drone.id):
            return False

        if current_positions[drone.id] == "connection":
            self._complete_connection_traversal(drone, next_hub_name)
            return True

        if connection.passed_in_turn >= connection.max_link_capacity:
            return False

        if not self._has_hub_capacity(next_hub):
            return False

        if next_hub.zone is ZoneEnum.RESTRICTED:
            self._start_restricted_traversal(drone, next_hub_name, connection)
        else:
            connection.passed_in_turn += 1
            self._turns_history[self.turn + 1][drone.id] = next_hub_name

        return True

    def _has_hub_capacity(self, hub: Hub) -> bool:
        """Check whether a hub can accommodate another drone next turn.

        The destination hub has unlimited capacity. For other hubs, account
        for both planned occupancy and places reserved for drones in transit.

        Returns:
            True if the hub has sufficient capacity; otherwise, False.
        """

        if hub is self._network.end_hub:
            return True

        next_positions = self._turns_history[self.turn + 1]
        drones_in_hub = list(next_positions.values()).count(hub.name)
        reserved_drones = len(self._reserved.get(hub.name, set()))

        return drones_in_hub + reserved_drones < hub.max_drones

    def _is_reserved_for_other_drone(
            self,
            hub_name: str,
            drone_id: int,
    ) -> bool:
        """Check whether a hub is reserved exclusively for other drones.

        A reservation belonging to the requesting drone does not block
        its entry.

        Returns:
            True if another drone holds a reservation for the hub;
            otherwise, False.
        """
        return (
                hub_name in self._reserved
                and drone_id not in self._reserved[hub_name]
        )

    def _complete_connection_traversal(
            self,
            drone: Drone,
            next_hub_name: str,
    ) -> None:
        """Move a drone from a connection into its reserved destination hub.

        Release the drone's reservation and update its position
        for the next turn.
        """

        reserved_drones = self._reserved.get(next_hub_name, set())

        if drone.id in reserved_drones:
            reserved_drones.remove(drone.id)

            if not reserved_drones:
                self._reserved.pop(next_hub_name)

        self._turns_history[self.turn + 1][drone.id] = next_hub_name

    def _start_restricted_traversal(
            self,
            drone: Drone,
            hub_name: str,
            connection: Connection,
    ) -> None:
        """Begin a two-turn traversal into a restricted hub.

        Reserve a place in the destination hub, consume one unit of connection
        capacity for this turn, and record the drone on the connection rather
        than inside the hub.
        """

        self._reserved.setdefault(hub_name, set()).add(drone.id)
        connection.passed_in_turn += 1
        self._turns_history[self.turn + 1][drone.id] = "connection"

    def _apply_planned_moves(
            self,
            planned_moves: list[tuple[Drone, Hub]]
    ) -> None:
        """Apply accepted movements and print their representation.

        Drones entering restricted hubs are reported on the connection during
        the intermediate turn. Other accepted movements advance the drone's
        path index. Mark a drone as finished when it reaches its destination.
        """

        for drone, next_hub in planned_moves:
            was_in_connection = (
                    self._turns_history[self.turn][drone.id] == "connection"
            )

            if next_hub.zone is ZoneEnum.RESTRICTED and not was_in_connection:
                connection = self._get_connection(
                    drone.path[drone.path_index],
                    next_hub.name
                )
                if connection is None:
                    raise SimulationException(
                        f"Connection not found between "
                        f"{drone.path[drone.path_index]} and {next_hub.name}."
                    )
                print(
                    f"D{drone.id}-connection:"
                    f"{self._get_hub(connection.name1)}-"
                    f"{self._get_hub(connection.name2)}", end=" "
                )
                continue

            print(f"D{drone.id}-{next_hub}", end=" ")
            drone.path_index += 1

            if drone.path_index == len(drone.path) - 1:
                drone.finished = True

    def _get_next_hub(self, drone: Drone) -> Hub | None:
        """Resolve the next hub in a drone's assigned path.

        Returns:
            The next hub, or None if the drone has finished its route.
        """

        if not drone.finished:
            next_hub = drone.path[drone.path_index + 1]
            if next_hub == self._network.end_hub.name:
                return self._network.end_hub
            return self._network.hubs[next_hub]
        return None

    def _get_hub(self, hub_name: str) -> Hub | None:
        """Find a hub by name, including the start and destination hubs.

        Returns:
            The matching hub, or None if the name is not present
            in the network.
        """

        if hub_name == self._network.start_hub.name:
            return self._network.start_hub
        if hub_name == self._network.end_hub.name:
            return self._network.end_hub
        return self._network.hubs.get(hub_name)

    def _get_connection(
            self,
            current_hub_name: str,
            next_hub_name: str
    ) -> Connection | None:
        """Find a directed connection from the current hub to the next hub.

        A connection in the opposite direction does not match.

        Returns:
            The matching connection, or None if the directed
            connection is absent.
        """

        for connection in self._network.connections:
            if (
                    connection.name1 == current_hub_name
                    and connection.name2 == next_hub_name
            ):
                return connection
        return None

    @staticmethod
    def _all_drones_finished(drones: list[Drone]) -> bool:
        """Check whether every drone has reached its destination.

        Returns:
            True if all drones are finished; otherwise, False.
        """

        for drone in drones:
            if not drone.finished:
                return False
        return True
