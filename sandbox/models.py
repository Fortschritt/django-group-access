from django.db import models
from django_group_access.models import (
    AccessManager,
    AccessGroupMixin,
    process_auto_share_groups
)
from django.contrib.auth.models import User
from django.db.models.signals import post_save

class AccessRestrictedParent(models.Model):
    name = models.CharField(max_length = 64)
    access_relation = 'accessrestrictedmodel'
    
    objects = AccessManager()
    
    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return self.name


class AccessRestrictedModel(AccessGroupMixin):
    owner = models.ForeignKey(User, null=True)
    name = models.CharField(max_length = 64)
    parent = models.ForeignKey(AccessRestrictedParent, null=True)

    objects = AccessManager()

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return self.name


class Project(AccessGroupMixin):
    owner = models.ForeignKey(User, null=True)
    name = models.CharField(max_length = 64)
    objects = AccessManager()

    def __unicode__(self):
        return self.name


class Build(AccessGroupMixin):
    owner = models.ForeignKey(User, null=True)
    name = models.CharField(max_length = 64)
    project = models.ForeignKey(Project)
    access_relation = 'project'
    objects = AccessManager()

    def __unicode__(self):
        return self.name


class Release(models.Model):
    owner = models.ForeignKey(User, null=True)
    name = models.CharField(max_length = 64)
    build = models.ForeignKey(Build)
    # We don't have a direct reference to the parent which is
    # accessgroup-controlled, so we have to go via Build.
    access_relation = 'build__project'
    objects = AccessManager()

    def __unicode__(self):
        return self.name


post_save.connect(process_auto_share_groups, AccessRestrictedModel)
