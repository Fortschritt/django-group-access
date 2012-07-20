Integration and use
===================

Registering a model
-------------------

Simple access control
~~~~~~~~~~~~~~~~~~~~~

Before you can use the access controls, you must register the model.

Example::

  from django.db import models
  from django_group_access import registration


  class MyModel(models.Model):
      name = models.CharField(max_length=24)

  registration.register(MyModel)

This will add ``owner``, a foreign key to the Django auth ``User`` class,
and ``access_groups``, a many to many field to whatever access group class
is configured (``django_group_access.models.AccessGroup`` by default).


No individual ownership
~~~~~~~~~~~~~~~~~~~~~~~

If you do not want the ``owner`` field, you can pass ``owner=False`` to
the register call.

Example::

  registration.register(MyModel, owner=False)


Controlling access through related records
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Let's say you have a House, and Rooms in the house. If you have
access to one of the Rooms, you automatically have access to the
House (but only the Room you've been given access to).

You can define "parent" and "child" relationships by using the
``control_relation`` parameter when calling ``register()``

Example::

  from django.db import models
  from django_group_access import registration


  class House(models.Model):
      address = models.CharField(max_length=128)


  class Room(models.Model):
      house = models.ForeignKey(House)
      name = models.CharField(max_length=32)


  registration.register(Room)
  registration.register(House, control_relation='room')


Granting unrestricted status based on custom conditions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want to allow a user unrestricted access to a model's
records based on something other than ``is_superuser`` (for
example, you may have a Hardware model, and a user attribute
called HardwareAdmin) you can pass an array of functions in the
parameter ``unrestricted_access_hooks``.

The functions will be passed one argument, the user. They must
return ``True`` or ``False``.

Example::

  def mike_is_all_powerful(user):
      return user.username == 'mike'
  
  registration.register(MyModel, unrestricted_access_hooks=[mike_is_all_powerful])


A silly example, but if you wanted to grant the user with the username 'mike'
unrestricted access to the MyModel records, that's how you'd do it.

Note: If you register a model with a ``control_relation``, the
unrestricted_access_hooks will be ignored, and the unrestricted_access_hooks
from the control relation's model will be used.


Sharing records
---------------

Sharing records with groups
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Adding groups to ``.access_groups`` on a record will share it with
those groups.

Example::

  obj = MyModel.objects.all()[0]
  group_i_want_to_share_with = AccessGroupModel.objects.get(name='Friends')
  obj.access_groups.add(group_i_want_to_share_with)

`obj` would then become visible to members of the 'Friends' group.


Automatic record sharing
~~~~~~~~~~~~~~~~~~~~~~~~

For ease of sharing data between groups, AccessGroup has a property called
`auto_share_groups`. This is a list of AccessGroups that records owned
by the group will automatically be shared with.

This is only available if you are using the ``AccessGroup`` model provided by
django-group-access.

See :ref:`group-model-setting` for information on configuring which group
model class to use.


View integration
----------------

Filtering querysets
~~~~~~~~~~~~~~~~~~~

To get back only the records a user has access to, use ``accessible_by_user``

Example::

  all_records = MyModel.objects.all()
  access_controlled = all_records.accessible_by_user(user_object)

The ``access_controlled`` queryset will be filtered based on the groups
that ``user_object`` is a member of.


Unfiltering a filtered queryset
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To remove the access filtering from a filtered queryset, you can do this::

  unrestricted = access_controlled.unrestricted()


Automatic access control filtering
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you have the django-group-access middleware installed, all access controlled
models will have their querysets filtered for the currently logged in user
automatically.

See :ref:`install-middleware` for how to install the automatic filtering middleware.

.. _group-model-attributes:

Group model attributes
----------------------

``Members`` or ``user_set``
~~~~~~~~~~~~~~~~~~~~~~~~~~~

To use a model as a group model, it must have either a ``members`` attribute
as a ManyToManyField to ``django.contrib.auth.models.User`` or a reverse
relationship to users called ``user_set``.


``supergroup``
~~~~~~~~~~~~~~

**Optional**

Boolean field. If a group's ``supergroup`` attribute is ``True``, members of that
group can see all records no matter how the sharing is configured.


``auto_share_groups``
~~~~~~~~~~~~~~~~~~~~~

**Optional**

ManyToManyField to the group model. Records created with an owner of the group
will automatically be shared with the groups in this list.
