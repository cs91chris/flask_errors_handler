import traceback
from functools import wraps

import flask
from werkzeug.exceptions import HTTPException, default_exceptions

from .exception import ApiProblem
from .dispatchers import ErrorDispatcher
from .normalize import DefaultNormalizeMixin


def default_response_builder(f):
    """

    :param f: function that returns dict response, status code and headers dict
    :return: flask response of decorated function
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        """

        :param args:
        :param kwargs:
        :return:
        """
        r, s, h = f(*args, **kwargs)

        m = h.get('Content-Type', '')
        if ApiProblem.ct_id not in m or 'json' not in m:
            m = 'application/{}+json'.format(ApiProblem.ct_id)

        return flask.Response(
            flask.json.dumps(r),
            status=s,
            headers=h,
            mimetype=m
        )

    return wrapper


class ErrorHandler(DefaultNormalizeMixin):
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
        self._exc_class = exc_class or ApiProblem
        self._response = response or default_response_builder

        if not issubclass(self._exc_class, ApiProblem):
            raise TypeError("exc_class argument must extend ApiProblem class")

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
                """

                """
                for code in default_exceptions.keys():
                    bp.errorhandler(code)(hderr)

                bp.register_error_handler(Exception, hderr)

            return wrapper()
        return _register

    def normalize(self, ex, exc_class=None, **kwargs):
        """

        :param ex: Exception
        :param exc_class: overrides ApiProblem class
        :return: new Exception instance of HTTPException
        """
        # noinspection PyPep8Naming
        ExceptionClass = exc_class or self._exc_class
        ex = super().normalize(ex, exc_class)

        if isinstance(ex, ExceptionClass):
            return ex

        tb = traceback.format_exc()
        if self._app.config['DEBUG']:
            mess = tb
        else:
            mess = self._app.config['ERROR_DEFAULT_MSG']

        _ex = ExceptionClass(mess, **kwargs)

        if isinstance(ex, HTTPException):
            _ex.code = ex.code
            _ex.description = ex.description
            _ex.response = ex.response if hasattr(ex, 'response') else None
            _ex.headers.update(**(ex.headers if hasattr(ex, 'headers') else {}))
        else:
            self._app.logger.error(tb)

        return _ex

    def _api_handler(self, ex):
        """

        :param ex: Exception
        :return:
        """
        ex = self.normalize(ex)

        if isinstance(ex.response, flask.Response):
            return ex.response, ex.code

        @self._response
        def _response():
            """

            :return:
            """
            return ex.prepare_response()

        resp = _response()

        # ugly hack in order to send the correct "api problem" content-type header in response
        # when using a custom response builder that is not compatible
        ct = resp.headers.get('Content-Type') or 'x-application/{}'.format(ApiProblem.ct_id)
        if ApiProblem.ct_id not in ct:
            if 'json' in ct or 'xml' in ct:
                ct = "/{}+".format(ApiProblem.ct_id).join(ct.split('/', maxsplit=1))

        resp.headers.update({'Content-Type': ct})
        # end hack

        return resp

    def _web_handler(self, ex):
        """

        :param ex: Exception
        :return:
        """
        ex = self.normalize(ex)

        if self._app.config['ERROR_XHR_ENABLED'] is True:
            # check if request is XHR (for compatibility with old clients)
            if flask.request.headers.get('X-Requested-With', '').lower() == "xmlhttprequest":
                return self._api_handler(ex)

        if self._app.config['ERROR_PAGE'] is not None:
            return flask.render_template(
                self._app.config['ERROR_PAGE'],
                error=ex
            ), ex.code

        if self._app.config['DEBUG']:
            return str(ex)
        else:
            return self._app.config['ERROR_DEFAULT_MSG'], 500

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
