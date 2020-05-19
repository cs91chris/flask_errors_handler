from functools import wraps

import flask
from flask import current_app as cap
from jinja2 import TemplateError
from werkzeug.exceptions import default_exceptions

from . import utils
from .exception import ApiProblem
from .normalize import DefaultNormalizeMixin
from .dispatchers import ErrorDispatcher, DEFAULT_DISPATCHERS


class ErrorHandler(DefaultNormalizeMixin):
    def __init__(self, app=None, **kwargs):
        """

        :param app: optional Flask instance
        """
        self._response = None
        self._exc_class = None

        if app is not None:
            self.init_app(app, **kwargs)

    def init_app(self, app, response=None, exc_class=None, dispatcher=None):
        """

        :param app: Flask instance
        :param response: decorator that produces a Flask Response object
        :param exc_class: subclass of ApiProblem
        :param dispatcher: ErrorDispatcher instance or default configured string name
        """
        self._exc_class = exc_class or ApiProblem
        self._response = response or utils.default_response_builder

        if not issubclass(self._exc_class, ApiProblem):
            raise TypeError("exc_class argument must extend ApiProblem class")

        utils.set_default_config(app)

        if not hasattr(app, 'extensions'):
            app.extensions = dict()
        app.extensions['errors_handler'] = self

        if dispatcher is not None:
            self.register_dispatcher(app, dispatcher)

    @staticmethod
    def register(bp, code=None):
        """

        :param code: optional a specific http code otherwise all
        :param bp: blueprint or flask app
        """
        def _register(hderr):
            """

            :param hderr: function that takes only an Exception object as argument
            """
            @wraps(hderr)
            def wrapper():
                if code is not None:
                    bp.errorhandler(code)(hderr)
                else:
                    for c in default_exceptions.keys():
                        bp.errorhandler(c)(hderr)

                    ErrorHandler.failure(bp)(hderr)

            return wrapper()
        return _register

    @staticmethod
    def failure(bp):
        """

        :param bp: blueprint or flask app
        """
        def _register(hderr):
            """

            :param hderr: function that takes only an Exception object as argument
            """
            @wraps(hderr)
            def wrapper():
                bp.register_error_handler(Exception, hderr)

            return wrapper()
        return _register

    def _failure_handler(self, ex):
        """

        :param ex: Exception instance
        :return: default template rendered response
        """
        ex = self.normalize(ex, self._exc_class)
        return flask.render_template_string(ex.default_html_template, exc=ex), ex.code

    def _api_handler(self, ex):
        """

        :param ex: Exception instance
        :return: response built from self._response
        """
        ex = self.normalize(ex, self._exc_class)

        if isinstance(ex.response, flask.Response):
            return ex.response, ex.code

        resp = self._response(lambda: ex.prepare_response())()

        if cap.config['ERROR_FORCE_CONTENT_TYPE'] is True:
            resp.headers = utils.force_content_type(resp.headers)

        return resp

    def _web_handler(self, ex):
        """

        :param ex: Exception instance
        :return: a template rendered response
        """
        ex = self.normalize(ex, self._exc_class)

        if cap.config['ERROR_XHR_ENABLED'] is True:
            # check if request is XHR (for compatibility with old clients)
            if flask.request.headers.get('X-Requested-With', '').lower() == "xmlhttprequest":
                return self._api_handler(ex)

        try:
            return flask.render_template(cap.config['ERROR_PAGE'], error=ex), ex.code
        except TemplateError:
            return flask.render_template_string(ex.default_html_template, exc=ex), ex.code

    def default_register(self, bp):
        """

        :param bp:
        """
        ErrorHandler.register(bp)(self._failure_handler)

    def failure_register(self, bp, callback=None):
        """

        :param bp: blueprint or flask app
        :param callback: optional function to register
        """
        ErrorHandler.failure(bp)(callback or self._failure_handler)

    def api_register(self, bp, callback=None, **kwargs):
        """

        :param bp: app or blueprint
        :param callback: optional function to register
        :param kwargs: passed to register
        """
        ErrorHandler.register(bp, **kwargs)(callback or self._api_handler)

    def web_register(self, bp, callback=None, **kwargs):
        """

        :param bp: app or blueprint
        :param callback: optional function to register
        :param kwargs: passed to register
        """
        ErrorHandler.register(bp, **kwargs)(callback or self._web_handler)

    def register_dispatcher(self, app, dispatcher, codes=(404, 405)):
        """

        :param app: Flask instance
        :param dispatcher: ErrorDispatcher class or a string name of default dispatcher
        :param codes: list of http codes
        """
        try:
            issubclass(dispatcher, ErrorDispatcher)
            dispatcher_class = dispatcher
        except TypeError:
            dispatcher_class = DEFAULT_DISPATCHERS.get(dispatcher)
            if not dispatcher_class:
                app.logger.error(
                    "dispatcher '{}' not exists. Use one of {}".format(
                        dispatcher, DEFAULT_DISPATCHERS.keys()
                    ))
                return

        for c in codes:
            @app.errorhandler(c)
            def error_handler(exc):
                """

                :param exc: Exception instance
                :return: dispatcher response
                """
                d = dispatcher_class(app)
                return d.dispatch(self.normalize(exc, self._exc_class))
