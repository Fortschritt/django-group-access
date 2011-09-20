from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save


class AccessManager(models.Manager):

    def get_for_owner(self, user):
        return self.filter(owner=user)

    def _get_accessible_by_user_filter_rules(self, user):
        """ Implements the access rules. Must return a
            queryset of available records. """
        if hasattr(self.model, 'access_relation'):
            acr = getattr(self.model, 'access_relation')
            k = '%s__access_groups__in' % acr
            access_groups_dict = {k: AccessGroup.objects.filter(members=user)}
            k = '%s__isnull' % acr
            no_related_records = {k: True}
            k = '%s__owner' % acr
            direct_owner_dict = {k: user}
            return (
                models.Q(**access_groups_dict) |
                models.Q(**direct_owner_dict) |
                models.Q(**no_related_records))
        else:
            user_groups = AccessGroup.objects.filter(members=user)
            return (models.Q(access_groups__in=user_groups) |
                    models.Q(owner=user))

    def accessible_by_user(self, user):
        if AccessGroup.objects.filter(members=user, supergroup=True).count():
            return self.all()
        rules = self._get_accessible_by_user_filter_rules(user)
        # Although this extra .filter() call seems redundant it turns out
        # to be a huge performance optimization.  Without it the ORM will
        # join on the related tables and .distinct() them, which killed
        # performance in HEXR leading to 30+ seconds to load a page.
        return self.filter(pk__in=self.filter(rules).distinct())


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


class AccessGroupMixin(models.Model):
    access_groups = models.ManyToManyField(AccessGroup, blank=True)

    class Meta:
        abstract = True


def process_invitations(user):
    for i in Invitation.objects.filter(lp_username=user.username):
        g = i.group
        g.members.add(user)
        g.save()
        i.delete()


def process_auto_share_groups(sender, instance, created, **kwargs):
    if created:
        try:
            owner = instance.owner
            if owner is None:
                return
            for g in owner.accessgroup_set.all():
                for sg in g.auto_share_groups.all():
                    instance.access_groups.add(sg)
        except User.DoesNotExist:
            pass


def process_invitations_for_user(sender, instance, created, **kwargs):
    if created:
        process_invitations(instance)


def populate_sharing(sender, instance, created, **kwargs):
    for g in AccessGroup.objects.all():
        if instance.can_be_shared_with:
            g.can_share_with.add(instance)
        elif instance in g.can_share_with.all():
            g.can_share_with.remove(instance)
    instance.can_share_with.add(instance)

post_save.connect(process_invitations_for_user, User)
post_save.connect(populate_sharing, AccessGroup)
