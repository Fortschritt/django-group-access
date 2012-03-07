from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save

from django_group_access.models import (
    AccessGroup, AccessManager, process_auto_share_groups)


def register(model, control_relation=False):
    owner = models.ForeignKey(User, null=True, blank=True)
    owner.contribute_to_class(model, 'owner')
    access_groups = models.ManyToManyField(AccessGroup, blank=True, null=True)
    access_groups.contribute_to_class(model, 'access_groups')
    manager = AccessManager()
    manager.contribute_to_class(model, 'objects')
    if control_relation:
        model.access_relation = control_relation
    post_save.connect(process_auto_share_groups, model)
