FROM python:3.9.9-alpine3.13

ENV MAPNIK_VERSION v3.0.24
ENV PYTHON_MAPNIK_BRANCH v3.0.x

### Download Locations
ARG PYTHON_MAPNIK_SOURCE="https://github.com/mapnik/python-mapnik.git"
ARG MAPNIK_SOURCE="https://github.com/mapnik/mapnik/releases/download/$MAPNIK_VERSION/mapnik-$MAPNIK_VERSION.tar.bz2"

### update apk and existing packages
RUN apk upgrade --update \
    ### build dependencies
    && apk add --virtual .build-deps \
        ### basic build packages              
        build-base \
        wget \
        bash \
        git \
        cairo-dev  \
        freetype  \
        harfbuzz-dev  \
        icu-dev  \
        libpng-dev  \
        libwebp-dev  \
        libxml2-dev  \
        sqlite-dev  \
        scons  \
        tiff-dev \
        zlib-dev  \
        cmake \
        g++ \
        expat-dev \
        bzip2-dev \
        zlib-dev \
        libpq \
        nlohmann-json \
        lua5.3-dev \
    && apk add --virtual .run-deps \
        boost-dev \
        postgis \
        postgresql-dev \
        boost-python3 \
    && apk add --virtual .build-deps-testing \
        --repository http://dl-cdn.alpinelinux.org/alpine/edge/testing \
        gdal-dev \
        proj-dev \
    && apk add --virtual .run-deps-testing \
        --repository http://dl-cdn.alpinelinux.org/alpine/edge/testing \
        gdal \
        proj
 
# ### Mapnik installation
RUN git clone https://github.com/mapnik/mapnik.git \
    && cd mapnik \
    && git checkout $MAPNIK_VERSION \
    && git submodule update --init \
    && python scons/scons.py INPUT_PLUGINS='all' \
    && ./configure \
    && make -j $(nproc) \
    && make install \
    && cd - \
    && rm -r mapnik

# # #    
# ### python-mapnik download + installation
RUN git clone https://github.com/mapnik/python-mapnik.git \
    && cd python-mapnik \
    && git checkout $PYTHON_MAPNIK_BRANCH \
    && export BOOST_PYTHON_LIB=boost_python38 \
    && python setup.py install \
    && cd - \
    && rm -r python-mapnik

# # # install osm2psql
# RUN apk --update-cache add cmake make g++ expat-dev \
#   bzip2-dev zlib-dev libpq nlohmann-json lua5.3-dev
RUN git clone https://github.com/openstreetmap/osm2pgsql.git \
  && cd osm2pgsql \
  && mkdir build && cd build \
  && cmake .. \
  && make -j $(nproc) \
  && make install \
  && cd ../../ \
  && rm -r osm2pgsql

## clean up files
# RUN apk del .build-deps \
RUN apk del .build-deps-testing \
    && rm -rf /tmp/* /var/cache/apk/* /usr/src/* \
    && ln -s /usr/local/lib/mapnik /usr/lib/mapnik

# # FROM mapnik as flask
# # Switch to main work directory
WORKDIR /osm2tactile

# prevent python from writing *.pyc files
ENV PYTHONDONTWRITEBYTECODE 1
# prevent python from buffering stdout and stderr
ENV PYTHONUNBUFFERED 1

# configure poetry
ENV POETRY_VERSION=1.7.1
ENV POETRY_HOME=/opt/poetry

RUN apk upgrade --update && apk add gcc musl-dev libffi-dev

# install poetry
RUN pip install pip --upgrade
RUN pip install poetry==${POETRY_VERSION}
RUN poetry config virtualenvs.create false

# install flask and python dependencies
# We install everything for production here, to help with caching
COPY pyproject.toml pyproject.toml
COPY poetry.lock poetry.lock
RUN poetry install --only main

CMD ["flask", "run"]
