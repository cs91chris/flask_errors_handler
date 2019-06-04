import traceback
from functools import wraps

from flask import json
from flask import request
from flask import Response
from flask import render_template

from werkzeug.routing import RequestRedirect
from werkzeug.exceptions import HTTPException
from werkzeug.exceptions import default_exceptions

from .exception import ApiProblem
from .dispatchers import ErrorDispatcher


def default_response_builder(f):
    """

    :param f: function that returns dict or Response object and status code
    :return: flask response  of decorated function
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        r, s, h = f(*args, **kwargs)
        m = 'application/problem+json'
        return Response(json.dumps(r), status=s, headers=h, mimetype=m)
    return wrapper


class ErrorHandler:
    def __init__(self, app=None, response=None, exc_class=None):
        """

        :param app:
        :param response: decorator
        :param exc_class: subclass of ApiProblem
        """
        self._app = None
        self._response = None
        self._exc_class = None

        if app is not None:
            self.init_app(app, response, exc_class)

    def init_app(self, app, response=None, exc_class=None):
        """

        :param app:
        :param response: decorator
        :param exc_class: subclass of ApiProblem
        """
        self._app = app
        self._response = response or default_response_builder
        self._exc_class = exc_class or ApiProblem

        if not issubclass(self._exc_class, ApiProblem):
            raise AttributeError("exc_class argument must extend ApiProblem class")

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
        :param exc_class: overrides self._exc_class
        :return: new Exception instance of HTTPException
        """
        # noinspection PyPep8Naming
        ExceptionClass = exc_class or self._exc_class

        if not isinstance(ex, ExceptionClass):
            tb = traceback.format_exc()
            self._app.logger.error(tb)

            _ex = ExceptionClass(
                tb if self._app.config['DEBUG']
                else self._app.config['ERROR_DEFAULT_MSG'],
                **kwargs
            )

            if isinstance(ex, HTTPException):
                _ex.code = ex.code
                _ex.description = ex.description
                _ex.response = ex.response if hasattr(ex, 'response') else None
        else:
            _ex = ex

        if isinstance(ex, RequestRedirect):
            _ex.headers.update(dict(Location=ex.new_url))
        return _ex

    def _api_handler(self, ex):
        """

        :param ex: Exception
        :return:
        """
        ex = self.normalize(ex)

        if hasattr(ex, 'response'):
            response_data = ex.response
            if isinstance(response_data, Response):
                return ex.response, ex.code
        else:
            response_data = None

        @self._response
        def _response():
            return dict(
                type=ex.type,
                title=ex.name,
                detail=ex.description,
                instance=ex.instance,
                response=response_data,
                status=ex.code
            ), ex.code, ex.headers

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
