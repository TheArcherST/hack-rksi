FROM python:3.12

SHELL ["/bin/bash", "-c"]
WORKDIR /usr/src/app

RUN apt-get update
RUN apt-get install -y netcat-traditional dnsutils

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN python -m venv .venv

ENV ORIGINAL_PATH=$PATH
ENV VIRTUAL_ENV=/usr/src/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN pip install poetry

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root --compile

COPY . .
RUN poetry install --only-root --compile
