# Copyright 2012 Canonical Ltd.
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models.signals import post_save

from django_group_access import middleware, registration


class AccessManagerMixin:
    """
    Provides access control methods for the Manager class.
    """
    def get_for_owner(self, user):
        return self.get_query_set().get_for_owner(user)

    def accessible_by_user(self, user):
        return self.get_query_set().accessible_by_user(user)


class QuerySetMixin:
    """
    Access control functions for the base QuerySet class.
    """
    def unrestricted(self):
        """
        Returns a new queryset with the access control meta data
        set to an unrestricted state.
        """
        queryset = self._clone()
        access_control_meta = getattr(
            queryset, '_access_control_meta', {}).copy()
        access_control_meta['user'] = None
        access_control_meta['unrestricted'] = True
        queryset._access_control_meta = access_control_meta
        return queryset

    def get_for_owner(self, user):
        return self.filter(owner=user)

    def _get_accessible_by_user_filter_rules(self, user):
        """
        Implements the access rules. Must return a set of Q conditions
        matching available records. If we get here and the user is not
        authenticated, DGA_UNSHARED_RECORDS_ARE_PUBLIC must be True.
        """
        if user.is_authenticated():

            if user.is_superuser:
                return models.Q()

            if AccessGroup.objects.filter(
                members=user, supergroup=True).count():
                return models.Q()

        if hasattr(self.model, 'access_control_relation'):
            # access control is managed by a related record
            access_relation = getattr(self.model, 'access_control_relation')
            rules = models.Q()
            if user.is_authenticated():
                if hasattr(self.model, 'owner'):
                    # direct owner
                    rules = rules | models.Q(
                        **{'%s__owner' % access_relation: user})
                # in access groups the user is in
                rules = rules | models.Q(
                    **{'%s__access_groups__in' % access_relation:
                        AccessGroup.objects.filter(members=user)})
                # or owned by user
                rules = rules | models.Q(
                    **{'%s__owner' % access_relation: user})
            # related records do not exist
            rules = rules | models.Q(
                **{'%s__isnull' % access_relation: True})
            # or related records not shared, and public mode is on
            if getattr(settings, 'DGA_UNSHARED_RECORDS_ARE_PUBLIC', False):
                rules = rules | models.Q(
                    **{'%s__access_groups__isnull' % access_relation: True})

            return rules
        else:
            # access controls are directly on the record
            if user.is_authenticated():
                user_groups = AccessGroup.objects.filter(members=user)
                # either the record is in the user's access groups, or
                # directly owned by the user
                rules = models.Q(access_groups__in=user_groups)
                if hasattr(self.model, 'owner'):
                    rules = rules | models.Q(owner=user)
                if getattr(settings, 'DGA_UNSHARED_RECORDS_ARE_PUBLIC', False):
                    rules = rules | models.Q(access_groups__isnull=True)
                return rules
            else:
                # records that are not in any access group
                return models.Q(access_groups__isnull=True)

    def _filter_for_access_control(self):
        """
        Returns a queryset filtered for the records the user stored
        in the access control metadata can access.
        """
        if not registration.is_registered_model(self.model):
            return self

        if getattr(self, '_access_control_filtering', False):
            return self

        user = None
        if hasattr(self, '_access_control_meta'):
            user = self._access_control_meta['user']
        elif registration.is_auto_filtered(self.model):
            user = middleware.get_access_control_user()

        if user is not None:
            unshared_are_public = getattr(
                settings, 'DGA_UNSHARED_RECORDS_ARE_PUBLIC', False)
            if not user.is_authenticated() and not unshared_are_public:
                return self.model.objects.none()
            # this stops any further filtering while the filtering rules
            # are applied
            self._access_control_filtering = True
            rules = self._get_accessible_by_user_filter_rules(user)
            # Although this extra .filter() call seems redundant it turns
            # out to be a huge performance optimization.  Without it the
            # ORM will join on the related tables and .distinct() them,
            # which can kill performance on larger queries.
            filtered_queryset = self.filter(
                pk__in=self.filter(rules).distinct())
            self._access_control_filtering = False
            return filtered_queryset

        return self

    def accessible_by_user(self, user):
        """
        Sets up metadata so the queryset will be access controlled when run.
        """
        self._access_control_meta = {'user': user,
                                     'unrestricted': False}
        return self


class AccessGroup(models.Model):
    name = models.CharField(max_length=64, unique=True)
    members = models.ManyToManyField(User, blank=True)
    supergroup = models.BooleanField(default=False)
    can_be_shared_with = models.BooleanField(default=True)
    can_share_with = models.ManyToManyField('self',
        blank=True, symmetrical=False)
    # list of groups to automatically share data with
    auto_share_groups = models.ManyToManyField('self', blank=True)

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return self.name


def process_auto_share_groups(sender, instance, created, **kwargs):
    """
    Automatically shares a record with the auto_share_groups
    on the groups the owner is a member of.
    """
    if created and hasattr(instance, 'owner'):
        try:
            owner = instance.owner
            if owner is None:
                return
            for group in owner.accessgroup_set.all():
                for share_group in group.auto_share_groups.all():
                    instance.access_groups.add(share_group)
        except User.DoesNotExist:
            pass


def populate_sharing(sender, instance, created, **kwargs):
    """
    When new groups are created, if they can be shared with
    they are added to the 'can_share_with' property of the
    other groups.
    """
    for group in AccessGroup.objects.all():
        if instance.can_be_shared_with:
            group.can_share_with.add(instance)
        elif instance in group.can_share_with.all():
            group.can_share_with.remove(instance)
    instance.can_share_with.add(instance)


post_save.connect(populate_sharing, AccessGroup)
