# Copyright 2012 Canonical Ltd.
from django.db.models import manager
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.db.models.fields import FieldDoesNotExist

_registered_models = set([])
_auto_filter_models = set([])
_unrestricted_access_hooks = {}


def _is_superuser(user):
    return user.is_superuser


def _get_registered_model_for_model(model):
    if model in _registered_models:
        return model
    if model._meta.proxy and model._meta.proxy_for_model in _registered_models:
        return model._meta.concrete_model


def get_unrestricted_access_hooks(model):
    return _unrestricted_access_hooks[_get_registered_model_for_model(model)]


def is_registered_model(model):
    return _get_registered_model_for_model(model) in _registered_models


def is_auto_filtered(model):
    return _get_registered_model_for_model(model) in _auto_filter_models


def register_proxy(proxy_model):
    try:
        owner = proxy_model._meta.proxy_for_model._meta.get_field('owner')
        if owner:
            owner.contribute_to_class(proxy_model, 'owner')
    except FieldDoesNotExist:
        pass


def register(
    model, control_relation=False, unrestricted_manager=False,
    auto_filter=True, owner=True, unrestricted_access_hooks=[]):
    """
    Register a model with the access control code.
    """
    from django_group_access.models import (
        get_group_model, process_auto_share_groups, DjangoGroupAccessForeignKey, DjangoGroupAccessManyToManyField)

    if is_registered_model(model):
        return
    _registered_models.add(model)

    _unrestricted_access_hooks[model] = [_is_superuser] + unrestricted_access_hooks

    if auto_filter:
        _auto_filter_models.add(model)

    reverse = '%s_owner' % str(model).split("'")[1].split('.')[-1].lower()

    if owner:
        DjangoGroupAccessForeignKey(
            User, null=True, blank=True,
            related_name=reverse).contribute_to_class(
                model, 'owner')

    if unrestricted_manager:
        un_manager = manager.Manager()
        un_manager._access_control_meta = {'user': None, 'unrestricted': True}
        un_manager.contribute_to_class(model, unrestricted_manager)

    if control_relation:
        model.access_control_relation = control_relation
        # access groups are inferred from which access groups
        # have access to the related records, so no need to
        # add the attribute to the class.
        return
    DjangoGroupAccessManyToManyField(
        get_group_model(), blank=True, null=True).contribute_to_class(
            model, 'access_groups')
    post_save.connect(process_auto_share_groups, model)
