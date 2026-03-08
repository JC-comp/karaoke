#!/bin/sh
exec gunicorn -k gevent -b 0.0.0.0:8000 'server.main:app'