from pydantic import BaseModel, Field, model_validator
from enum import StrEnum

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

class Network(BaseModel):
	nb_drones: int = Field(..., gt=0)
	start_hub: Hub = Field(...)
	end_hub: Hub = Field(...)
	hubs: dict[str, Hub] = Field(...)
	conections: list[Conection] = Field(...)

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

class Conection(BaseModel):
	name1: str = Field(..., min_length=1)
	name2: str = Field(..., min_length=1)
	max_link_capacity: int = 1

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