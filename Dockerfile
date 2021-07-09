FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN mkdir -p /app
WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY app /app

