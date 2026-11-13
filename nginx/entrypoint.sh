#!/bin/sh
set -e

# 使用 envsubst 将模板中的变量替换为实际值，生成最终 Nginx 配置
envsubst '$PROD_DOMAIN $SSL_CERT_PATH $SSL_KEY_PATH' \
    < /etc/nginx/conf.d/default.conf.template \
    > /etc/nginx/conf.d/default.conf

# 继续执行 CMD（默认启动 nginx）
exec "$@"
