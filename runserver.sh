#!/bin/bash
sleep 10
python manage.py collectstatic --no-input
python manage.py migrate --no-input
gunicorn --config gunicorn.conf.py canvas_gamification.wsgi:application