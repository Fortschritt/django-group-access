#!/usr/bin/env python

from setuptools import setup


setup(
    name='django-group-access',
    author="Foo Bar",  # FIXME!
    author_email="foo.bar@example.com",   # FIXME!
    description=("Base Django model to add access control, via groups, to "
                 "objects."),
    url='https://launchpad.net/django-group-access',
    license='LGPLv3', # FIXME!
    keywords=['django', 'ownership', 'models'],
    version="0.0.1",
    classifiers=[
        "Development Status :: 4 - Beta",
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
    ],
    zip_safe=True,
    packages=['django_group_access'],
    # dependencies
    install_requires=['django >= 1.0'],  # XXX: Is this correct?
)
