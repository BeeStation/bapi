# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.11-alpine as base

# Keeps Python from generating .pyc files in the container
# Turns off buffering for easier container logging
# Prevents poetry from creating a virtualenv
ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1 \
	POETRY_VERSION=1.7.1 \
	POETRY_VIRTUALENVS_CREATE=false \
	PYTHONDONTWRITEBYTECODE=1

COPY ["poetry.lock", "pyproject.toml", "./"]

RUN apk add --no-cache mariadb-dev \
    && apk add --no-cache --virtual build-dependencies gcc git libc-dev linux-headers \
    && pip install --no-cache-dir "poetry==$POETRY_VERSION"

# Install pip requirements

RUN poetry install --without=dev --no-root --no-interaction --no-ansi \
    && apk del --purge build-dependencies

COPY server-conf/bapi_uwsgi.ini /etc/uwsgi/uwsgi.ini

WORKDIR /app
COPY /src /app

RUN adduser -u 82 -D -S -G www-data www-data \
    && chown -R www-data:www-data /app

USER www-data:www-data

EXPOSE 8080

CMD ["/usr/local/bin/uwsgi", "--ini", "/etc/uwsgi/uwsgi.ini"]
