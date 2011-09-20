import itertools

from django.test import TestCase
from django.conf import settings
from django.core.management import call_command
from django.db.models import loading
from django.contrib.auth.models import User
from django_group_access.sandbox.models import (
    AccessRestrictedModel,
    AccessRestrictedParent,
    Build,
    Project,
    Release,
)
from django_group_access.models import AccessGroup, Invitation


class SyncingTestCase(TestCase):
    apps = ('django_group_access.sandbox',)

    def _pre_setup(self):
        # Add the models to the db.
        self._original_installed_apps = list(settings.INSTALLED_APPS)
        for app in self.apps:
            settings.INSTALLED_APPS.append(app)
        loading.cache.loaded = False
        call_command('syncdb', interactive=False, verbosity=0, migrate=False)
        # Call the original method that does the fixtures etc.
        super(SyncingTestCase, self)._pre_setup()

    def _post_teardown(self):
        # Call the original method.
        super(SyncingTestCase, self)._post_teardown()
        # Restore the settings.
        settings.INSTALLED_APPS = self._original_installed_apps
        loading.cache.loaded = False


class AccessRelationTests(SyncingTestCase):

    def setUp(self):
        super(AccessRelationTests, self).setUp()
        self.owner = _create_user()
        self.project = Project(owner=self.owner, name='project')
        self.project.save()
        self.build = Build(
            owner=self.owner, name='build', project=self.project)
        self.build.save()
        self.release = Release(
            owner=self.owner, name='release', build=self.build)
        self.release.save()
        group = self._create_access_group_with_one_member()
        self.project.access_groups.add(group)
        self.project.save()
        self.user_with_access = group.members.all()[0]
        self.user_without_access = _create_user()

    def _create_access_group_with_one_member(self):
        g = AccessGroup(name='oem')
        g.save()
        g.members.add(_create_user())
        g.save()
        return g

    def test_direct_reference(self):
        # Build has a foreign key to Project so its access_relation just need
        # to point to project and we'll take advantage of Django's ORM to do
        # the access group checks on Project.
        query_method = Build.objects.accessible_by_user

        self.assertEqual('project', Build.access_relation)
        self.assertEqual(
            [self.build.name], [b.name for b in query_method(self.owner)])
        self.assertEqual(
            [self.build.name],
            [b.name for b in query_method(self.user_with_access)])
        self.assertEqual(
            [], [b for b in query_method(self.user_without_access)])

    def test_indirect_reference(self):
        # Release has no foreign key to Project, but it has one to Build
        # and it can use that to tell us to do the access group checks on
        # Project.
        query_method = Release.objects.accessible_by_user

        self.assertEqual('build__project', Release.access_relation)
        self.assertEqual(
            [self.release.name], [r.name for r in query_method(self.owner)])
        self.assertEqual(
            [self.release.name],
            [r.name for r in query_method(self.user_with_access)])
        self.assertEqual(
            [], [r for r in query_method(self.user_without_access)])



class InvitationTest(TestCase):

    def setUp(self):
        g = AccessGroup(name='oem')
        g.save()
        i = Invitation(lp_username='tomservo', group=g)
        i.save()

    def test_add_to_group_on_user_creation(self):
        """ If there is an invitation for a user, when that user is
            created they should be added to the access group they
            were invited to. """

        u = User.objects.create_user(
            'tomservo', 'tomservo@example.com', 'test')
        self.assertTrue(u in AccessGroup.objects.get(name='oem').members.all())

    def test_invitation_deleted_after_processing(self):
        self.assertEqual(Invitation.objects.all().count(), 1)
        User.objects.create_user(
            'tomservo', 'tomservo@example.com', 'test')
        self.assertEqual(Invitation.objects.all().count(), 0)


class AccessGroupSharingTest(TestCase):

    def test_can_be_shared_group_is_added_to_other_sharing_lists(self):
        AccessGroup.objects.all().delete()
        group_a = AccessGroup(name='A', can_be_shared_with=False)
        group_a.save()
        group_b = AccessGroup(name='B', can_be_shared_with=False)
        group_b.save()

        self.assertEqual(str(group_a.can_share_with.all()), str([group_a]))
        self.assertEqual(str(group_b.can_share_with.all()), str([group_b]))

        group_a.can_be_shared_with = True
        group_a.save()

        self.assertEqual(str(group_a.can_share_with.all()), str([group_a]))
        self.assertEqual(
            str(group_b.can_share_with.all()), str([group_a, group_b]))

        group_a.can_be_shared_with = False
        group_a.save()

        self.assertEqual(str(group_a.can_share_with.all()), str([group_a]))
        self.assertEqual(str(group_b.can_share_with.all()), str([group_b]))


class AccessTest(SyncingTestCase):
    everyone = None
    public_group = None
    restricted_group_a = None
    restricted_group_b = None
    supergroup = None

    def _load_users(self, prefix, group):
        for i in range(3):
            u = User.objects.create_user(
                '%s%d' % (prefix, i), '%s%d@example.com' % (prefix, i), prefix)
            group.members.add(u)
            self.everyone.members.add(u)

    def _load_owned_models(self, group):
        users = group.members.all().order_by('username')

        # parent class for these resources
        p = AccessRestrictedParent(name='%s parent record' % group.name)
        p.save()

        # one model per user, two for the first user
        for (idx, u) in enumerate(users):
            m = AccessRestrictedModel(
                owner=u, name='%s record %d' % (group.name, idx), parent=p)
            m.save()

        u = users[0]
        m = AccessRestrictedModel(
            owner=u, name='%s record extra' % group.name, parent=p)
        m.save()

    def setUp(self):
        self.everyone = AccessGroup.objects.get_or_create(name='everyone')[0]

        self.public_group = AccessGroup(name='public')
        self.public_group.save()
        self.public_group.auto_share_groups.add(self.everyone)
        self.public_group.auto_share_groups.add(self.public_group)

        self.restricted_group_a = AccessGroup(name='the cabal')
        self.restricted_group_a.save()
        self.restricted_group_a.auto_share_groups.add(self.restricted_group_a)

        self.restricted_group_b = AccessGroup(name='the stonecutters')
        self.restricted_group_b.save()
        self.restricted_group_b.auto_share_groups.add(self.restricted_group_b)

        self.supergroup = AccessGroup(name='supergroup', supergroup=True)
        self.supergroup.save()

        self._load_users('public', self.public_group)
        self._load_users('cabal', self.restricted_group_a)
        self._load_users('stonecutter', self.restricted_group_b)

        self._load_owned_models(self.public_group)
        self._load_owned_models(self.restricted_group_a)
        self._load_owned_models(self.restricted_group_b)

        su = User.objects.create_user(
            'supergroupuser', 'supergroup@example.com', 'test')
        self.supergroup.members.add(su)

        User.objects.create_user('nogroupuser', 'nogroup@example.com', 'test')

    def test_get_own_resources(self):
        u = self.restricted_group_a.members.all().order_by('username')[0]
        mine = AccessRestrictedModel.objects.get_for_owner(u)
        self.assertEqual(mine.count(), 2)
        self.assertEqual(mine[0].name, 'the cabal record 0')
        self.assertEqual(mine[1].name, 'the cabal record extra')

    def test_accessible_by_user(self):
        u = self.restricted_group_a.members.all().order_by('username')[0]

        # should return all of the records owned by someone in the user's group
        # plus all records owned by anyone in a group marked as public
        available = AccessRestrictedModel.objects.accessible_by_user(user=u)
        self.assertEqual(available.count(), 8)
        self.assertEqual(available[0].name, 'public record 0')
        self.assertEqual(available[1].name, 'public record 1')
        self.assertEqual(available[2].name, 'public record 2')
        self.assertEqual(available[3].name, 'public record extra')
        self.assertEqual(available[4].name, 'the cabal record 0')
        self.assertEqual(available[5].name, 'the cabal record 1')
        self.assertEqual(available[6].name, 'the cabal record 2')
        self.assertEqual(available[7].name, 'the cabal record extra')

        record = AccessRestrictedModel.objects.accessible_by_user(u)\
                .get(name='public record 2')
        self.assertTrue(record.name, 'public record 2')

        try:
            record = AccessRestrictedModel.objects.accessible_by_user(u)\
                    .get(name='the stonecutters record 1')
            self.fail(
                "Shouldn't be able to access other non public group record")
        except AccessRestrictedModel.DoesNotExist:
            pass

    def test_accessible_parent_records(self):
        u = self.restricted_group_a.members.all().order_by('username')[0]
        parents = AccessRestrictedParent.objects.accessible_by_user(u)
        self.assertEqual(parents.count(), 2)
        self.assertEqual(parents[0].name, 'public parent record')
        self.assertEqual(parents[1].name, 'the cabal parent record')

    def test_members_of_supergroup_can_see_all_records(self):
        u = self.supergroup.members.all()[0]
        available = AccessRestrictedModel.objects.accessible_by_user(user=u)
        self.assertEqual(available.count(), 12)
        self.assertEqual(available[0].name, 'public record 0')
        self.assertEqual(available[1].name, 'public record 1')
        self.assertEqual(available[2].name, 'public record 2')
        self.assertEqual(available[3].name, 'public record extra')
        self.assertEqual(available[4].name, 'the cabal record 0')
        self.assertEqual(available[5].name, 'the cabal record 1')
        self.assertEqual(available[6].name, 'the cabal record 2')
        self.assertEqual(available[7].name, 'the cabal record extra')
        self.assertEqual(available[8].name, 'the stonecutters record 0')
        self.assertEqual(available[9].name, 'the stonecutters record 1')
        self.assertEqual(available[10].name, 'the stonecutters record 2')
        self.assertEqual(available[11].name, 'the stonecutters record extra')

        available = AccessRestrictedParent.objects.accessible_by_user(user=u)
        self.assertEqual(available.count(), 3)
        self.assertEqual(available[0].name, 'public parent record')
        self.assertEqual(available[1].name, 'the cabal parent record')
        self.assertEqual(available[2].name, 'the stonecutters parent record')

    def test_can_access_owned_records_if_not_in_a_group(self):
        u = User.objects.create_user(
            'groupless', 'groupless@example.com', 'nogroup')
        m = AccessRestrictedModel(name='a record', owner=u)
        m.save()

        r = AccessRestrictedModel.objects.accessible_by_user(u).get(pk=m.id)
        self.assertEqual(m, r)

    def test_can_see_individual_records_shared_with_my_group(self):
        record = AccessRestrictedModel.objects.get(
                    name='the stonecutters record 1')
        g = AccessGroup.objects.get(name='the cabal')
        record.access_groups.add(g)
        record.save()
        u = g.members.all()[0]
        available = AccessRestrictedModel.objects.accessible_by_user(u)
        self.assertEqual(available.count(), 9)
        self.assertEqual(available[0].name, 'public record 0')
        self.assertEqual(available[1].name, 'public record 1')
        self.assertEqual(available[2].name, 'public record 2')
        self.assertEqual(available[3].name, 'public record extra')
        self.assertEqual(available[4].name, 'the cabal record 0')
        self.assertEqual(available[5].name, 'the cabal record 1')
        self.assertEqual(available[6].name, 'the cabal record 2')
        self.assertEqual(available[7].name, 'the cabal record extra')
        self.assertEqual(available[8].name, 'the stonecutters record 1')


counter = itertools.count()
def _create_user():
    random_string = 'asdfg%d' % counter.next()
    user = User.objects.create_user(
        random_string, '%s@example.com' % random_string)
    return user
