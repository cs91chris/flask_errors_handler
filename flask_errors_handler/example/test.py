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


@app.route('/api')
def index():
    abort(500, 'Error from app')


@web.route('/web')
def index():
    abort(500, 'Error from web blueprint')


app.register_blueprint(web)
app.run()
