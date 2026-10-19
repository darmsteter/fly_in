from pydantic import BaseModel, Field, model_validator, ConfigDict

class Drone(BaseModel):
	model_config = ConfigDict(validate_assignment=True)

	id: int = Field(..., ge=1)
	path: list[str] = Field(..., min_length=2)
	path_index: int = Field(..., ge=0)
	finished: bool = False

	@model_validator(mode='after')
	def drone_check(self) -> 'Drone':
		if self.path_index >= len(self.path):
			raise ValueError("Drone path index is out of range.")
		return self