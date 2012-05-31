# Copyright 2010-2012 Canonical Ltd.

VIRTUALENV=dga-env

ACTIVATE=. dga-env/bin/activate

DJANGO_13_PROJECT=cd test_projects/dga_django_1_3
DJANGO_14_PROJECT=cd test_projects/dga_django_1_4

DJANGO_MANAGE=python manage.py

# virtualenv & requirements

bin/activate:
	@echo ">>> Creating virtualenv..."
	virtualenv $(VIRTUALENV)

requirements-test: bin/activate
	@echo ">>> Installing requirements..."
	$(ACTIVATE) && pip install -r requirements.test.txt

requirements-14:
	@echo ">>> Installing requirements for Django 1.4..."
	$(ACTIVATE) && pip install -r requirements.django1.4.txt

requirements-13:
	@echo ">>> Installing requirements for Django 1.3..."
	$(ACTIVATE) && pip install -r requirements.django1.3.txt

env: bin/activate requirements-test
	@echo ">>> Test environment set up..."

clean-env:
	rm -rf dga-env

# Documentation

docs:
	@echo ">>> Creating documentation..."
	$(ACTIVATE) && cd docs && make html

clean-docs:
	cd docs && make clean

# Tests

test-14: env requirements-14
	@echo ">>> Testing with django_group_access.models.AccessGroup..."
	$(ACTIVATE) && $(DJANGO_14_PROJECT) && $(DJANGO_MANAGE) test django_group_access
	@echo ">>> Testing with django.contrib.auth.models.Group..."
	$(ACTIVATE) && $(DJANGO_14_PROJECT) && $(DJANGO_MANAGE) test django_group_access --settings=settings_auth_groups

test-13: env requirements-13
	@echo ">>> Testing with django_group_access.models.AccessGroup..."
	$(ACTIVATE) && $(DJANGO_13_PROJECT) && $(DJANGO_MANAGE) test django_group_access
	@echo ">>> Testing with django.contrib.auth.models.Group..."
	$(ACTIVATE) && $(DJANGO_13_PROJECT) && $(DJANGO_MANAGE) test django_group_access --settings=settings_auth_groups

test: test-13 test-14
	@echo ">>> Tests complete."

pep8:
	$(CHANGED) $(PEP8)

pylint:
	$(CHANGED) $(PYLINT)

# Cleanup

clean:
	find . -name '*~' -delete
	find . -name '*.pyc' -delete
	bzr clean-tree

clean-all: clean clean-env clean-docs
	@echo ">>> All cleaned up!"
