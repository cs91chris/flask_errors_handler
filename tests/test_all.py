import pytest

from flask import Flask
from flask import abort
from flask import Response
from flask import Blueprint

from werkzeug.exceptions import BadRequest

from flask_errors_handler import ErrorHandler
from flask_errors_handler import DefaultDispatcher
from flask_errors_handler import SubdomainDispatcher
from flask_errors_handler import URLPrefixDispatcher


error = ErrorHandler()


@pytest.fixture
def app():
    _app = Flask(__name__)
    _app.config['SERVER_NAME'] = 'flask.dev:5000'
    _app.config['ERROR_PAGE'] = 'error.html'

    web = Blueprint('web', __name__)
    test_bp = Blueprint('test_bp', __name__)
    custom = Blueprint('custom', __name__, subdomain='api')

    error.init_app(_app)
    error.api_register(_app)
    error.web_register(web)

    @test_bp.route('/test')
    def test():
        exc = error.normalize(NameError('custom error'), exc_class=BadRequest)
        abort(exc.code, exc.description)

    @error.register(custom)
    def error_handler(exc):
        return str(exc), 404, {'Content-Type': 'text/html', 'custom': 'test'}

    @_app.route('/api')
    def index():
        abort(500, 'Error from app')

    @_app.route('/api/response')
    def response():
        abort(500, response=Response("response"))

    @_app.route('/permanent/')
    def permanent():
        return 'redirected'

    @_app.route('/api/error')
    def api_error():
        raise NameError('exception from app')

    @web.route('/web')
    def index():
        abort(500, 'Error from web blueprint')

    @web.route('/web/error')
    def web_error():
        _app.config['ERROR_PAGE'] = None
        abort(500, 'Error from web blueprint')

    @custom.route('/custom')
    def index():
        abort(500, 'Error from custom blueprint')

    _app.register_blueprint(custom)
    _app.register_blueprint(web, url_prefix='/web')
    _app.register_blueprint(test_bp, url_prefix='/testbp')

    _app.testing = True
    return _app


@pytest.fixture
def client(app):
    _client = app.test_client()
    return _client


def test_app_runs(client):
    res = client.get('/')
    assert res.status_code == 404


def test_api(client):
    res = client.get('/api')
    assert res.status_code == 500
    assert res.headers.get('Content-Type') == 'application/problem+json'

    data = res.get_json()
    assert data['type'] == 'about:blank'
    assert data['title'] == 'Internal Server Error'
    assert data['detail'] is not None
    assert data['status'] == 500
    assert data['instance'] == 'about:blank'
    assert data['response'] is None


def test_api_error(client):
    res = client.get('/api/error')
    assert res.status_code == 500
    assert res.headers.get('Content-Type') == 'application/problem+json'


def test_web(client):
    res = client.get('/web/web')
    assert res.status_code == 500
    assert res.headers.get('Content-Type') == 'text/html; charset=utf-8'


def test_web_xhr(client):
    res = client.get('/web/web', headers={'X-Requested-With': 'XMLHttpRequest'})
    assert res.status_code == 500
    assert res.headers.get('Content-Type') == 'application/problem+json'


def test_web_error(client):
    res = client.get('/web/web/error')
    assert res.status_code == 500
    assert res.headers.get('Content-Type') == 'text/html; charset=utf-8'


def test_custom(client, app):
    res = client.get('/custom', base_url='http://api.' + app.config['SERVER_NAME'])
    assert res.status_code == 404
    print(res.headers)
    assert res.headers.get('Content-Type') == 'text/html'


def test_custom_error(client):
    res = client.get('/testbp/test')
    assert res.status_code == 400
    assert res.headers.get('Content-Type') == 'application/problem+json'


def test_dispatch_error_web(client):
    error.register_dispatcher(URLPrefixDispatcher)
    res = client.get('/web/web/page-not-found')
    assert res.status_code == 404
    assert 'text/html' in res.headers['Content-Type']


def test_dispatch_error_api(client, app):
    error.register_dispatcher(SubdomainDispatcher)
    res = client.get('/api-not-found', base_url='http://api.' + app.config['SERVER_NAME'])
    assert res.status_code == 404
    assert 'text/html' in res.headers['Content-Type']
    assert 'test' in res.headers['custom']


def test_dispatch_default(client):
    error.register_dispatcher(DefaultDispatcher)
    res = client.get('/testbp/not-found')
    assert res.status_code == 404
    assert 'text/plain' in res.headers['Content-Type']

    res = client.post('/testbp/test')
    assert res.status_code == 405
    assert 'text/plain' in res.headers['Content-Type']


def test_permanent_redirect(client):
    res = client.get('/permanent')
    assert res.status_code == 301


def test_response(client):
    res = client.get('/api/response')
    assert res.status_code == 500
    assert res.data == b'response'
