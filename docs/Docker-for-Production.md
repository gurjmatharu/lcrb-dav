# Production mode in Docker

This document outlines the steps to get a production-ready instance of the LCRB DAV service running in docker.

## Pre Requisites

- Docker
- A publicly-addressable URL pointing to the port defined by the `AGENT_HTTP_PORT` (8030 by default) on the target machine
- The firewall must allow inbound/outbound traffic on the port defined by the `AGENT_HTTP_PORT` (8030 by default)
- The firewall must allow inbound/outbound traffic on the port defined by the `CONTROLLER_SERVICE_PORT` (5000 by default)
- The firewall must allow outbound traffic on the port range 9700-9799 (this is to allow reading the Indy ledger)

## Getting Started

To get started, follow these steps:

1. Clone the repository on the target machine
2. Open a shell in the `docker` folder. Any shell should work, but a bash shell (such as Git Bash or WSL) is recommended
3. Copy the `.env-example` file to a new file named `.env`: `cp .env-example .env`)
4. Replace the values between angle braces in the `.env` file with values appropriate for your setup. The hard-coded values can be used to further customize the configuration, but they do not need to be changed.
5. Once everything is configured, running `docker compose -f docker-compose-prod.yaml up` should start the services and have them ready to accept requests.
