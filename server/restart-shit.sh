#!/bin/bash
#systemctl reload nginx
systemctl restart celery.service
systemctl restart gunicorn.service
