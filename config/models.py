from pydantic import BaseModel, Field
from enum import StrEnum

class ConfigKey(StrEnum):
	NB_DRONES = "nb_drones"
	START_HUB = "start_hub"
	END_HUB = "end_hub"

class config(BaseModel):
	nb_drones: int = Field(..., gt=0)
	start_hub: str = Field(..., min_length=1)
	end_hub: str = Field(..., min_length=1)
