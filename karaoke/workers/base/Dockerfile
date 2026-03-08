FROM ktv-airflow-init:latest AS build

USER root

RUN apt update && apt install -y --no-install-recommends --no-install-suggests \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN cp -r /home/airflow/.local /tmp/backup

RUN apt update && apt install -y --no-install-recommends --no-install-suggests \
    portaudio19-dev xz-utils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
USER airflow
RUN pip install -r /tmp/requirements.txt
RUN rsync -a --compare-dest=/tmp/backup /home/airflow/.local /tmp/.local

FROM ktv-airflow-init:latest

USER root
RUN apt update && apt install -y --no-install-recommends --no-install-suggests \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY --from=build /tmp/.local /home/airflow
USER airflow