from django.apps import AppConfig

from django.db.models import query, manager

class DjangoGroupAccessConfig(AppConfig):
    name = "django_group_access"

    def ready(self):

        from django_group_access.models import AccessManagerMixin, QuerySetMixin
        """
        Django creates managers in a whole bunch of places, sometimes
        defining the class dynamically inside a closure, which makes
        decorating every manager creation a tricky job. So we add a mixin
        to the base Manager class so that we're guaranteed to have the
        access control code available no matter which Manager we're using.
        """
        # add access control methods to the base Manager class
        if AccessManagerMixin not in manager.Manager.__bases__:
            manager.Manager.__bases__ += (AccessManagerMixin, )
        # add access control methods to the base QuerySet class
        if QuerySetMixin not in query.QuerySet.__bases__:
            """
            With Python3, this old hack gets even hackier:
            the old-style classes trick from above doesn't work anymore if QuerySet inherits only from object(), because mro changed.
            Changing the order of __bases__ would probably work, but triggers an issue that has been open since A.D. 2003...
            ("TypeError: __bases__ assignment: 'QuerySetMixin' deallocator differs from 'object'")
            To keep this module running without changes in code relying on this, we manually assign the methods the mixin wants to add.
            This change essentially makes this module python3 only, in python2 you could access the unbound functions by appending
            ".__func__" to each QuerySetMixin method name (so QuerySetMixin.unrestricted.__func__ instead of QuerySetMixin.unrestricted)

            Long term, switch to something like django guardian.
            """
            query.QuerySet.unrestricted = QuerySetMixin.unrestricted
            query.QuerySet.get_for_owner = QuerySetMixin.get_for_owner
            query.QuerySet._resolve_model_from_relation = QuerySetMixin._resolve_model_from_relation
            query.QuerySet._get_control_relation_model = QuerySetMixin._get_control_relation_model
            query.QuerySet._get_accessible_by_user_filter_rules = QuerySetMixin._get_accessible_by_user_filter_rules
            query.QuerySet.accessible_by_user = QuerySetMixin.accessible_by_user
            query.QuerySet._filter_for_access_control = QuerySetMixin._filter_for_access_control
