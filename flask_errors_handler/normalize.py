from werkzeug.routing import RequestRedirect
from werkzeug.exceptions import MethodNotAllowed


class BaseNormalize(object):
    def normalize(self, ex, exc_class=None, **kwargs):
        """
        Child class must return super().normalize() so as to keep the chain of Mixins
        :param ex: input exception
        :param exc_class: class of output exception
        :return:
        """
        return ex


class RequestRedirectMixin(BaseNormalize):
    def normalize(self, ex, exc_class=None, **kwargs):
        """

        :param ex:
        :param exc_class:
        :param kwargs:
        :return:
        """
        if isinstance(ex, RequestRedirect):
            location = dict(Location=ex.new_url)
            ex.headers = location
            ex.response = location

        return super().normalize(ex, exc_class)


class MethodNotAllowedMixin(BaseNormalize):
    def normalize(self, ex, exc_class=None, **kwargs):
        """

        :param ex:
        :param exc_class:
        :param kwargs:
        :return:
        """
        if isinstance(ex, MethodNotAllowed):
            ex.response = dict(Allow=ex.valid_methods)
            ex.headers = dict(Allow=", ".join(ex.valid_methods))

        return super().normalize(ex, exc_class)


class DefaultNormalizeMixin(
    MethodNotAllowedMixin,
    RequestRedirectMixin
):
    def normalize(self, ex, exc_class=None, **kwargs):
        """
        Collects the default normalize Mixins used in ErrorHandler
        :param ex:
        :param exc_class:
        :param kwargs:
        :return:
        """
        return super().normalize(ex, exc_class)
