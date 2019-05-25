from flask import Flask
from flask import abort
from flask import Blueprint

from flask_errors_handler import ErrorHandler


app = Flask(__name__)
app.config['ERROR_PAGE'] = 'error.html'

error = ErrorHandler()
error.init_app(app)
error.api_register(app)

web = Blueprint('web', __name__)
error.web_register(web)

custom = Blueprint('custom', __name__)


@error.register(custom)
def error_handler(exc):
    return str(exc), 500, {'Content-Type': 'text/plain'}


@app.route('/api')
def index():
    abort(500, 'Error from app')


@web.route('/web')
def index():
    abort(500, 'Error from web blueprint')


@custom.route('/custom')
def index():
    abort(500, 'Error from custom blueprint')


app.register_blueprint(web)
app.register_blueprint(custom)
app.run()
