# Copyright 2012 Canonical Ltd.
from django import forms
from django.db import models
from django_group_access import register


class AccessRestrictedParent(models.Model):
    name = models.CharField(max_length=64)

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return self.name


class AccessRestrictedModel(models.Model):
    name = models.CharField(max_length=64)
    parent = models.ForeignKey(AccessRestrictedParent, null=True)

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return self.name


class Machine(models.Model):
    name = models.CharField(max_length=64)

    def __unicode__(self):
        return self.name


class Unrestricted(models.Model):
    name = models.CharField(max_length=64)

    def __unicode__(self):
        return self.name


class Project(models.Model):
    name = models.CharField(max_length=64)
    machines = models.ManyToManyField(Machine)
    unrestricted = models.ForeignKey(Unrestricted, null=True)

    def __unicode__(self):
        return self.name


class Build(models.Model):
    name = models.CharField(max_length=64)
    project = models.ForeignKey(Project)

    def __unicode__(self):
        return self.name


class Release(models.Model):
    name = models.CharField(max_length=64)
    build = models.ForeignKey(Build)

    def __unicode__(self):
        return self.name


class UniqueModel(models.Model):
    name = models.CharField(max_length=64, unique=True)

    def __unicode__(self):
        return self.name


class UniqueForm(forms.ModelForm):

    class Meta:
        model = UniqueModel


def username_is_mike(user):
    return user.username == 'mike'


# allows us to test that the additional superuser checks are called
register(AccessRestrictedModel, unrestricted_access_hooks=[username_is_mike])
register(
    AccessRestrictedParent, control_relation='accessrestrictedmodel',
    owner=False)
register(Project, unrestricted_manager='objects_unrestricted')
register(Build, control_relation='project', auto_filter=False)

# We don't have a direct reference to the parent which is
# accessgroup-controlled, so we have to go via Build.
register(Release, control_relation='build__project')

# a project can have many machines, a machine can be in many projects,
# so this is here to test the ManyToMany related records filtering
register(Machine)

# to test unique constraints when using ModelForms and ownerless records
register(UniqueModel, owner=False)
