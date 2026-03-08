FROM ktv-airflow-init:latest AS build

USER root

RUN apt update && apt install -y --no-install-recommends --no-install-suggests \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN cp -r /home/airflow/.local /tmp/backup

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

# Copy daemon script
COPY daemon /app/daemon/

# Copy custom script
COPY pre-entrypoint.sh /usr/local/bin/pre-entrypoint.sh
RUN chmod +x /usr/local/bin/pre-entrypoint.sh
USER airflow

# New ENTRYPOINT structure
ENTRYPOINT ["/usr/local/bin/pre-entrypoint.sh", "/usr/bin/dumb-init", "--", "/entrypoint"]