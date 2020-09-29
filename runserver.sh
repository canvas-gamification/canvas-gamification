#!/bin/bash
sleep 10
python manage.py collectstatic --no-input
python manage.py migrate --no-input
python manage.py runserver 0.0.0.0:8000