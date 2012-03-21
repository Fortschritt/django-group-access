# Copyright 2012 Canonical Ltd.
from django.contrib import admin
from django_group_access.models import AccessGroup


class GroupAdmin(admin.ModelAdmin):
    filter_horizontal = ('members',)

admin.site.register(AccessGroup, GroupAdmin)
