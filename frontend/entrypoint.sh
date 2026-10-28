#!/bin/sh
set -e

CONFIG_FILE="/usr/share/nginx/html/config.js"

cat > "$CONFIG_FILE" <<EOF
window.__CONFIG__ = {
  SENTRY_DSN: "${VITE_SENTRY_DSN:-}"
};
EOF

echo "Runtime config injected: $CONFIG_FILE"

# 启动 Nginx（原来的 CMD）
exec nginx -g "daemon off;"