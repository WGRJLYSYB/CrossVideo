FROM postgres:16-alpine

# 安装 rclone, openssl (加密用), tzdata (时区) 和 supercronic/crond
RUN apk add --no-cache \
    bash \
    curl \
    openssl \
    ca-certificates \
    tzdata \
    rclone

# 创建备份与配置工作目录
RUN mkdir -p /opt/backup /root/.config/rclone

# 复制启动脚本与备份脚本
COPY entrypoint.sh /usr/local/bin/custom-entrypoint.sh
COPY backup.sh /opt/backup.sh

RUN chmod +x /usr/local/bin/custom-entrypoint.sh /opt/backup.sh

ENTRYPOINT ["custom-entrypoint.sh"]
CMD ["postgres"]