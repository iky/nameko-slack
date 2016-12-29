test: flake8 pylint pytest

flake8:
	flake8 nameko_slack tests

pylint:
	pylint nameko_slack -E

pytest:
	coverage run --concurrency=eventlet --source nameko_slack --branch -m pytest tests
	coverage report --show-missing --fail-under=100
