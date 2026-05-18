WORKDIR = .

req:
	uv sync

req-dev:
	uv sync --extra lint,test

lint:
	uv run ruff format --check ${WORKDIR}
	uv run ruff check ${WORKDIR}
	uv run ty check ${WORKDIR}
	uv run mypy ${WORKDIR}
	uv run fulldoc

lint-fix:
	uv run ruff format ${WORKDIR}
	uv run ruff check --fix ${WORKDIR}
	uv run ty check ${WORKDIR}
	uv run mypy ${WORKDIR}
	uv run fulldoc

run:
	uv run bot.py

test:
	uv run python -m pytest --cov=. --cov-report=term-missing
