from warnings import warn

from flask import request
from flask import make_response


class ErrorDispatcher(object):
    def __init__(self, app):
        """

        :param app: flask app
        """
        self._app = app

    @staticmethod
    def default(exc):
        """

        :param exc:
        :return:
        """
        resp = make_response('{}: {}'.format(exc.name, exc.description), exc.code)
        resp.headers['Content-Type'] = 'text/plain'
        return resp

    def dispatch(self, exc, **kwargs):
        """

        :param exc:
        """
        raise NotImplemented


class DefaultDispatcher(ErrorDispatcher):
    def dispatch(self, exc, **kwargs):
        """

        :param exc:
        """
        return self.default(exc)


class SubdomainDispatcher(ErrorDispatcher):
    def dispatch(self, exc, **kwargs):
        """

        :param exc:
        :return:
        """
        len_domain = len(self._app.config.get('SERVER_NAME') or '')
        if len_domain > 0:
            subdomain = request.host[:-len_domain].rstrip('.') or None
            for bp_name, bp in self._app.blueprints.items():
                if subdomain == bp.subdomain:
                    handler = self._app.error_handler_spec.get(bp_name, {}).get(exc.code)
                    for k, v in (handler or {}).items():
                        return v(exc)
        else:
            warn("You must set 'SERVER_NAME' in order to use {}".format(self.__class__.__name__))

        return super().default(exc)


class URLPrefixDispatcher(ErrorDispatcher):
    def dispatch(self, exc, **kwargs):
        """

        :param exc:
        :return:
        """
        for bp_name, bp in self._app.blueprints.items():
            if request.path.startswith(bp.url_prefix or '/'):
                handler = self._app.error_handler_spec.get(bp_name, {}).get(exc.code)
                for k, v in (handler or {}).items():
                    return v(exc)

        return super().default(exc)
