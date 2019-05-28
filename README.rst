Flask-ErrorsHandler
===================

Set default errors handler for flask app and blueprints.

You can register handler for api that returns JSON, for web that returns html page or JSON if request is XHR, or
you can register custom handlers for blueprint or the entire app.


QuickStart
~~~~~~~~~~

Install ``flask_errors_handler`` using ``pip``:

::

   $ pip install Flask-ErrorsHandler

.. _section-1:

Example usage
^^^^^^^^^^^^^

.. code:: python

    from flask import Flask
    from flask import abort
    from flask import Blueprint

    from flask_errors_handler import ErrorHandler


    app = Flask(__name__)
    app.config['ERROR_PAGE'] = 'error.html'

    error = ErrorHandler(app)

    custom = Blueprint('custom', __name__)
    web = Blueprint('web', __name__)

    error.api_register(app)
    error.web_register(web)

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
    app.run()


- Go to http://127.0.0.1:5000/api and see error message response as a JSON
- Go to http://127.0.0.1:5000/web and see error message response as an HTML page
- Go to http://127.0.0.1:5000/custom and see error message response as a plain text

.. _section-2:

Configuration
^^^^^^^^^^^^^

1. ``ERROR_PAGE``: *(default: None)* path of html template to use for show error message
2. ``ERROR_DEFAULT_MSG``: *(default: Unhandled Exception)* default message for unhandled exceptions

License MIT
