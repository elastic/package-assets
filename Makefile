ifeq ($(VENV),)
	PYTHON := python3
else
	PYTHON := source $(VENV)/bin/activate; python3
endif

prereq:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt

lint:
	$(PYTHON) -m flake8 --ignore D203 --max-line-length 120

sanity:
	$(PYTHON) -m bot meta --pedantic
