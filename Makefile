MAIN = fly_in.py
CONFIG = config.txt

all: run

install:
	uv sync

run:
	uv run python3 $(MAIN) $(CONFIG)

debug:
	uv run python3 -m pdb $(MAIN) $(CONFIG)

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .mypy_cache -exec rm -rf {} +

lint:
	flake8
	mypy .

lint-strict:
	flake8
	mypy . --strict

.PHONY: install run debug clean lint lint-strict
