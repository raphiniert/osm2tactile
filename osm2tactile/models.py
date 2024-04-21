import logging

from osm2tactile.db import db, Base

logger = logging.getLogger("osm2tactile")


class OSMNodes(db.Model):
    __table__ = Base.metadata.tables["planet_osm_nodes"]


class OSMWays(db.Model):
    __table__ = Base.metadata.tables["planet_osm_ways"]


class OSMRels(db.Model):
    __table__ = Base.metadata.tables["planet_osm_rels"]


class OSMPoint(db.Model):
    __table__ = Base.metadata.tables["planet_osm_point"]
    __mapper_args__ = {
        "primary_key": [Base.metadata.tables["planet_osm_point"].c.osm_id]
    }


class OSMLine(db.Model):
    __table__ = Base.metadata.tables["planet_osm_line"]
    __mapper_args__ = {
        "primary_key": [Base.metadata.tables["planet_osm_line"].c.osm_id]
    }


class OSMPolygon(db.Model):
    __table__ = Base.metadata.tables["planet_osm_polygon"]
    __mapper_args__ = {
        "primary_key": [Base.metadata.tables["planet_osm_polygon"].c.osm_id]
    }


class OSMRoads(db.Model):
    __table__ = Base.metadata.tables["planet_osm_roads"]
    __mapper_args__ = {
        "primary_key": [Base.metadata.tables["planet_osm_roads"].c.osm_id]
    }
