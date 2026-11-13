FROM nginx:alpine

# 安装 gettext 以使用 envsubst 渲染模板
RUN apk add --no-cache gettext

# 复制 Nginx 配置模板与入口脚本
COPY nginx.prod.conf.template /etc/nginx/conf.d/default.conf.template
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 在容器启动时将模板中的环境变量替换为实际值
ENTRYPOINT ["/entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
