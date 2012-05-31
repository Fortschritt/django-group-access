Installation and Configuration
==============================

Installation
------------

Add ``django_group_access`` to your ``INSTALLED_APPS`` in ``settings.py``


.. _install-middleware:

Auto filtering middleware
-------------------------

**Optional**

To enable automatic filtering of querysets, add
``django_group_access.middleware.DjangoGroupAccessMiddleware``
to ``MIDDLEWARE_CLASSES`` in ``settings.py``


Settings
--------

.. _group-model-setting:

DGA_GROUP_MODEL
~~~~~~~~~~~~~~~

**Optional**

Allows you to nominate another model to use in place of the AccessGroup model.
Specify the other model using ``app.modelname``

Example::

  DGA_GROUP_MODEL = 'auth.group'

See the group api documentation if you want to implement your own group model.

The most common setting for this is ``auth.group`` which will use the django authentication group model.

Defaults to ``django_group_access.accessgroup``


DGA_UNSHARED_RECORDS_ARE_PUBLIC
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Optional**

If set, makes records accessible to all users unless they have been shared with specific groups, in which case they will be limited to those groups. Otherwise records will be private by default.

Example::

  DGA_UNSHARED_RECORDS_ARE_PUBLIC = True

Defaults to ``False``

