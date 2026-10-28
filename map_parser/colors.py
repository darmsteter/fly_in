from enum import StrEnum

class Color(StrEnum):
	"""ANSI escape codes for terminal text colors."""

	RED = '\033[31m'
	GREEN = '\033[32m'
	YELLOW = '\033[33m'
	BLUE = '\033[34m'
	PURPLE = '\033[35m'
	LIGHTBLUE = '\033[36m'
	CYAN = '\033[96m'
	ORANGE = '\033[38;5;208m'
	LIME = '\033[38;5;118m'
	MAGENTA = '\033[95m'
	GOLD = '\033[38;5;220m'
	MAROON = '\033[38;5;124m'
	DARKRED = '\033[38;5;88m'
	VIOLET = '\033[38;5;129m'
	CRIMSON = '\033[38;5;161m'
	RESET = '\033[0m'

def rainbow(text: str) -> str:
	"""Return text with each character colored in a rainbow sequence."""
	colors = [
        Color.RED,
        Color.ORANGE,
		Color.YELLOW,
		Color.GREEN,
		Color.LIGHTBLUE,
		Color.BLUE,
		Color.PURPLE
    ]
	return ''.join(f'{colors[i % len(colors)]}{char}' for i, char in enumerate(text)) + Color.RESET
