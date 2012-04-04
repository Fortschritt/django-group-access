# Copyright 2012 Canonical Ltd.
from django.db.models import ForeignKey, ManyToManyField, manager
from django.contrib.auth.models import User
from django.db.models.signals import post_save

_registered_models = set([])
_auto_filter_models = set([])


def is_registered_model(model):
    return model in _registered_models


def is_auto_filtered(model):
    return model in _auto_filter_models


def register(
    model, control_relation=False, unrestricted_manager=False,
    auto_filter=True, owner=True):
    """
    Register a model with the access control code.
    """
    from django_group_access.models import (
        AccessGroup, process_auto_share_groups)

    if is_registered_model(model):
        return
    _registered_models.add(model)

    if auto_filter:
        _auto_filter_models.add(model)

    reverse = '%s_owner' % str(model).split("'")[1].split('.')[-1].lower()

    if owner:
        ForeignKey(
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
    ManyToManyField(
        AccessGroup, blank=True, null=True).contribute_to_class(
            model, 'access_groups')
    post_save.connect(process_auto_share_groups, model)
