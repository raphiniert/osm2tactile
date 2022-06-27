import logging
import requests
import mapnik

from sqlalchemy import func
from flask import current_app, g, Blueprint, render_template, request

from osm2tactile.models import OSMNodes, OSMLine, OSMPoint, OSMPolygon


logger = logging.getLogger("osm2tactile")

bp = Blueprint("osm2tactile", __name__)


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
    road_style_name = "roads-fill-dejavu"

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

    # append the layer to the map
    mapnik.load_map(m, "osm2tactile/static/xml/mapnik_stylesheet.xml")
    m.layers.append(roads_layer)

    # save-path for the image
    static_path = "osm2tactile/static"
    map_path = "img"
    map_file_name = f"{lat}_{lon}_{dx}_{dy}.png"
    mapnik.render_to_file(m, f"{static_path}/{map_path}/{map_file_name}")

    # query street names (lines that are highways), intersecting the bounding box
    envelope = [
        bounding_box.minx,
        bounding_box.miny,
        bounding_box.maxx,
        bounding_box.maxy,
    ]
    streets = (
        OSMLine.query.with_entities(OSMLine.name)
        .filter(OSMLine.way.op("&&")(func.ST_MakeEnvelope(*envelope)))
        .filter(OSMLine.highway != None)
        .filter(OSMLine.name != None)
        .group_by(OSMLine.name)
        .all()
    )

    # query points of interest and nearest steet for guessing the street
    points = (
        OSMPoint.query.filter(OSMPoint.way.op("&&")(func.ST_MakeEnvelope(*envelope)))
        .filter(OSMPoint.name != None)
        .all()
    )
    # TODO: make this a function or template fiter to get street name
    point_lines = {}
    for point in points:
        line = (
            OSMLine.query.with_entities(
                OSMLine.name,
                func.ST_Distance(
                    func.ST_LineInterpolatePoint(
                        OSMLine.way, func.ST_LineLocatePoint(OSMLine.way, point.way)
                    ),
                    point.way,
                ).label("distance"),
            )
            .filter(OSMLine.way.op("&&")(func.ST_MakeEnvelope(*envelope)))
            .filter(OSMLine.highway != None)
            .filter(OSMLine.name != None)
            .order_by("distance")
            .first()
        )
        point_lines[point.osm_id] = line[0]

    # TODO: query public transport stations

    # query buildings
    buildings = (
        OSMPolygon.query.filter(
            OSMPolygon.way.op("&&")(func.ST_MakeEnvelope(*envelope))
        )
        .filter(OSMPolygon.building != None)
        .all()
    )

    return render_template(
        f"osm2tactile/index.html",
        mapnik_version=mapnik.mapnik_version_string(),
        map_img=f"{map_path}/{map_file_name}",
        lat=lat,
        lon=lon,
        dx=dx,
        dy=dy,
        streets=streets,
        points=points,
        point_lines=point_lines,
        buildings=buildings,
    )
