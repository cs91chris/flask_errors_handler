from functools import wraps

import flask
from flask import current_app as cap

from .exception import ApiProblem


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

        if not h.get('Content-Type'):
            h['Content-Type'] = 'application/{}+json'.format(ApiProblem.ct_id)
        elif cap.config['ERROR_FORCE_CONTENT_TYPE'] is True:
            h = force_content_type(h)

        options = dict(status=s, headers=h, mimetype=h['Content-Type'])
        return flask.Response(flask.json.dumps(r), **options)
    return wrapper


def force_content_type(hdr):
    """

    :param hdr: headers dict
    :return: updated headers
    """
    ct = hdr.get('Content-Type') or 'x-application/{}'.format(ApiProblem.ct_id)
    if ApiProblem.ct_id not in ct:
        if any([i in ct for i in cap.config['ERROR_CONTENT_TYPES']]):
            ct = "/{}+".format(ApiProblem.ct_id).join(ct.split('/', maxsplit=1))

    hdr.update({'Content-Type': ct})
    return hdr


def set_default_config(app):
    """

    :param app: Flask instance
    """
    app.config.setdefault('ERROR_PAGE', 'error.html')
    app.config.setdefault('ERROR_XHR_ENABLED', True)
    app.config.setdefault('ERROR_DEFAULT_MSG', 'Unhandled Exception')
    app.config.setdefault('ERROR_FORCE_CONTENT_TYPE', True)
    app.config.setdefault('ERROR_CONTENT_TYPES', ('json', 'xml'))
