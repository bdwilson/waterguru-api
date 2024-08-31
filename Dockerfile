#!/bin/bash
FROM amd64/python:3.9-slim-buster
ENV TZ=America/New_York
ENV WG_USER=''
ENV WG_PASS=''

ARG WG_PORT=53255

RUN mkdir /code
WORKDIR /code

RUN apt-get update -y && \
    apt-get install -y gcc git && \
	git clone https://github.com/pysanders/waterguru-api && \
    pip install -r /code/waterguru-api/requirements.txt && \
	sed -i "s/WG_PORT/${WG_PORT}/" /code/waterguru-api/waterguru_flask.py && \
	ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

#ADD . /code/
EXPOSE ${WG_PORT}
CMD [ "python3.9", "/code/waterguru-api/waterguru_flask.py" ]