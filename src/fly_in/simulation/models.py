from pydantic import BaseModel, Field, model_validator, ConfigDict


class Drone(BaseModel):
    """Represent a drone moving along a predefined path."""

    model_config = ConfigDict(validate_assignment=True)

    id: int = Field(ge=1)
    path: list[str] = Field(min_length=2)
    path_index: int = Field(ge=0)
    finished: bool = False

    @model_validator(mode='after')
    def validate_path_index(self) -> 'Drone':
        """Ensure the path index is within the path boundaries."""

        if self.path_index >= len(self.path):
            raise ValueError("Drone path index is out of range.")
        return self
