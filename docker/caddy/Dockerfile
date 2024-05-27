# caddy build stage
FROM caddy:builder-alpine

# Install ratelimit plugin
RUN xcaddy build --with github.com/mholt/caddy-ratelimit

# Fix permissions issue with Caddy image
# - Between version 2.6.2 and 2.6.3 there were some permissions changes on the official images that stopped them from working on OpenShift.
# - This update resolves that permissions issue for OCP.
RUN chown 1001:root /usr/bin/caddy

CMD [ "caddy", "run", "--config", "/etc/caddy/Caddyfile", "--adapter", "caddyfile" ]
