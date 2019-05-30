Flask-ErrorsHandler
===================

Set customizable default errors handler for flask app and blueprints.

You can register error handler for:

- api that returns JSON, default response is as API problem specification like (see https://tools.ietf.org/html/rfc7807).
  Instead you can use your own response implementation passed as argument to ``ErrorHandler`` class:
  it must be a decorator and must take 3 args, a dict response, status code and dict headers.
- web that returns html page or api response if request is XHR
- you can register custom handlers for blueprint or the entire app

This module provide also an abstract ``ErrorDispatcher`` class in order to dispatch 404 or 405 error to the correct blueprint
because flask Blueprint does not own url_prefix (see https://github.com/pallets/flask/issues/1498).

There are 2 concrete implementation:

- ``SubdomainDispatcher``: dispatch the error to the handler associate with blueprint with certain subdomain
  (if 2 or more Blueprint has the same subdomain the first blueprint handler matched is used)
- ``URLPrefixDispatcher``: dispatch the error to the handler associate with blueprint with certain url prefix.
  This will not work if 2 Blueprint are registered under the same url prefix, for example:
  Blueprint A registered under /prefix/blueprint, Blueprint B registered under /prefix, this dispatcher executes the handler
  of B in both case if B is registered after A.

Moreover you can create you own dispatcher by extending ``ErrorDispatcher`` class and implementing ``dispatch`` method.
Only the *last* ErrorDispatcher registered is execute. This is the best solution I have found, suggestions are welcome.


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
3. ``ERROR_XHR_ENABLED``: *(default: True)* enable or disable api response where request is XHR


License MIT
