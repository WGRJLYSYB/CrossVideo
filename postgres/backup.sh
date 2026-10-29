#!/bin/bash
set -e

# 如果未开启备份，直接退出
if [ "$DB_BACKUP_ENABLED" != "true" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] === 自动数据库云盘备份未启用 ==="
    exit 0
fi

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
# 备份文件名格式：crossvideo_backup_YYYYMMDD_HHMMSS.dump.enc
BACKUP_FILENAME="crossvideo_backup_${TIMESTAMP}.dump.enc"
TMP_DIR="/tmp/pg_backup_tmp"
TMP_RAW_FILE="${TMP_DIR}/backup.dump"
TMP_ENC_FILE="${TMP_DIR}/${BACKUP_FILENAME}"

mkdir -p "$TMP_DIR"

# 捕获退出信号，确保无论备份成功还是失败，都彻底清理容器内部缓存
cleanup() {
    rm -rf "$TMP_DIR"
}
trap cleanup EXIT

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 开始执行数据库备份..."

# 1. 导出 PostgreSQL 二进制格式备份 (-Fc)
PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump \
    -h 127.0.0.1 \
    -U "${POSTGRES_USER:-crossvideo}" \
    -d "${POSTGRES_DB:-crossvideo}" \
    -F c \
    -f "$TMP_RAW_FILE"

# 2. 使用 OpenSSL AES-256-CBC 进行加密，确保云盘端无法直接窥探 SQL/数据
if [ -n "$DB_BACKUP_ENCRYPTION_PASSWORD" ]; then
    openssl enc -aes-256-cbc -pbkdf2 -salt \
        -in "$TMP_RAW_FILE" \
        -out "$TMP_ENC_FILE" \
        -pass pass:"$DB_BACKUP_ENCRYPTION_PASSWORD"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 数据库备份已加密为 AES-256-CBC 格式。"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [警告] 未设置 BACKUP_ENCRYPTION_PASSWORD，跳过加密步骤！"
    mv "$TMP_RAW_FILE" "$TMP_ENC_FILE"
fi

# 3. 使用 Rclone 上传加密备份至 WebDAV 目标目录
REMOTE_PATH="${WEBDAV_REMOTE_NAME:-webdav_remote}:${WEBDAV_BACKUP_DIR:-/crossvideo-backups}"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 正在上传备份到 WebDAV: ${REMOTE_PATH}..."
rclone copy "$TMP_ENC_FILE" "$REMOTE_PATH" --config /root/.config/rclone/rclone.conf

# 4. 清理云盘上超过 30 天的旧备份
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 正在清理远端云盘 30 天前的旧备份..."
rclone delete --min-age 30d "$REMOTE_PATH" --config /root/.config/rclone/rclone.conf

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 数据库备份与同步完成！"