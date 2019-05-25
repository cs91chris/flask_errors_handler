import pytest

from flask import Flask
from flask import abort
from flask import Blueprint

from werkzeug.exceptions import BadRequest

from flask_errors_handler import ErrorHandler


@pytest.fixture
def app():
    _app = Flask(__name__)
    _app.config['ERROR_PAGE'] = 'error.html'
    error = ErrorHandler(_app)

    web = Blueprint('web', __name__)
    custom = Blueprint('custom', __name__)
    test_bp = Blueprint('test_bp', __name__)

    error.api_register(_app)
    error.web_register(web)

    @test_bp.route('/test')
    def test():
        exc = error.normalize(NameError('custom error'), exc_class=BadRequest)
        abort(exc.code, exc.description)

    @error.register(custom)
    def error_handler(exc):
        return str(exc), 500, {'Content-Type': 'text/plain'}

    @_app.route('/api')
    def index():
        abort(500, 'Error from app')

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

    _app.register_blueprint(web)
    _app.register_blueprint(custom)
    _app.register_blueprint(test_bp)

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
    assert res.headers.get('Content-Type') == 'application/json'


def test_api_error(client):
    res = client.get('/api/error')
    assert res.status_code == 500
    assert res.headers.get('Content-Type') == 'application/json'


def test_web(client):
    res = client.get('/web')
    assert res.status_code == 500
    assert res.headers.get('Content-Type') == 'text/html; charset=utf-8'


def test_web_xhr(client):
    res = client.get('/web', headers={'X-Requested-With': 'XMLHttpRequest'})
    assert res.status_code == 500
    assert res.headers.get('Content-Type') == 'application/json'


def test_web_error(client):
    res = client.get('/web/error')
    assert res.status_code == 500
    assert res.headers.get('Content-Type') == 'text/html; charset=utf-8'


def test_custom(client):
    res = client.get('/custom')
    assert res.status_code == 500
    assert res.headers.get('Content-Type') == 'text/plain'


def test_custom_error(client):
    res = client.get('/test')
    assert res.status_code == 400
    assert res.headers.get('Content-Type') == 'application/json'
