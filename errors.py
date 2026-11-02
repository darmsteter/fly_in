from pydantic import ValidationError

class MapParsingError(Exception):
	def __init__(self, message: str = "Unknown configuration error.") -> None:
		self.message = message
		super().__init__(self.message)

	def __str__(self) -> str:
		return f"{self.message}"

class SimulationException(Exception):
	def __init__(self, message: str = "Unknown simulation error.") -> None:
		self.message = message
		super().__init__(self.message)

	def __str__(self) -> str:
		return f"{self.message}"
def format_validation_error(e: ValidationError) -> str:
	messages = []

	for error in e.errors():
		field = error['loc'][-1]
		value = error.get('input')
		error_type = error['type']
		context = error.get("ctx", {})

		if error_type == "greater_than":
			messages.append(
				f"Invalid value '{value}' for '{field}'. "
				f"Expected a value greater than {context['gt']}."
			)
		elif error_type == "greater_than_equal":
			messages.append(
				f"Invalid value '{value}' for '{field}'. "
				f"Expected a value of at least {context['ge']}."
			)
		elif error_type == "int_parsing":
			messages.append(
				f"Invalid value '{value}' for '{field}'. "
				"Expected an integer."
			)
		else:
			messages.append(
				f"Invalid value '{value}' for '{field}'. "
			)
	return "\n".join(messages)