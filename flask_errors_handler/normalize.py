import traceback

from flask import current_app as cap
from werkzeug.exceptions import HTTPException, MethodNotAllowed
from werkzeug.routing import RequestRedirect

from .exception import ApiProblem


class BaseNormalize(object):
    def normalize(self, ex, **kwargs):
        """
        Child class must return super().normalize() so as to keep the chain of Mixins

        :param ex: input exception
        :return:
        """
        return ex


class RequestRedirectMixin(BaseNormalize):
    def normalize(self, ex, **kwargs):
        """

        :param ex:
        :return:
        """
        if isinstance(ex, RequestRedirect):
            location = dict(Location=ex.new_url)
            ex.headers = location
            ex.response = location

        return super().normalize(ex)


class MethodNotAllowedMixin(BaseNormalize):
    def normalize(self, ex, **kwargs):
        """

        :param ex:
        :return:
        """
        if isinstance(ex, MethodNotAllowed):
            try:
                ex.headers = dict(Allow=", ".join(ex.valid_methods))
                ex.response = dict(Allow=ex.valid_methods)
            except TypeError:
                pass

        return super().normalize(ex)


class DefaultNormalizeMixin(MethodNotAllowedMixin, RequestRedirectMixin):
    def normalize(self, ex, exc_class=ApiProblem, **kwargs):
        """

        :param ex: Exception
        :param exc_class: overrides ApiProblem class
        :return: new Exception instance of HTTPException
        """
        ex = super().normalize(ex)

        if isinstance(ex, exc_class):
            return ex

        tb = traceback.format_exc()
        if cap.config['DEBUG']:
            mess = tb
        else:
            mess = cap.config['ERROR_DEFAULT_MSG']

        _ex = exc_class(mess, **kwargs)

        if isinstance(ex, HTTPException):
            _ex.code = ex.code
            _ex.description = ex.description
            _ex.response = ex.response if hasattr(ex, 'response') else None
            _ex.headers.update(**(ex.headers if hasattr(ex, 'headers') else {}))
        else:
            cap.logger.error(tb)

        return _ex
