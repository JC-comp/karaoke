FROM alpine:3.18.3

ENV PYTHONPATH=/app/web_server/

RUN apk add --no-cache \
    python3 py-pip

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN chmod 755 entrypoint.sh

RUN adduser -D web

USER web

ENTRYPOINT ["./entrypoint.sh"]