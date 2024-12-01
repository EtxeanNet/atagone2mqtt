FROM python:3.12 AS build
WORKDIR /app
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

COPY pyproject.toml poetry.lock ./

RUN apt update && apt install -y build-essential
RUN if [ $(dpkg --print-architecture) = "armhf" ]; then \
    printf "[global]\nextra-index-url=https://www.piwheels.org/simple\n" > /etc/pip.conf ; \
    fi
RUN pip install poetry
RUN --mount=type=cache,target=$POETRY_CACHE_DIR poetry install --without dev --no-root

COPY homie.patch ./
RUN patch --verbose  -p0 -i homie.patch

FROM python:3.12-slim AS final
WORKDIR /app
ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1

RUN apt update && apt install -y bluez

COPY --from=build ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY ./atagmqtt atagmqtt

# During debugging, this entry point will be overridden. For more information, refer to https://aka.ms/vscode-docker-python-debug
CMD ["python", "-m", "atagmqtt"]