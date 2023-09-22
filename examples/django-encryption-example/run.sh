#!/bin/sh
set -euo pipefail
IFS=$'\n\t'

shopt -s expand_aliases

# Random string.
DOCKER_TAG=1.8.3

# Deletes container if exists.
docker rm -f pvault-server

echo "Starting Vault"
docker run --rm --init \
       --name pvault-server \
       -p 8123:8123 \
       -e PVAULT_SERVICE_LICENSE=${PVAULT_SERVICE_LICENSE} \
       -d \
       piiano/pvault-dev:${DOCKER_TAG}

alias pvault="docker run --rm -i --add-host='host.docker.internal:host-gateway' -v $(pwd):/pwd -w /pwd piiano/pvault-cli:${DOCKER_TAG}"

until pvault status > /dev/null 2>&1
do echo "Waiting for the vault to start ..." && sleep 1; done

pvault version
cp ./vault_sample_django/local_settings_example.py ./vault_sample_django/local_settings.py

pip install django-encryption

echo "Run migration"
python3 manage.py migrate
python3 manage.py generate_vault_migration > vault_migration.py
python3 vault_migration.py

echo "Run app server"
python3 manage.py runserver &

echo "Adding customer"
python3 add_customer_example.py
