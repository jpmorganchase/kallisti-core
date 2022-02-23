.DEFAULT_TARGET := clean
.PHONY: test smoke
.PHONY: deps

ifndef ENV
ENV=dev
endif

ifeq ($(OS),Windows_NT)
PYDIST_UTIL=$(HOME)/pydistutils.cfg
else
PYDIST_UTIL=~/.pydistutils.cfg
endif

PYTHON=python
PIP=pip

MIN_TEST_COVERAGE_PERCENTAGE=97

clean:
	rm -rf coverage
	rm -rf records
	rm -rf build/
	rm -rf fileupload/
	rm -rf *.egg-info
	rm -f ./vendor/*
	rm -rf .eggs/*

deps:
	$(PIP) install -r requirements.txt --user
	$(PIP) install -r requirements-dev.txt --user
	$(PYTHON) manage.py migrate

test:
	$(PYTHON) manage.py test

test_with_coverage:
	$(PYTHON) -m coverage run manage.py test
	$(PYTHON) -m coverage report --fail-under=$(MIN_TEST_COVERAGE_PERCENTAGE)
	$(PYTHON) -m coverage html
	start coverage/htmlcov/index.html

lint:
	$(PYTHON) -m flake8 --exclude=kallisticore/migrations/* kallisticore/ tests/ config/

runserver:
	$(PYTHON) manage.py run_huey
	$(PYTHON) manage.py runserver

ci:
	$(PYTHON) -m coverage run manage.py test
	$(PYTHON) -m coverage report --fail-under=$(MIN_TEST_COVERAGE_PERCENTAGE)
	$(PYTHON) -m coverage html
	$(PYTHON) -m coverage xml

sdist: clean
	$(PYTHON) manage.py collectstatic --no-input
	$(PYTHON) setup.py sdist

VERSION=$(shell $(PYTHON) setup.py --version)

ifndef SEMANTIC_VERSION_TYPE
SEMANTIC_VERSION_TYPE=patch
endif
release_prepare:
	# Usage:
	# make SEMANTIC_VERSION_TYPE=<type> release_prepare
	# "type" can be major/minor/patch
	# Note: By default `make release_prepare` will bump patch
	echo "Bumping $(SEMANTIC_VERSION_TYPE) version"
	bumpversion --verbose $(SEMANTIC_VERSION_TYPE)

update_release_notes:
	echo "Updating release notes"
	sh -e ./update_release_notes.sh $(SEMANTIC_VERSION_TYPE) $(BRANCH_NAME)