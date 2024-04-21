import os
import logging

from flask import Flask
from rich.logging import RichHandler


FORMAT = "%(message)s"
logging.basicConfig(
    level="DEBUG", format=FORMAT, datefmt="%Y-%m-%d %H:%M:%S", handlers=[RichHandler()]
)

logger = logging.getLogger("osm2tactile")


def create_app(test_config=None):
    """
    # TODO: comment create_app
    :param test_config:
    :return:
    """
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    if test_config is None:
        # load the instance config, if it exists, when not testing
        config_file = "config.py"
        app.config.from_pyfile(config_file, silent=True)
        logger.debug(f"Loaded app conifg from {config_file}.")
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)
        logger.debug(f"Loaded app conifg from mapping {test_config}.")

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # db stuff
    from osm2tactile.db import db, setup_engine

    with app.app_context():
        setup_engine()

    db.init_app(app)
    logger.debug("Setup db engine and initialzed app.")

    # register blueprints
    from osm2tactile import osm2tactile

    app.register_blueprint(osm2tactile.bp)
    logger.debug("Registered osm2tactile blueprint")

    app.add_url_rule("/", endpoint="root", view_func=osm2tactile.index)
    logger.debug("Added url rule for / as root endpoint to osm2tactile.index")

    return app
