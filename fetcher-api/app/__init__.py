from flask import Flask

from . import db
from .config import Config
from .routes import bp


def create_app():
    app = Flask(__name__)
    config = Config()
    app.config["APP_CONFIG"] = config
    db.init_pool(config)
    app.register_blueprint(bp)
    return app
