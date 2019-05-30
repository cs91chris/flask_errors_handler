import traceback
from functools import wraps

from flask import json
from flask import request
from flask import Response
from flask import render_template

from werkzeug.exceptions import HTTPException
from werkzeug.exceptions import default_exceptions
from werkzeug.exceptions import InternalServerError

from .dispatchers import ErrorDispatcher


def default_response_builder(f):
    """

    :param f: function that returns dict or Response object and status code
    :return: flask response  of decorated function
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        r, s = f(*args, **kwargs)
        m = 'application/problem+json'
        return Response(json.dumps(r), status=s, mimetype=m)
    return wrapper


class ErrorHandler:
    def __init__(self, app=None, response=None):
        """

        :param app:
        :param response: decorator
        """
        self._app = None
        self._response = None

        if app is not None:
            self.init_app(app, response)

    def init_app(self, app, response=None):
        """

        :param app:
        :param response: decorator
        """
        self._app = app
        self._response = response or default_response_builder
        self._app.config.setdefault('ERROR_PAGE', None)
        self._app.config.setdefault('ERROR_XHR_ENABLED', True)
        self._app.config.setdefault('ERROR_DEFAULT_MSG', 'Unhandled Exception')

        if not hasattr(app, 'extensions'):
            app.extensions = dict()
        app.extensions['errors_handler'] = self

    @staticmethod
    def register(bp):
        """

        :param bp: blueprint or flask app
        """
        def _register(hderr):
            """

            :param hderr: function that takes only an Exception object as argument
            """
            @wraps(hderr)
            def wrapper():
                for code in default_exceptions.keys():
                    bp.errorhandler(code)(hderr)

                bp.register_error_handler(Exception, hderr)

            return wrapper()
        return _register

    def normalize(self, ex, exc_class=None, **kwargs):
        """

        :param ex: Exception
        :param exc_class: custom Exception class
        :return: new Exception instance of HTTPException
        """
        if not isinstance(ex, HTTPException):
            # noinspection PyPep8Naming
            ExceptionClass = exc_class or InternalServerError
            self._app.logger.error(traceback.format_exc())
            ex = ExceptionClass(
                ex if self._app.config['DEBUG']
                else self._app.config['ERROR_DEFAULT_MSG'],
                **kwargs
            )
        return ex

    def _api_handler(self, ex):
        """

        :param ex: Exception
        :return:
        """
        ex = self.normalize(ex)
        _type = ex.type if hasattr(ex, 'type') else 'about:blank'
        _instance = ex.instance if hasattr(ex, 'instance') else 'about:blank'

        @self._response
        def _response():
            return dict(
                type=_type,
                title=ex.name,
                detail=ex.description,
                status=ex.code,
                instance=_instance,
                data=ex.response
            ), ex.code

        return _response()

    def _web_handler(self, ex):
        """

        :param ex: Exception
        :return:
        """
        ex = self.normalize(ex)

        if self._app.config['ERROR_XHR_ENABLED'] is True:
            if request.is_xhr:
                return self._api_handler(ex)

        if self._app.config['ERROR_PAGE'] is not None:
            return render_template(
                self._app.config['ERROR_PAGE'],
                error=ex
            ), ex.code

        return str(ex) if self._app.config['DEBUG'] \
            else self._app.config['ERROR_DEFAULT_MSG'], 500

    # noinspection PyMethodMayBeStatic
    def default_register(self, bp):
        """

        :param bp:
        """
        ErrorHandler.register(bp)(ErrorDispatcher.default)

    def api_register(self, bp):
        """

        :param bp: app or blueprint
        """
        ErrorHandler.register(bp)(self._api_handler)

    def web_register(self, bp):
        """

        :param bp: app or blueprint
        """
        ErrorHandler.register(bp)(self._web_handler)

    def register_dispatcher(self, dispatcher, codes=None):
        """

        :param dispatcher:
        :param codes:
        """
        codes = codes or (404, 405)

        for c in codes:
            @self._app.errorhandler(c)
            def error_handler(exc):
                """

                :param exc:
                :return:
                """
                d = dispatcher(self._app)
                return d.dispatch(self.normalize(exc))
