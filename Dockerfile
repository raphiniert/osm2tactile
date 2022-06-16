# syntax=docker/dockerfile:1
FROM python:3.9
ENV PYTHONUNBUFFERED=1
# scons does not yet work with python:3.10

ENV LANG de_AT.UTF-8
ENV LC_ALL de_AT.UTF-8

ENV MAPNIK_VERSION v3.1.0
ENV PYTHON_MAPNIK_BRANCH v3.0.x

ENV BUILD_DEPENDENCIES="build-essential \
    ca-certificates \
    git \
    icu-devtools \
    libboost-dev \
    libboost-filesystem-dev \
    libboost-program-options-dev \
    libboost-regex-dev \
    libboost-thread-dev \
    libboost-system-dev \
    libcairo-dev \
    libfreetype6-dev \
    libgdal-dev \
    libharfbuzz-dev \
    libicu-dev \
    libjpeg-dev \
    libpq-dev  \
    libproj-dev \
    librasterlite2-dev \
    libsqlite3-dev \
    libtiff-dev \
    libwebp-dev"

ENV DEPENDENCIES="libboost-filesystem1.74.0 \
    libboost-program-options1.74.0 \
    libboost-regex1.74.0 \
    libboost-thread1.74.0 \
    libboost-system1.74.0 \
    libcairo2 \
    libfreetype6 \
    libgdal28 \
    libharfbuzz-gobject0 \
    libharfbuzz-icu0 \
    libharfbuzz0b \
    libicu67 \
    libjpeg62-turbo \
    libpq5 \
    libproj19 \
    librasterlite2-1 \
    libsqlite3-0 \
    libtiff5 \
    libtiffxx5 \
    libwebp6  \
    libwebpdemux2 \
    libwebpmux3"

# Switch to main work directory
WORKDIR /srv/osm2tactile

# install and set the locale
RUN apt-get update \
    && apt-get install -y locales \
    && sed -i -e 's/# de_AT.UTF-8 UTF-8/de_AT.UTF-8 UTF-8/' /etc/locale.gen \
    && dpkg-reconfigure --frontend=noninteractive locales

# install mapnik
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        $BUILD_DEPENDENCIES $DEPENDENCIES

RUN git clone https://github.com/mapnik/mapnik.git \
    && cd mapnik \
    && git checkout $MAPNIK_VERSION \
    && git submodule update --init \
    && python scons/scons.py INPUT_PLUGINS='all' \
    && make \
    && make install \
    && cd - \
    && rm -r mapnik

# install mapnik python bindings
RUN apt-get update \
    && apt-get install -y libboost-python-dev
RUN git clone https://github.com/mapnik/python-mapnik.git \
    && cd python-mapnik \
    && git checkout $PYTHON_MAPNIK_BRANCH \
    && export BOOST_PYTHON_LIB=boost_python39 \
    && python setup.py install \
    && cd - \
    && rm -r python-mapnik

# install osm2pgsql
RUN apt-get update \
    && apt-get install -y osm2pgsql

# clean up build dependencies
RUN apt-get autoremove -y --purge $BUILD_DEPENDENCIES \
    && rm -rf /var/lib/apt/lists/* \
    && ln -s /usr/local/lib/mapnik /usr/lib/mapnik

# install flask and python dependencies
COPY requirements.txt requirements.txt
RUN pip install pip --upgrade
RUN pip install -r requirements.txt -v
