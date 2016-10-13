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
            query.QuerySet.__bases__ += (QuerySetMixin, )
