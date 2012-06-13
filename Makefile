# Copyright 2010-2012 Canonical Ltd.

VIRTUALENV=dga-env
PIP_INSTALL=pip install --download-cache=dga-env/
ACTIVATE=. dga-env/bin/activate
DJANGO_VERSION=`python -c "import django; print '_'.join(django.get_version().split('.')[:2]);"`

MAKE=make

DJANGO_MANAGE=python manage.py

# virtualenv & requirements

bin/activate:
	@echo ">>> Creating virtualenv..."
	virtualenv $(VIRTUALENV)

requirements-14:
	@echo ">>> Installing requirements for Django 1.4..."
	$(ACTIVATE) && $(PIP_INSTALL) -r requirements.django1.4.txt

requirements-13:
	@echo ">>> Installing requirements for Django 1.3..."
	$(ACTIVATE) && $(PIP_INSTALL) -r requirements.django1.3.txt

env: bin/activate
	@echo ">>> Test environment set up..."

clean-env:
	rm -rf dga-env

# Documentation

htmldocs:
	@echo ">>> Creating documentation..."
	$(ACTIVATE) && $(MAKE) -C docs html

clean-docs:
	cd docs && make clean

# Tests

test-14: env requirements-14 test
	@echo ">>> Tests for Django 1.4 complete."

test-13: env requirements-13 test
	@echo ">>> Tests for Django 1.3 complete."

test-all: test-13 test-14
	@echo ">>> Tests complete."

test:
	@echo ">>> Testing with django_group_access.models.AccessGroup..."
	cd test_projects/dga_django_$(DJANGO_VERSION) && $(DJANGO_MANAGE) test django_group_access
	@echo ">>> Testing with django.contrib.auth.models.Group..."
	cd test_projects/dga_django_$(DJANGO_VERSION) && $(DJANGO_MANAGE) test django_group_access --settings=settings_auth_groups

pep8:
	$(CHANGED) $(PEP8)

pylint:
	$(CHANGED) $(PYLINT)

# Cleanup

clean:
	find . -name '*~' -delete
	find . -name '*.pyc' -delete

clean-all: clean clean-env clean-docs
	@echo ">>> All cleaned up!"
