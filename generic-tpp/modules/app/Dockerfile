FROM python:3.8-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /module

RUN apt-get update && apt-get upgrade -y

RUN addgroup --system module_user && adduser --system --group module_user

COPY config/requirements.txt config/requirements.txt
RUN python -m venv venv
RUN venv/bin/python -m pip install -U pip
RUN venv/bin/pip install -r config/requirements.txt

COPY . .

RUN chown -R module_user /module
RUN touch /module/data/analog.json
RUN touch /module/data/discrete.txt
RUN chmod -R 777 /module/data

USER module_user
