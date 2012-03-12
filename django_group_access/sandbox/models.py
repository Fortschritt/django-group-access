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


register(AccessRestrictedModel)
register(AccessRestrictedParent, control_relation='accessrestrictedmodel')
register(Project)
register(Build, control_relation='project')
# We don't have a direct reference to the parent which is
# accessgroup-controlled, so we have to go via Build.
register(Release, control_relation='build__project')
# a project can have many machines, a machine can be in many projects,
# so this is here to test the ManyToMany related records filtering
register(Machine)
