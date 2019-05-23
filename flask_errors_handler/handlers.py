import traceback
from functools import wraps

from flask import abort
from flask import request
from flask import jsonify
from flask import render_template

from werkzeug.exceptions import HTTPException
from werkzeug.exceptions import default_exceptions
from werkzeug.exceptions import InternalServerError


def default_response_builder(f):
    """

    :param f: function that returns dict or Response object and status code
    :return: flask jsonify and status code of decorated function
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        r, s = f(*args, **kwargs)
        return jsonify(r), s
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
        self._app.config.setdefault('ERROR_DEFAULT_MSG', 'Unhandled Exception')

    @staticmethod
    def register(bp, hderr):
        """

        :param bp: blueprint or flask app
        :param hderr: function that takes only an Exception object as argument
        """
        for code in default_exceptions.keys():
            bp.errorhandler(code)(hderr)

        bp.register_error_handler(Exception, hderr)

    def _normalize(self, ex):
        """
        Wraps a generic Exception into InternalServerError in order to have the same interface
        :param ex: Exception
        :return: new Exception instance of HTTPException
        """
        if not isinstance(ex, HTTPException):
            self._app.logger.error(traceback.format_exc())
            ex = InternalServerError(
                ex if self._app.config['DEBUG']
                else self._app.config['ERROR_DEFAULT_MSG']
            )
        return ex

    def _api_error_handler(self, ex):
        """

        :param ex: Exception
        :return:
        """
        ex = self._normalize(ex)

        @self._response
        def _response():
            return dict(
                error=ex.name,
                description=ex.description,
                status=ex.code,
                response=ex.response or {}
            ), ex.code

        return _response()

    def _web_error_handler(self, ex):
        """

        :param ex: Exception
        :return:
        """
        ex = self._normalize(ex)

        if request.is_xhr:
            return self._api_error_handler(ex)

        if self._app.config['ERROR_PAGE']:
            return render_template(
                self._app.config['ERROR_PAGE'],
                error=ex.name,
                message=ex.description
            ), ex.code

        abort(ex.code, ex.description)

    def api_register(self, component):
        """

        :param component: app or blueprint
        """
        ErrorHandler.register(
            component,
            self._api_error_handler
        )

    def web_register(self, component):
        """

        :param component: app or blueprint
        """
        ErrorHandler.register(
            component,
            self._web_error_handler
        )
