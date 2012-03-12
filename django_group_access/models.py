from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save


class AccessManagerMixin:
    """
    Provides access control methods for the Manager class.
    """

    def get_for_owner(self, user):
        return self.filter(owner=user)

    def _get_accessible_by_user_filter_rules(self, user):
        """
        Implements the access rules. Must return a queryset
        of available records.
        """
        if hasattr(self.model, 'access_relation'):
            access_relation = getattr(self.model, 'access_relation')
            lookup_key = '%s__access_groups__in' % access_relation
            access_groups_dict = {
                lookup_key: AccessGroup.objects.filter(members=user)}
            lookup_key = '%s__isnull' % access_relation
            no_related_records = {lookup_key: True}
            lookup_key = '%s__owner' % access_relation
            direct_owner_dict = {lookup_key: user}
            return (
                models.Q(**access_groups_dict) |
                models.Q(**direct_owner_dict) |
                models.Q(**no_related_records))
        else:
            user_groups = AccessGroup.objects.filter(members=user)
            return (models.Q(access_groups__in=user_groups) |
                    models.Q(owner=user))

    def accessible_by_user(self, user):
        """
        Returns a queryset filtered by the records available to the user.
        """
        if AccessGroup.objects.filter(members=user, supergroup=True).count():
            return self.all()

        rules = self._get_accessible_by_user_filter_rules(user)

        # This stops the filtering happening over and over and over and...
        self._access_control_filter_processing = True

        # Although this extra .filter() call seems redundant it turns out
        # to be a huge performance optimization.  Without it the ORM will
        # join on the related tables and .distinct() them, which can kill
        # performance on larger queries.
        filtered_queryset = self.filter(pk__in=self.filter(rules).distinct())

        self._access_control_filter_processing = False

        # now load the filtered_queryset with the access_control metadata
        filtered_queryset._access_control_meta = {'user': user}
        filtered_queryset._access_control_filtered = True
        return filtered_queryset


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


class Invitation(models.Model):
    lp_username = models.CharField(max_length=64)
    group = models.ForeignKey(AccessGroup)

    class Meta:
        ordering = ('lp_username',)

    def __unicode__(self):
        return u'%s to %s' % (self.lp_username, self.group)


def process_invitations(user):
    """
    Processes invitations for users and adds them to
    the group they've been invited to.
    """
    for invitation in Invitation.objects.filter(lp_username=user.username):
        group = invitation.group
        group.members.add(user)
        group.save()
        invitation.delete()


def process_auto_share_groups(sender, instance, created, **kwargs):
    """
    Automatically shares a record with the auto_share_groups
    on the groups the owner is a member of.
    """
    if created:
        try:
            owner = instance.owner
            if owner is None:
                return
            for group in owner.accessgroup_set.all():
                for share_group in group.auto_share_groups.all():
                    instance.access_groups.add(share_group)
        except User.DoesNotExist:
            pass


def process_invitations_for_user(sender, instance, created, **kwargs):
    if created:
        process_invitations(instance)


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

post_save.connect(process_invitations_for_user, User)
post_save.connect(populate_sharing, AccessGroup)
