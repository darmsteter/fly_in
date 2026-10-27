from pydantic import BaseModel, Field, model_validator
from enum import StrEnum
from math import inf

class ConfigKey(StrEnum):
	NB_DRONES = "nb_drones"
	START_HUB = "start_hub"
	END_HUB = "end_hub"
	HUB = "hub"
	CONNTCTION = "connection"

class MetadataKey(StrEnum):
	COLOR = "color"
	ZONE = "zone"
	MAX_DRONES = "max_drones"
	MAX_LINK_CAPACITY = "max_link_capacity"

class ZoneEnum(StrEnum):
	NORMAL = "normal"
	BLOCKED = "blocked"
	RESTRICTED = "restricted"
	PRIORITY = "priority"

	def get_distance(self) -> float:
		match self:
			case ZoneEnum.NORMAL:
				return 1
			case ZoneEnum.PRIORITY:
				return 0.99
			case ZoneEnum.BLOCKED:
				return inf
			case ZoneEnum.RESTRICTED:
				return 2

class Color(StrEnum):
	RED = '\033[31m'
	GREEN = '\033[32m'
	YELLOW = '\033[33m'
	BLUE = '\033[34m'
	PURPLE = '\033[35m'
	LIGTH_BLUE = '\033[36m'
	CYAN = '\033[96m'
	ORANGE = '\033[38;5;208m'
	RESET = '\033[0m'

class Network(BaseModel):
	nb_drones: int = Field(..., gt=0)
	start_hub: Hub = Field(...)
	end_hub: Hub = Field(...)
	hubs: dict[str, Hub] = Field(...)
	conections: list[Conection] = Field(...)

	@model_validator(mode='after')
	def check_network(self) -> 'Network':
		if self.start_hub.name in self.hubs or self.end_hub.name in self.hubs:
			raise ValueError("The hub name cannot be the same as the start or the exit.")
		return self

class Hub(BaseModel):
	name: str = Field(..., min_length=1)
	x: int = Field(...)
	y: int = Field(...)
	zone: ZoneEnum = ZoneEnum.NORMAL
	color: str | None = Field(None, min_length=1)
	max_drones: int  = 1

	@model_validator(mode="after")
	def hub_check(self) -> "Hub":
		if "-" in self.name:
			raise ValueError("The connection syntax forbids dashes in zone names.")
		return self

	def __str__(self):
		match self.color:
			case 'red':
				color = Color.RED
			case 'green':
				color = Color.GREEN
			case 'yellow':
				color = Color.YELLOW
			case 'blue':
				color = Color.BLUE
			case 'ligthblue':
				color = Color.LIGTH_BLUE
			case 'purple':
				color = Color.PURPLE
			case 'cyan':
				color = Color.CYAN
			case 'orange':
				color = Color.ORANGE
			case _:
				raise ValueError(
					f"Unknown color: {self.color}. Can be on of list: red, green, yellow, blue, ligthblue, purple, cyan or none."
					)
		return f"{color}{self.name}{Color.RESET}"

class Conection(BaseModel):
	name1: str = Field(..., min_length=1)
	name2: str = Field(..., min_length=1)
	max_link_capacity: int = 1
	passed_in_turn: int = 0

	@model_validator(mode="after")
	def conection_check(self) -> "Conection":
		if "-" in self.name1 or "-" in self.name2:
			raise ValueError("The connection syntax forbids dashes in zone names.")
		return self

	def connections_conflict(self, conection2: Conection):
		if self.name1 == conection2.name1 and self.name2 == conection2.name2:
			return True
		elif self.name1 == conection2.name2 and self.name2 == conection2.name1:
			return True
		return False