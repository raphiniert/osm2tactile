import logging
import requests
import mapnik

from flask import current_app, g, Blueprint, render_template, request


logger = logging.getLogger("osm2tactile")

bp = Blueprint("osm2tactile", __name__)


@bp.route("/", methods=("GET",), strict_slashes=False)
def index():
    return render_template(
        f"osm2tactile/index.html", mapnik_version=mapnik.mapnik_version_string()
    )
