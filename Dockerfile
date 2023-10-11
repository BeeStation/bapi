# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.11-slim-bullseye as base

# Keeps Python from generating .pyc files in the container
# Turns off buffering for easier container logging
# Prevents poetry from creating a virtualenv
ENV PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1 \
	POETRY_VERSION=1.6.1 \
	POETRY_VIRTUALENVS_CREATE=false \
	PYTHONDONTWRITEBYTECODE=1

COPY ["poetry.lock", "pyproject.toml", "./"]

RUN apt-get update && \
    apt-get install -y --no-install-recommends default-libmysqlclient-dev gcc git && \
    pip install "poetry==$POETRY_VERSION"

# Install pip requirements

RUN poetry install --without=dev --no-root --no-interaction --no-ansi

RUN apt-get autoremove gcc git --purge -y && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /root/.cache

COPY server-conf/bapi_uwsgi.ini /etc/uwsgi/uwsgi.ini

FROM base as final
WORKDIR /app
COPY /src /app

RUN chown -R www-data:www-data /app

USER www-data:www-data

EXPOSE 8081

CMD ["/usr/local/bin/uwsgi", "--ini", "/etc/uwsgi/uwsgi.ini"]
