from pydantic import BaseModel, Field, model_validator
from enum import StrEnum

class ConfigKey(StrEnum):
	NB_DRONES = "nb_drones"
	START_HUB = "start_hub"
	END_HUB = "end_hub"
	HUB = "hub"
	CONNTCTION = "connection"

class ZoneEnum(StrEnum):
	NORMAL = "normal"
	BLOCKED = "blocked"
	RESTRICTED = "restricted"
	PRIORITY = "priority"

class Config(BaseModel):
	nb_drones: int = Field(..., gt=0)
	start_hub: str = Field(..., min_length=1)
	end_hub: str = Field(..., min_length=1)

class Hub(BaseModel):
	name: str = Field(..., min_length=1)
	x: int = Field(..., ge=0)
	y: int = Field(..., ge=0)
	zone: ZoneEnum = ZoneEnum.NORMAL
	color: str | None = Field(None, min_length=1)
	max_drones: int  = 1

	@model_validator(mode="after")
	def hub_check(self) -> "Hub":
		if "-" in self.name:
			raise ValueError("The connection syntax forbids dashes in zone names.")
		return self