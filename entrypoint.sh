#!/bin/bash

cd /django/app || exit 1

python manage.py wait_for_postgres
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
