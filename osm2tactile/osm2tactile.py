import logging
import mapnik

from sqlalchemy import func
from flask import current_app, Blueprint, render_template

from osm2tactile.models import OSMLine


logger = logging.getLogger("osm2tactile")

bp = Blueprint("osm2tactile", __name__)


@bp.route("/", methods=("GET",), strict_slashes=False)
def index():
    # sepcify coordinates
    # Witteslbachstraße 5, Vienna (Bundes-Blindeninstitut)
    lat, lon = 48.20635, 16.39929  # longlat
    # TODO: query lon, lat coordinates from nominatim for given address

    # this project aims to allow printing maps on A4 paper (297 x 210mm)
    # Mapnik's DPI (Dot per Inch) is approximately 90.71, 1 Inch is 25.4mm
    # following the (90.71 x 297) / 25.4
    # that correlates with 1060 x 749 px
    A4 = (297, 210)  # landscape  # TODO: make customizable
    DPI = 90.71  # TODO: make customizable
    map_width, map_height = int((A4[0] * DPI) / 25.4), int((A4[1] * DPI) / 25.4)
    # calculate bound box center offsets
    dx = 0.0036  # TODO: make zoom level customizable
    dy = (((dx * 2) * map_height) / map_width) / 2
    logger.info(f"Calculated dy: {dy}")
    # 1/60 = 1852m
    # dx = 0.0036  ~400m
    # 1060/(dx*2) = 749/(dy*2)
    # makes dy about 0.0025, that roughly translates to 280m
    # so map inlcudes approximately an area of 800 x 560m

    # define bounding box area
    longlat_bounding_box = mapnik.Box2d(lon - dx, lat + dy, lon + dx, lat - dy)
    # transform the coordinates
    # mapnik spatial refernce system defaults to +proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs
    # data imported w/ osm2psql uses the web mercator (EPSG 3857) projection for geometry columns
    # by default and therefore, the bounding box must be transofrmed accordingly
    web_merctor_projection = mapnik.Projection("+init=epsg:3857")
    wgs84_projection = mapnik.Projection("+init=epsg:4326")
    proj_transformation = mapnik.ProjTransform(wgs84_projection, web_merctor_projection)
    web_mercator_bounding_box = proj_transformation.forward(longlat_bounding_box)

    # create a map with a given width and height in pixels
    m = mapnik.Map(map_width, map_height)
    # apsect fix mode options:  # TODO: make this customizable
    # m.aspect_fix_mode = mapnik.aspect_fix_mode.GROW_BBOX
    # m.aspect_fix_mode = mapnik.aspect_fix_mode.GROW_CANVAS
    # m.aspect_fix_mode = mapnik.aspect_fix_mode.SHRINK_CANVAS
    # m.aspect_fix_mode = mapnik.aspect_fix_mode.ADJUST_BBOX_WIDTH
    # m.aspect_fix_mode = mapnik.aspect_fix_mode.ADJUST_BBOX_HEIGHT
    # m.aspect_fix_mode = mapnik.aspect_fix_mode.ADJUST_CANVAS_WIDTH
    # m.aspect_fix_mode = mapnik.aspect_fix_mode.ADJUST_CANVAS_HEIGHT

    # zoom to bounding box
    m.zoom_to_box(web_mercator_bounding_box)
    map_envelope = m.envelope()
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
    map_envelope_list = [
        map_envelope.minx,
        map_envelope.miny,
        map_envelope.maxx,
        map_envelope.maxy,
        3857,
    ]
    streets = (
        OSMLine.query.with_entities(OSMLine.name)
        .filter(
            OSMLine.way.op(
                "&&"
            )(  # && ... intersects, @ ... contained by, ~ contains  # TODO: make this customizable
                func.ST_MakeEnvelope(*map_envelope_list)
            )
        )
        .filter(OSMLine.highway != None)  # noqa: E711
        .filter(OSMLine.name != None)  # noqa: E711
        .group_by(OSMLine.name)
        .all()
    )

    # TODO: pass image alt text with address at center location
    return render_template(
        "osm2tactile/index.html",
        mapnik_version=mapnik.mapnik_version_string(),
        map_img=f"{map_path}/{map_file_name}",
        map_width=map_width,
        map_height=map_height,
        lat=lat,
        lon=lon,
        streets=[street[0] for street in streets if street],
    )
