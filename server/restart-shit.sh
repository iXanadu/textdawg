#!/bin/bash

systemctl restart celery.service
systemctl restart gunicorn.service
