import logging

from flask import Flask


log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)


def create_app():
    app = Flask(__name__)

    from . import api

    app.register_blueprint(api.bp)

    return app


app = create_app()
