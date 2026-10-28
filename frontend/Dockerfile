# 阶段一：构建前端静态资源
FROM node:24-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# 阶段二：使用极轻量的 Nginx 托管静态文件 (总镜像体积通常小于 25MB)
FROM nginx:alpine

# 【新增】将自定义的 Nginx 配置文件复制到配置目录中
COPY default.conf /etc/nginx/conf.d/default.conf
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 将构建产物复制到 Nginx 默认托管目录
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80
ENTRYPOINT ["/entrypoint.sh"]