import traceback

from flask import current_app as cap
from werkzeug.routing import RequestRedirect
from werkzeug.exceptions import MethodNotAllowed, HTTPException


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
            try:
                ex.headers = dict(Allow=", ".join(ex.valid_methods))
                ex.response = dict(Allow=ex.valid_methods)
            except TypeError:
                pass

        return super().normalize(ex, exc_class)


class DefaultNormalizeMixin(
    MethodNotAllowedMixin,
    RequestRedirectMixin
):
    def normalize(self, ex, exc_class=None, **kwargs):
        """

        :param ex: Exception
        :param exc_class: overrides ApiProblem class
        :return: new Exception instance of HTTPException
        """
        # noinspection PyPep8Naming
        ExceptionClass = exc_class
        ex = super().normalize(ex, exc_class)

        if isinstance(ex, ExceptionClass):
            return ex

        tb = traceback.format_exc()
        if cap.config['DEBUG']:
            mess = tb
        else:
            mess = cap.config['ERROR_DEFAULT_MSG']

        _ex = ExceptionClass(mess, **kwargs)

        if isinstance(ex, HTTPException):
            _ex.code = ex.code
            _ex.description = ex.description
            _ex.response = ex.response if hasattr(ex, 'response') else None
            _ex.headers.update(**(ex.headers if hasattr(ex, 'headers') else {}))
        else:
            cap.logger.error(tb)

        return _ex
