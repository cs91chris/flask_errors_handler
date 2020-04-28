from warnings import warn

import flask


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
        return flask.render_template_string(
            exc.default_html_template, exc=exc
        ), exc.code

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
            subdomain = flask.request.host[:-len_domain].rstrip('.') or None
            for bp_name, bp in self._app.blueprints.items():
                if subdomain == bp.subdomain:
                    handler = self._app.error_handler_spec.get(bp_name, {}).get(exc.code)
                    for k, v in (handler or {}).items():
                        return v(exc)
        else:
            warn("You must set 'SERVER_NAME' in order to use {}".format(self.__class__.__name__))

        return self.default(exc)


class URLPrefixDispatcher(ErrorDispatcher):
    def dispatch(self, exc, **kwargs):
        """

        :param exc:
        :return:
        """
        for bp_name, bp in self._app.blueprints.items():
            if not bp.url_prefix:
                warn("You must set 'url_prefix' when instantiate Blueprint: '{}'".format(bp_name))
                continue

            if flask.request.path.startswith(bp.url_prefix):
                handler = self._app.error_handler_spec.get(bp_name, {}).get(exc.code)
                for k, v in (handler or {}).items():
                    return v(exc)

        return self.default(exc)


DEFAULT_DISPATCHERS = {
    'default': DefaultDispatcher,
    'subdomain': SubdomainDispatcher,
    'urlprefix': URLPrefixDispatcher,
}
