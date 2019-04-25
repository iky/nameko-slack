test: static pytest

static:
	pre-commit run --all-files

pytest:
	coverage run --concurrency=eventlet --source nameko_slack --branch -m pytest tests
	coverage report --show-missing --fail-under=100
