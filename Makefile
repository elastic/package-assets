ifeq ($(VENV),)
	PYTHON := python3
else
	PYTHON := source $(VENV)/bin/activate; python3
endif

ELASTIC_PACKAGE=elastic-package

prereq:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt

pkg-build:
	$(PYTHON) -m build

pkg-sanity:
	$(PYTHON) -m venv test-venv
	(. ./test-venv/bin/activate && pip install dist/*.whl && python3 -c 'import elastic.package.assets')
	rm -r test-venv

lint:
	$(PYTHON) -m flake8 --ignore D203 --max-line-length 120 --exclude assets/production,assets/staging,assets/snapshot,packages/production,packages/staging,packages/snapshot

tests: tests/*.py
	$(PYTHON) -m pytest tests

sanity:
	$(PYTHON) -m bot meta --pedantic
	$(PYTHON) -m bot plan
	$(PYTHON) -m bot download endpoint/8.4.0 test-download
	rm -rf test-download

stack-up:
	STACK_VERSION=`curl -s -H 'Accept: application/vnd.github+json' https://api.github.com/repos/elastic/elasticsearch/releases | \
		jq -r '.[] .tag_name' | \
		sort -V | \
		tail -n1 | \
		sed 's/v//'`; \
	echo "Stack version: $$STACK_VERSION"; \
	$(ELASTIC_PACKAGE) stack up -d --version $$STACK_VERSION

stack-down:
	$(ELASTIC_PACKAGE) stack down

.PHONY: prereq pkg-build pkg-sanity lint tests sanity
