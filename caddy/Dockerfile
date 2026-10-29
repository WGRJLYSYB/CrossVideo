FROM caddy:alpine

RUN apk add --no-cache bash curl socat openssl git tzdata

COPY Caddyfile /etc/caddy/Caddyfile
COPY Caddyfile.bootstrap /etc/caddy/Caddyfile.bootstrap
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["run", "--config", "/etc/caddy/Caddyfile", "--adapter", "caddyfile"]