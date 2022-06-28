from cgitb import text
import logging
import requests
import mapnik

from flask import current_app, g, Blueprint, render_template, request


logger = logging.getLogger("osm2tactile")

bp = Blueprint("osm2tactile", __name__)


def get_mapnik_stylesheet():
    background_color = "#ffffff"
    road = {
        "line": {  # line symbolizer
            "stroke": "#000000",
            "stroke_width": 3,
        },
        "text": {  # text symbolizer
            "allow_overlap": False,
            "face_name": "DejaVu Sans Book",
            "dx": 0.0,
            "dy": -15.0,
            "placement": "line",
            "size": 16,
        },
    }
    building = {
        "line": {"stroke": "#dddddd", "stroke_width": 3, "stroke_dasharray": "10,10"}
    }

    return render_template(
        "xml/mapnik_stylesheet.xml",
        background_color=background_color,
        road=road,
        building=building,
    )


@bp.route("/", methods=("GET",), strict_slashes=False)
def index():
    # sepcify coordinates
    # Witteslbachstraße 5, Vienna (Bundes-Blindeninstitut)
    lat, lon = 48.20635, 16.39929
    # TODO: query lon, lat coordinates from nominatim for given address

    # 1/60 = 1852m
    # a 0.0025 offset for latitude roughly translates to 300m
    # so map inlcudes approximately an area of 600 x 450m
    dx, dy = 0.0025, 0.0025
    # define bounding box area
    bounding_box = mapnik.Box2d(lon - dx, lat + dy, lon + dx, lat - dy)

    # transform the coordinates
    # mapnik spatial refernce system defaults to +proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs
    spherical_merc = mapnik.Projection("+init=epsg:3857")
    wgs84 = mapnik.Projection("+init=epsg:4326")  # longlat
    proj_transformation = mapnik.ProjTransform(wgs84, spherical_merc)
    bounding_box = proj_transformation.forward(bounding_box)

    # create a map with a given width and height in pixels
    map_width, map_height = 1024, 768  # px
    m = mapnik.Map(map_width, map_height)
    # zoom to bounding box
    m.zoom_to_box(bounding_box)

    # make the style available to the map with a name
    road_style_name = "road-style"
    building_style_name = "building-style"

    # create layer containing the actual map data
    roads_layer = mapnik.Layer("roads-layer")
    roads_layer.datasource = mapnik.PostGIS(
        host=current_app.config["POSTGRES_HOST"],
        user=current_app.config["POSTGRES_USER"],
        password=current_app.config["POSTGRES_PASSWORD"],
        dbname=current_app.config["POSTGRES_DB"],
        table="planet_osm_line",
    )
    # append a certain style to the layer
    roads_layer.styles.append(road_style_name)

    # create layer containing the actual map data
    building_layer = mapnik.Layer("roads-layer")
    building_layer.datasource = mapnik.PostGIS(
        host=current_app.config["POSTGRES_HOST"],
        user=current_app.config["POSTGRES_USER"],
        password=current_app.config["POSTGRES_PASSWORD"],
        dbname=current_app.config["POSTGRES_DB"],
        table="planet_osm_polygon",
    )
    # append a certain style to the layer
    building_layer.styles.append(building_style_name)

    # append the layer to the map
    mapnik.load_map_from_string(m, get_mapnik_stylesheet())
    m.layers.append(roads_layer)
    m.layers.append(building_layer)

    # save-path for the image
    static_path = "osm2tactile/static"
    map_path = "img"
    map_file_name = f"{lat}_{lon}_{dx}_{dy}.png"
    mapnik.render_to_file(m, f"{static_path}/{map_path}/{map_file_name}")

    return render_template(
        f"osm2tactile/index.html",
        mapnik_version=mapnik.mapnik_version_string(),
        map_img=f"{map_path}/{map_file_name}",
        lat=lat,
        lon=lon,
    )
