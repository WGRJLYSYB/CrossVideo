#!/bin/bash
set -e

CADDY_ENABLE_ACME="${CADDY_ENABLE_ACME:-true}"
CADDY_SITE_ADDRESS="${CADDY_SITE_ADDRESS:-}"

ACME_HOME="/data/acme.sh"
CERT_DIR="/data/certs"
EMAIL_CONFIG_FILE="/data/acme_email.txt"

if [ "$CADDY_ENABLE_ACME" = "true" ] && [ -n "$CADDY_SITE_ADDRESS" ]; then
    echo "=== ACME IP证书自动管理已启用 ==="

    # 创建标准目录
    mkdir -p "$ACME_HOME" "$CERT_DIR" /srv/.well-known/acme-challenge

    # 处理邮箱：优先读取环境变量 -> 其次读取持久化文件 -> 最后自动生成并保存
    if [ -n "$CADDY_ACME_EMAIL" ]; then
        ACME_EMAIL="$CADDY_ACME_EMAIL"
    elif [ -f "$EMAIL_CONFIG_FILE" ]; then
        ACME_EMAIL=$(cat "$EMAIL_CONFIG_FILE")
    else
        ACME_EMAIL="admin_$(openssl rand -hex 4)@domain.local"
        echo "$ACME_EMAIL" > "$EMAIL_CONFIG_FILE"
        echo "已自动生成并持久化随机注册邮箱: $ACME_EMAIL"
    fi

    # 1. 干净地初始化 acme.sh
    if [ ! -f "$ACME_HOME/acme.sh" ]; then
        echo "检测到 acme.sh 不存在，正在通过 Git 安装..."
        rm -rf "$ACME_HOME"
        git clone --depth=1 https://github.com/acmesh-official/acme.sh.git "$ACME_HOME"
        "$ACME_HOME"/acme.sh --install -m "$ACME_EMAIL" --home "$ACME_HOME" > /dev/null 2>&1 || true
    fi

    # 2. 首次申请证书判定
    if [ ! -f "$CERT_DIR/fullchain.pem" ]; then
        echo "检测到证书不存在，正在为公网 IP: $CADDY_SITE_ADDRESS 首次申请..."
        
        # 【关键优化】使用 Alpine 自带的轻量级 httpd 专门响应 80 端口验证
        # 彻底避免 Caddy 因为找不到证书而崩溃退出的问题
        httpd -p 80 -h /srv
        HTTPD_PID=$!
        sleep 1

        # 注册与申请
        "$ACME_HOME"/acme.sh --home "$ACME_HOME" --register-account -m "$ACME_EMAIL" > /dev/null 2>&1 || true
        "$ACME_HOME"/acme.sh --home "$ACME_HOME" --issue --server letsencrypt --certificate-profile shortlived \
            -d "$CADDY_SITE_ADDRESS" --webroot /srv

        # 安装证书到持久化目录
        "$ACME_HOME"/acme.sh --home "$ACME_HOME" --install-cert -d "$CADDY_SITE_ADDRESS" --ecc \
            --key-file "$CERT_DIR/privkey.pem" \
            --fullchain-file "$CERT_DIR/fullchain.pem" \
            --reloadcmd "caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile"

        # 关闭临时验证服务器
        kill $HTTPD_PID 2>/dev/null || true
        echo "首次 IP 证书申请并安装成功！"
    fi

    # 3. 后台循环守护：每 12 小时检查一次续期
    (
        while true; do
            sleep 43200
            "$ACME_HOME"/acme.sh --cron --home "$ACME_HOME" > /dev/null 2>&1
        done
    ) &
    echo "后台续期守护进程已启动。"
else
    echo "=== ACME 自动管理未启用或未配置 IP，直接启动标准 Caddy ==="
fi

exec caddy "$@"