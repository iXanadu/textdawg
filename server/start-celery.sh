#!/bin/bash

# Set the Pyenv environment
export PYENV_ROOT="/root/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv virtualenv-init -)"

# Navigate to your Django project directory
cd /root/textdawg

# Set Django settings module
export DJANGO_SETTINGS_MODULE=textDawg.settings

# Start Celery
exec /root/.pyenv/versions/3.12.0/envs/textdawg-3.12.0/bin/celery -A textDawg worker --loglevel=info

