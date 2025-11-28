.PHONY: install test clean run lint format

install:
	./runme.sh

test:
	python -m pytest tests/ -v --cov=src

run:
	python main.py

clean:
	rm -rf output/*.html output/*.md output/plots/* output/logs/*
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete

lint:
	flake8 src/ tests/
	mypy src/

format:
	black src/ tests/
	isort src/ tests/