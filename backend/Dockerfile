# 校园社区后端基础镜像
# 同时支持 HTTP API、WebSocket、Celery Worker 三种启动方式

FROM python:3.12-slim

WORKDIR /app

# 安装系统依赖（MySQL 客户端编译依赖、GCC 等）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    pkg-config \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv
RUN pip install --no-cache-dir uv

# 复制依赖文件并安装（包含生产环境依赖）
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --extra prod

# 复制项目代码并赋予启动脚本执行权限
COPY . .
RUN chmod +x scripts/*.sh

# 暴露端口（HTTP 与 WS 运行时由启动命令决定）
EXPOSE 8000 8001
