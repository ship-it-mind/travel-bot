#!/bin/sh
chmod 666 app.sock
celery worker -A app.celery --loglevel=info

