from pydantic import BaseModel, Field, model_validator, field_validator
from map_parser.enums import ZoneEnum
from map_parser.colors import Color, rainbow

class Network(BaseModel):
	"""Represent the parsed drone network and its configuration."""

	nb_drones: int = Field(gt=0)
	start_hub: Hub
	end_hub: Hub
	hubs: dict[str, Hub]
	connections: list[Connection]

	@model_validator(mode='after')
	def validate_hub_names(self) -> 'Network':
		"""Ensure start and end hubs are not duplicated in regular hubs."""
		if self.start_hub.name in self.hubs or self.end_hub.name in self.hubs:
			raise ValueError("The hub name cannot be the same as the start or the exit.")
		return self

class Hub(BaseModel):
	"""Represent a zone in the drone network."""

	name: str = Field(min_length=1)
	x: int
	y: int
	zone: ZoneEnum = ZoneEnum.NORMAL
	color: str = Color.RESET.name
	max_drones: int = Field(default=1, gt=0)


	@field_validator('color')
	@classmethod
	def validate_color(cls, field: str) -> str:
		if field.lower() == "rainbow":
			return field

		if field.upper() not in Color.__members__:
			raise ValueError(f"Unknown color: {field}")
		return field

	@model_validator(mode="after")
	def validate_name(self) -> "Hub":
		"""Ensure the hub name does not contain forbidden characters."""

		if "-" in self.name:
			raise ValueError(
				"Hub names cannot contain dashes because they are used "
				"to separate hub names in connection declarations."
			)
		return self

	def __str__(self):
		"""Return the hub name formatted with its configured color."""

		if self.color == "rainbow":
			return  rainbow(self.name)
		try:
			color = Color[self.color.upper()]
		except KeyError:
			raise ValueError(f"Unknown color: {self.color}")
		return f"{color}{self.name}{Color.RESET}"

class Connection(BaseModel):
	"""Represent a connection between two hubs in the network."""

	name1: str = Field(min_length=1)
	name2: str = Field(min_length=1)
	max_link_capacity: int = Field(default=1, ge=0 )
	passed_in_turn: int = Field(default=0, ge=0)

	@model_validator(mode="after")
	def validate_hub_names(self) -> "Connection":
		"""Ensure hub names do not contain the connection separator."""

		if "-" in self.name1 or "-" in self.name2:
			raise ValueError(
				"Hub names cannot contain dashes because dashes separate "
				"hub names in connection declarations."
			)
		if self.name1 == self.name2:
			raise ValueError("A connection cannot link a hub to itself.")
		return self

	def conflicts_with(self, other: "Connection"):
		"""Return whether another connection links the same two hubs.

		Connections are considered identical regardless of endpoint order.
		"""
		if self.name1 == other.name1 and self.name2 == other.name2:
			return True
		elif self.name1 == other.name2 and self.name2 == other.name1:
			return True
		return False