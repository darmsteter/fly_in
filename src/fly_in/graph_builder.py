from .map_parser import Network, Connection
from .errors import MapParsingError


def build_graph(network: Network) -> dict[str, list[Connection]]:
    """Build a directed graph from the network configuration.

    Args:
        network: The parsed network configuration.

    Returns:
        An adjacency list representing the directed graph.

    Raises:
        MapParsingError: If a connection references an unknown hub,
            starts at the exit hub, or duplicates an existing connection.
    """
    graph: dict[str, list[Connection]] = {network.start_hub.name: []}

    for hub_name in network.hubs:
        if hub_name != network.start_hub.name:
            graph[hub_name] = []

    for connection in network.connections:
        if connection.name1 == network.end_hub.name:
            raise MapParsingError(
                "Connection cannot start at "
                f"the exit hub '{connection.name1}'."
            )

        if connection.name1 not in graph:
            raise MapParsingError(
                f"Unknown hub name '{connection.name1}' "
                f"in connection: {connection}."
            )

        if (
                connection.name2 not in graph
                and connection.name2 != network.end_hub.name
        ):
            raise MapParsingError(
                f"Unknown hub name '{connection.name2}' "
                f"in connection: {connection}."
            )

        for connections in graph.values():
            if any(
                    connection.conflicts_with(existing)
                    for existing in connections
            ):
                raise MapParsingError(
                    f"Duplicate link between two hubs: "
                    f"{connection.name1} and {connection.name2}."
                )
        graph[connection.name1].append(connection)
    return graph
