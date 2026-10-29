#!/bin/bash
set -e

DB_BACKUP_ENABLED="${DB_BACKUP_ENABLED:-false}"

if [ "$DB_BACKUP_ENABLED" = "true" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] === 自动数据库云盘备份已启用 ==="
    
    WEBDAV_URL="${WEBDAV_URL:?DB_BACKUP_ENABLED 为 true 时必须提供 WEBDAV_URL}"
    WEBDAV_USER="${WEBDAV_USER:?DB_BACKUP_ENABLED 为 true 时必须提供 WEBDAV_USER}"
    WEBDAV_PASSWORD="${WEBDAV_PASSWORD:?DB_BACKUP_ENABLED 为 true 时必须提供 WEBDAV_PASSWORD}"
    
    # 动态生成 rclone 密码混淆串
    OBSCURED_PASS=$(rclone obscure "$WEBDAV_PASSWORD")
    
    # 动态写入 Rclone 配置文件
    mkdir -p /root/.config/rclone
    cat <<EOF > /root/.config/rclone/rclone.conf
[webdav_remote]
type = webdav
url = ${WEBDAV_URL}
vendor = other
user = ${WEBDAV_USER}
pass = ${OBSCURED_PASS}
EOF

    # 配置 Crontab 任务：每天凌晨 3 点 (0 3 * * *) 执行备份，日志输出到标准输出
    CRON_SCHEDULE="${BACKUP_CRON_SCHEDULE:-0 3 * * *}"
    echo "${CRON_SCHEDULE} /opt/backup.sh >> /var/log/backup.log 2>&1" > /etc/crontabs/root
    
    # 在后台启动 Alpine 的 crond 守护进程
    # -b: 后台运行，-l 2: 日志级别为 info，输出到标准输出
    crond -b -l 2
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 已启动 Crond 守护进程，备份计划: ${CRON_SCHEDULE}"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] === 自动数据库云盘备份未启用 (DB_BACKUP_ENABLED!=true) ==="
fi

# 启动官方 postgres 入口点，保留原有的初始化与数据库启动逻辑
exec docker-entrypoint.sh "$@"