"""
Elasticsearch 客户端配置。

提供单一入口获取 ES 连接，并封装健康检查与连接异常处理。
"""

import logging

from django.conf import settings
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError as ESConnectionError

logger = logging.getLogger(__name__)

_es_client = None


def get_es_client():
    """获取单例 Elasticsearch 客户端。"""
    global _es_client
    if _es_client is None:
        _es_client = Elasticsearch(
            settings.ELASTICSEARCH_HOSTS,
            timeout=settings.ELASTICSEARCH_TIMEOUT,
            retry_on_timeout=settings.ELASTICSEARCH_RETRY_ON_TIMEOUT,
            max_retries=1,
        )
    return _es_client


def es_is_available():
    """检查 Elasticsearch 是否可用。"""
    try:
        client = get_es_client()
        return client.ping()
    except ESConnectionError:
        return False
    except Exception as exc:
        logger.warning(f"Elasticsearch 健康检查失败: {exc}")
        return False
