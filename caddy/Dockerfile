FROM caddy:alpine

RUN apk add --no-cache bash curl socat openssl

RUN curl https://get.acme.sh | sh -s -- --home /data/acme.sh --email placeholder@example.com

COPY Caddyfile /etc/caddy/Caddyfile
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["run", "--config", "/etc/caddy/Caddyfile", "--adapter", "caddyfile"]