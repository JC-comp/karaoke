FROM apache/airflow:slim-3.1.7 AS build
USER root
RUN apt update && apt install -y \
    pkg-config build-essential libmariadb-dev-compat mariadb-client \
    && rm -rf /var/lib/apt/lists/*

USER airflow

RUN cp -r /home/airflow/.local /tmp/backup

RUN pip --no-cache-dir install apache-airflow-providers-mysql \
    apache-airflow-providers-celery apache-airflow-providers-fab apache-airflow-providers-http

RUN rsync -a --compare-dest=/tmp/backup /home/airflow/.local /tmp/.local

FROM apache/airflow:slim-3.1.7

COPY --from=build /tmp/.local /home/airflow/
