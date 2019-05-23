import traceback

from flask import abort
from flask import request
from flask import render_template

from flask_json import as_json

from werkzeug.exceptions import HTTPException
from werkzeug.exceptions import default_exceptions
from werkzeug.exceptions import InternalServerError


class ErrorHandler:
    def __init__(self, app=None, response=None):
        """

        :param app:
        :param response:
        """
        self._app = None
        self._response = None

        if app is not None:
            self.init_app(app, response)

    def init_app(self, app, response=None):
        """

        :param app:
        :param response:
        """
        self._app = app
        self._response = response or as_json
        self._app.config.setdefault('ERROR_PAGE', None)
        self._app.config.setdefault('ERROR_DEFAULT_MSG', 'Unhandled Exception')

    @staticmethod
    def _register(bp, hderr, hddef):
        """

        :param bp:
        :param hderr:
        :param hddef:
        """
        for code in default_exceptions.keys():
            bp.errorhandler(code)(hderr)

        bp.register_error_handler(Exception, hddef)

    def _make_response_error(self, ex):
        """

        :param ex:
        :return:
        """
        @self._response
        def _response():
            if isinstance(ex, HTTPException) and ex.code:
                status_code = ex.code
            else:
                status_code = 500

            response = dict(message=str(ex), status=status_code)
            return response, status_code
        return _response()

    def _api_all_error_handler(self, error):
        """

        :param error:
        :return:
        """
        self._app.logger.error(traceback.format_exc())
        exc = InternalServerError(
            error if self._app.config['DEBUG']
            else self._app.config['ERROR_DEFAULT_MSG']
        )
        return self._make_response_error(exc)

    def _web_error_handler(self, e):
        """

        :param e:
        :return:
        """
        if not isinstance(e, HTTPException):
            self._app.logger.error(traceback.format_exc())
            e = InternalServerError()

        if request.is_xhr:
            @self._response
            def jsonify():
                return {
                    'status': e.code,
                    'error': e.name,
                    'message': e.description
                }, e.code
            return jsonify()

        if self._app.config['ERROR_PAGE']:
            return render_template(
                self._app.config['ERROR_PAGE'],
                error=e.name,
                message=e.description
            ), e.code

        abort(e.code, e.description)

    def api_register(self, component):
        """

        :param component:
        """
        ErrorHandler._register(
            component,
            self._make_response_error,
            self._api_all_error_handler
        )

    def web_register(self, component):
        """

        :param component:
        """
        ErrorHandler._register(
            component,
            self._web_error_handler,
            self._web_error_handler
        )
