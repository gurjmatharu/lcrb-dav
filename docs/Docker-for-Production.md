# Production mode in Docker

This document outlines the steps to get a production-ready instance of the LCRB DAV service running in docker.

Once running, the project will expose a service on ports `80` and `443`.

## Pre Requisites

- Docker
- A publicly-addressable URL pointing to the target machine.
- The firewall must allow inbound/outbound traffic on the ports `80` (http) and `443` (https).
- The firewall must allow outbound traffic on the port range 9700-9799 (this is to allow reading the Indy ledger)

## Getting Started

To get started, follow these steps:

1. Clone the repository on the target machine
2. Open a shell in the `docker` folder. Any shell should work, but a bash shell (such as Git Bash or WSL) is recommended
3. Copy the `.env-example` file to a new file named `.env`: `cp .env-example .env`
4. Replace the values between angle braces in the `.env` file with values appropriate for your setup. The hard-coded values can be used to further customize the configuration, but they do not need to be changed. Remember to remove the braces when setting new values.
5. Once everything is configured, running `docker compose -f docker-compose-prod.yaml up --build -d` should start the services and have them ready to accept requests.

The application will be available at `https://your-domain.test/dav/`.

A new `certs` folder holding the SSL certificates for the service will be created in the `docker/caddy` folder.

## Resetting the environment

To start from scratch and delete all existing containers and volumes, run the following command:
`docker compose -f docker-compose-prod.yaml down -v`

## Production CA Authority

By default, the project is set-up to use LetsEncrypt Staging to obtain SSL certificates: when ready to run in production mode, uncomment the line specifying `CA_ENDPOINT` in the `.env` file and restart your services.
