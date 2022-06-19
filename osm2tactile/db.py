from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base


db = SQLAlchemy()
Base = declarative_base()


def setup_engine():
    engine = create_engine(
        current_app.config.get("SQLALCHEMY_DATABASE_URI"),
    )
    Base.metadata.reflect(engine)
