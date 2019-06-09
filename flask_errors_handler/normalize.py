from werkzeug.routing import RequestRedirect
from werkzeug.exceptions import MethodNotAllowed


class BaseNormalize(object):
    def normalize(self, ex, **kwargs):
        """

        :param ex:
        :param kwargs:
        :return:
        """
        return ex


class RequestRedirectMixin(BaseNormalize):
    def normalize(self, ex, **kwargs):
        if isinstance(ex, RequestRedirect):
            location = dict(Location=ex.new_url)
            ex.headers = location
            ex.response = location

        return super().normalize(ex)


class MethodNotAllowedMixin(BaseNormalize):
    def normalize(self, ex, **kwargs):
        if isinstance(ex, MethodNotAllowed):
            ex.response = dict(Allow=ex.valid_methods)
            ex.headers = dict(Allow=", ".join(ex.valid_methods))

        return super().normalize(ex)


class DefaultNormalizeMixin(
    MethodNotAllowedMixin,
    RequestRedirectMixin
):
    def normalize(self, ex, **kwargs):
        return super().normalize(ex)
