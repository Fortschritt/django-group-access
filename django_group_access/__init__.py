__all__ = ['register', ]

from django.db.models import query, manager
from django.db.models.fields import related

from django_group_access import registration
from django_group_access.models import AccessManagerMixin, QuerySetMixin

register = registration.register

"""
Django creates managers in a whole bunch of places, sometimes
defining the classs dynamically inside a closure, which makes
decorating every manager creation a tricky job. So we add a mixin
to the base Manager class so that we're guaranteed to have the
access control code available no matter which Manager we're using.
"""
# add access control methods to the base Manager class
if AccessManagerMixin not in manager.Manager.__bases__:
    manager.Manager.__bases__ += (AccessManagerMixin, )
# add access control methods to the base QuerySet class
if QuerySetMixin not in query.QuerySet.__bases__:
    query.QuerySet.__bases__ += (QuerySetMixin, )


def wrap_db_method(func):
    """
    When the queryset is going to go to the database, apply
    the access control filters.
    """
    def db_wrapper(self, *args, **kwargs):
        queryset = self._filter_for_access_control()
        return func(queryset, *args, **kwargs)
    return db_wrapper

query.QuerySet.get = wrap_db_method(query.QuerySet.get)
query.QuerySet.latest = wrap_db_method(query.QuerySet.latest)
query.QuerySet.aggregate = wrap_db_method(query.QuerySet.aggregate)
query.QuerySet.iterator = wrap_db_method(query.QuerySet.iterator)
query.QuerySet.count = wrap_db_method(query.QuerySet.count)
query.QuerySet.in_bulk = wrap_db_method(query.QuerySet.in_bulk)
query.QuerySet.__getitem__ = wrap_db_method(query.QuerySet.__getitem__)


def wrap_get_query_set(func):
    """
    Propagate metadata from model instances in the manager
    to the queryset and apply access controls where needed.
    """
    def get_query_set_wrapper(self, *args, **kwargs):
        queryset = func(self, *args, **kwargs)

        metadata = False
        if hasattr(self, 'instance'):
            # some related managers have the original instance, we can get
            # the metadata from the instance.
            metadata = getattr(self.instance, '_access_control_meta', False)
        else:
            # some are loaded with the metadata directly.
            metadata = getattr(self, '_access_control_meta', False)

        if metadata:
            queryset._access_control_meta = metadata
            queryset._access_control_filtered = True
        return queryset
    return get_query_set_wrapper


manager.Manager.get_query_set = wrap_get_query_set(
    manager.Manager.get_query_set)


def wrap_query_set_iterator(func):
    """
    Sits between the iterator and the loop, propagating the access
    control meta data.
    """
    def iterator_wrapper(self, *args, **kwargs):
        for obj in func(self, *args, **kwargs):
            if hasattr(self, '_access_control_meta'):
                obj._access_control_meta = self._access_control_meta
            yield obj
    return iterator_wrapper

query.QuerySet.iterator = wrap_query_set_iterator(query.QuerySet.iterator)


def wrap_query_set_clone(func):
    """
    If the access control meta data exists, make sure it
    gets cloned too.
    """
    def clone_queryset(self, *args, **kwargs):
        clone = func(self, *args, **kwargs)
        if hasattr(self, '_access_control_meta'):
            clone._access_control_meta = self._access_control_meta

        # if this queryset has been run through accessible_by_user, its clone
        # will have that filter too, so copy the flag over.
        if hasattr(self, '_access_control_filtering'):
            clone._access_control_filtering = self._access_control_filtering
        return clone
    return clone_queryset

query.QuerySet._clone = wrap_query_set_clone(query.QuerySet._clone)


def wrap_getitem(func):
    """
    Propagating access control metadata from querysets to models when
    a model is accessed as if the queryset were a list.
    """
    def getitem_wrapper(self, k):
        item = func(self, k)
        if hasattr(self, '_access_control_meta'):
            item._access_control_meta = self._access_control_meta
        return item
    return getitem_wrapper

query.QuerySet.__getitem__ = wrap_getitem(query.QuerySet.__getitem__)


def wrap_descriptor_get(func):
    """
    Getting a model or a manager from a related field descriptor
    will have the access control metadata propagated to it
    from the instance it is on.
    """
    def get_wrapper(self, instance, instance_type=None):
        obj = func(self, instance, instance_type)
        if hasattr(instance, '_access_control_meta'):
            obj._access_control_meta = instance._access_control_meta
        return obj
    return get_wrapper

related.ReverseSingleRelatedObjectDescriptor.__get__ = wrap_descriptor_get(
    related.ReverseSingleRelatedObjectDescriptor.__get__)
related.ManyRelatedObjectsDescriptor.__get__ = wrap_descriptor_get(
    related.ManyRelatedObjectsDescriptor.__get__)
related.ForeignRelatedObjectsDescriptor.__get__ = wrap_descriptor_get(
    related.ForeignRelatedObjectsDescriptor.__get__)
