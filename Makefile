MAP = config.txt

all: run

install:
	uv sync

run:
	@uv run python -m src.fly_in $(MAP)

debug:
	uv run python3 -m pdb $(MAIN) $(MAP)

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .mypy_cache -exec rm -rf {} +

lint:
	flake8 src
	mypy . src

lint-strict:
	flake8 src
	mypy . --strict src

.PHONY: install run debug clean lint lint-strict
