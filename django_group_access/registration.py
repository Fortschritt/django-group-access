from django.db.models import ForeignKey, ManyToManyField
from django.contrib.auth.models import User
from django.db.models.signals import post_save

from django_group_access.models import (
    AccessGroup, process_auto_share_groups)

registered_models = []


def register(model, control_relation=False):
    """
    Register a model with the access control code.
    """
    if model in registered_models:
        return
    registered_models.append(model)
    ForeignKey(
        User, null=True, blank=True).contribute_to_class(model, 'owner')

    if control_relation:
        model.access_relation = control_relation
        # access groups are inferred from which access groups
        # have access to the related records, so no need to
        # add the attribute to the class.
        return
    ManyToManyField(
        AccessGroup, blank=True, null=True).contribute_to_class(
            model, 'access_groups')
    post_save.connect(process_auto_share_groups, model)
