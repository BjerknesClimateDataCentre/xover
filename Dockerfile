FROM python:3.9-slim-buster

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV TZ=UTC

RUN apt-get update && \
    apt-get install -y netcat  libgeos-c1v5 libgeos-dev binutils \
        libproj-dev gdal-bin python-gdal postgresql-client && \
    apt-get clean

RUN mkdir /app
WORKDIR /app

COPY requirements.txt /app/

RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /app/
RUN chmod 755 /app/entrypoint.sh
ENV PYTHONPATH="/app/d2qc:${PYTHONPATH}"

EXPOSE 8000

CMD ["/app/entrypoint.sh"]
