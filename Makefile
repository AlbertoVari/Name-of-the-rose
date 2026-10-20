PYTHON ?= python3
SOURCE ?= .upstream

.PHONY: test validate build check demo
test:
	$(PYTHON) -m unittest discover -s tests -v
	$(PYTHON) -m unittest discover -s orchestration -p 'test_*.py' -v
	$(PYTHON) orchestration/check.py orchestration/run.example.json

validate:
	$(PYTHON) -m rose validate --source $(SOURCE)

build:
	$(PYTHON) -m rose build --source $(SOURCE) --output build

check: test validate
	$(PYTHON) -m rose build --source $(SOURCE) --output build --check

demo:
	$(PYTHON) -m rose query "double-entry"
	$(PYTHON) -m rose query "threshold"
	$(PYTHON) -m rose query "CTRFIL0"
