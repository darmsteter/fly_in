from pydantic import ValidationError


class MapParsingError(Exception):
    """Exception raised when a map file cannot be parsed."""

    def __init__(self, message: str = "Unknown map parsing error.") -> None:
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return f"{self.message}"


class PathFindingError(Exception):
    """Exception raised when a path finding error occurs."""

    def __init__(self, message: str = "Unknown path finding error.") -> None:
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return f"{self.message}"


class SimulationException(Exception):
    """Exception raised when an error occurs during simulation."""

    def __init__(self, message: str = "Unknown simulation error.") -> None:
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return f"{self.message}"


def format_validation_error(e: ValidationError) -> str:
    """Format Pydantic validation errors into readable messages.

    Args:
        e: Pydantic validation error containing one or more errors.

    Returns:
        A string containing formatted error messages, separated by newlines.
    """

    messages = []

    for error in e.errors():
        field = error["loc"][-1] if error["loc"] else "unknown field"
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
