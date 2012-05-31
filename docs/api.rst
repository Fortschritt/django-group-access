API
===

Manager
-------

``accessible_by_user``
~~~~~~~~~~~~~~~~~~~~

.. method:: Manager.accessible_by_user(self, user)

Returns a ``QuerySet`` with access control filtering activated for the user.


Queryset
--------

``accessible_by_user``
~~~~~~~~~~~~~~~~~~~~

.. method:: QuerySet.accessible_by_user(self, user)

Returns a ``QuerySet`` with access control filtering activated for the user.


``unrestricted``
~~~~~~~~~~~~~~~~

.. method:: QuerySet.unrestricted(self)

Returns a ``QuerySet`` with access control filtering turned off.


Registration
------------

``register``
~~~~~~~~~~~~

.. method:: register(model_class, control_relation=False, unrestricted_manager=False, auto_filter=True, owner=True)

Registers a model class with django-group-access.

``model_class``: The model class to register.

``control_relation``: The "child" relation that controls access to the class.

``unrestricted_manager``: Attribute name to use for a manager that will return unrestricted querysets by default (most useful if you're using the middleware that automatically applies access control based on the currently logged in user).

``auto_filter``: Determines if this model class is included in the automatic filtering provided by the middleware.

``owner``: Determines if an owner foreignkey to the Django auth User class is added to the model.
