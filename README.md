*This project has been created as part of the 42 curriculum by skorenev.*

# Fly-in

## Description

**Fly-in** is a Python project focused on graph algorithms, pathfinding, and simulation.

The goal of the project is to find efficient routes for a fleet of drones travelling through a network of interconnected hubs. Each drone must move from a starting hub to a destination hub while respecting the network's constraints.

The network is described in a map configuration file. It contains information about the number of drones, hubs, connections, and optional metadata such as zone types, hub capacities, and connection capacities.

The project parses this configuration, builds a directed graph, calculates possible routes, and simulates drone movements turn by turn.

The main challenges are:
- Parsing and validating map configurations.
- Representing the network as a directed graph.
- Finding efficient paths while considering different zone costs.
- Coordinating multiple drones without violating occupancy and connection constraints.
- Producing a clear visual representation of the simulation.

## Features

- Map parsing and validation.
- Directed graph construction.
- Shortest-path search using Dijkstra's algorithm.
- Alternative route search using Yen's algorithm.
- Multi-drone movement simulation.
- Hub occupancy and connection capacity management.
- Support for different zone types.
- Colored terminal output for easier visualization.

## Instructions


### Installation

Install the dependencies:

```bash
uv sync
```
or
```bash
make install
```

### Execution

Run the project:

```bash
make
```

The program reads a map configuration and runs the drone simulation.

Use a valid map file following the project's map format.

## Map Configuration

A map describes the network in which the drones move.

It includes:

- `nb_drones` — the number of drones.
- `start_hub` — the starting hub.
- `end_hub` — the destination hub.
- `hub` — an intermediate hub.
- `connection` — a directed connection between two hubs.

Example:

```text
nb_drones: 3

start_hub: start 0 0
end_hub: end 10 0

hub: A 2 0
hub: B 5 2 [zone=priority]
hub: C 5 -2 [zone=restricted max_drones=2]

connection: start-A
connection: A-B
connection: A-C [max_link_capacity=2]
connection: B-end
connection: C-end
```

### Hub metadata

Optional metadata can be used to configure hubs:

| Metadata | Description |
|---|---|
| `zone` | Defines the zone type. |
| `color` | Defines the hub's display color. |
| `max_drones` | Sets the maximum number of drones allowed in the hub simultaneously. |

### Zone types

Different zone types affect route selection:

| Zone | Description |
|---|---|
| `normal` | Standard zone with the default movement cost. |
| `priority` | Zone with the default movement cost. |
| `restricted` | Zone with a higher movement cost and special transit rules. |
| `blocked` | Zone that cannot be used as part of a route. |

### Connection metadata

| Metadata | Description |
|---|---|
| `max_link_capacity` | Defines how many drones can use a connection simultaneously. |

## Algorithm Choices and Implementation

### 1. Map Parsing and Validation

The map parser reads the configuration file line by line.

It extracts the configuration values, hubs, connections, and metadata. Regular expressions are used to validate the syntax of individual declarations.

Pydantic models are used to validate the resulting data structures and enforce their types and constraints.

Additional checks ensure that:
- Hub names are unique.
- Hub coordinates are unique.
- There is exactly one starting hub and one destination hub.
- Metadata keys are valid and are not duplicated.
- Connections reference valid hubs.
- The configuration follows the required declaration order.

The parser separates reading and syntax validation from data modelling, making the resulting network easier to work with in other parts of the project.

### 2. Graph Representation

The network is represented as a directed graph using an adjacency list.

Each hub is represented by a vertex, and each connection represents a directed edge between two hubs.

An adjacency list was chosen because it provides an efficient way to access the outgoing connections of a hub without requiring a matrix containing every possible pair of vertices.

The graph is built from the validated network configuration.

### 3. Shortest Path — Dijkstra's Algorithm

Dijkstra's algorithm is used to find the shortest route between the starting hub and the destination.

The algorithm calculates the total cost of a path rather than considering only the number of connections.

Zone types influence the cost of entering a hub:
- Normal and priority zones have the default cost.
- Restricted zones have a higher cost.
- Blocked zones are excluded from route selection.

This allows the pathfinding algorithm to consider the characteristics of the network when choosing a route.

### 4. Alternative Routes — Yen's Algorithm

Finding only one shortest path may not be sufficient when multiple drones need to travel through the same network.

To find alternative routes, the project uses Yen's algorithm.

Yen's algorithm finds loopless paths in order of increasing cost. It works by taking an existing path, temporarily excluding selected hubs or connections, and searching for alternative paths using Dijkstra's algorithm.

This makes it possible to discover different routes and reduce dependence on a single path.

### 5. Drone Simulation

Once routes have been calculated and assigned, the simulation manages drone movements turn by turn.

Each drone maintains its own route and current position.

During each turn, the simulation checks whether a drone can move to its next destination while respecting the network rules.

The simulation considers:

- **Hub occupancy:** A hub can contain only a limited number of drones at a time. The default capacity is one drone unless configured otherwise.
- **Start and destination hubs:** These hubs allow multiple drones to share the same space.
- **Connection capacity:** A connection can be used by a limited number of drones simultaneously.
- **Restricted zones:** Entering a restricted zone requires additional transit time. A drone must complete the transition after the required number of turns rather than waiting on the connection for available space.
- **Movement coordination:** Drones must be coordinated so that their movements do not violate hub or connection capacity constraints.

The simulation records the state of the drones after each turn and continues until all drones reach the destination.

## Visual Representation

The project uses colored terminal output to make the simulation easier to follow.

### Hub colors

Hubs can be displayed using different colors. This makes it easier to distinguish locations and follow drone movements through the network.

### Zone visualization

Zone types can be represented visually, helping users identify different areas of the network and understand why certain routes may be preferred or avoided.

### Drone movement

The simulation output displays drone positions turn by turn.

Connections can also be represented explicitly when a drone is in transit between hubs.

This visual representation helps users:
- Follow the progress of individual drones.
- Understand how drones move through the network.
- Identify shared routes and potential bottlenecks.
- Observe how capacity restrictions affect movement.
- Compare the behaviour of different routes.

## Project Structure

```text
src/
└── fly_in/
    ├── __main__.py
    ├── fly_in.py
    ├── errors.py
    ├── find_path.py
    ├── graph_builder.py
    ├── map_parser/
    │   ├── colors.py
    │   ├── enums.py
    │   ├── models.py
    │   └── parser.py
    └── simulation/
        ├── models.py
        └── simulation.py
```
The project is divided into separate modules, each responsible for a specific part of the application:
- map_parser — reads and validates map configuration files.
- graph_builder.py — constructs the directed graph.
- find_path.py — implements pathfinding algorithms.
- simulation — manages drones and their movements.
- fly_in.py — coordinates the main application flow.
- errors.py — contains custom exceptions and validation error formatting.

## Resources

### Documentation and References
- Python Documentation
- Pydantic Documentation
- uv Documentation
- Dijkstra's Algorithm — Wikipedia
- Yen's Algorithm — Wikipedia
- Graph Theory — Wikipedia

### AI Usage

AI assistance was used for:

- **Learning and research:** Understanding graph algorithms and pathfinding concepts.
- **Code quality:** Type annotations, Python conventions.
- **Documentation:** Structuring and preparing the README documentation.

The implementation, design decisions, testing, and integration of the project were carried out by the author.