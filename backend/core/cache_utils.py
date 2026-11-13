"""统一缓存工具层。

提供规范的缓存 key、分层 TTL、空值缓存、互斥锁、随机抖动、
版本号失效、gzip 压缩以及 Redis 异常降级等能力。
"""

from __future__ import annotations

import gzip
import hashlib
import json
import logging
import random
from functools import wraps
from typing import Any, Callable, Optional, TypeVar, Union

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

T = TypeVar("T")

# 标记经过 gzip 压缩的值
_GZIP_FLAG = b"\x01"
_EMPTY_VALUE = "__CACHE_EMPTY__"
_VERSION_KEY_TEMPLATE = "{namespace}:version"


def _setting(name: str, default: Any) -> Any:
    cache_settings = getattr(settings, "CACHE_UTILS", {})
    return cache_settings.get(name, getattr(settings, name, default))


def get_default_timeout(level: str = "medium") -> int:
    """根据数据热度返回默认 TTL（秒）。"""
    timeouts = _setting(
        "CACHE_TIMEOUTS",
        {
            "hot": 600,      # 热点只读数据，如列表、对比、统计
            "medium": 300,   # 用户个性化推荐
            "cold": 3600,    # 低频/重计算数据
        },
    )
    return timeouts.get(level, timeouts.get("medium", 300))


def get_namespace_prefix() -> str:
    """返回全局缓存 key 前缀，便于按环境隔离。"""
    return _setting("CACHE_KEY_PREFIX", "campus")


def build_cache_key(namespace: str, *parts: Union[str, int]) -> str:
    """生成规范缓存 key：prefix:namespace:part1:part2...。"""
    prefix = get_namespace_prefix()
    key_parts = [prefix, namespace]
    for part in parts:
        key_parts.append(str(part))
    return ":".join(key_parts)


def _hash_key_part(value: str, length: int = 12) -> str:
    """对较长参数做摘要，避免 key 过长。"""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]


def build_query_cache_key(namespace: str, identifier: str, query_string: str) -> str:
    """为带查询参数的接口生成缓存 key。"""
    return build_cache_key(namespace, identifier, _hash_key_part(query_string))


def _jitter(timeout: int, ratio: float = 0.1) -> int:
    """在 timeout 基础上加入随机抖动，防止缓存雪崩。"""
    if timeout <= 0:
        return timeout
    jitter = max(1, int(timeout * ratio))
    return timeout + random.randint(-jitter, jitter)


def _serialize(value: Any) -> bytes:
    """将 Python 对象序列化为 bytes。"""
    return json.dumps(value, default=str, ensure_ascii=False).encode("utf-8")


def _deserialize(data: bytes) -> Any:
    """将 bytes 反序列化为 Python 对象。"""
    return json.loads(data.decode("utf-8"))


def _compress(data: bytes) -> bytes:
    """gzip 压缩并在头部打标记。"""
    return _GZIP_FLAG + gzip.compress(data)


def _decompress(data: bytes) -> bytes:
    """根据头部标记解压数据。"""
    if data.startswith(_GZIP_FLAG):
        return gzip.decompress(data[len(_GZIP_FLAG):])
    return data


def _should_compress(data: bytes, threshold: int) -> bool:
    return threshold > 0 and len(data) >= threshold


def _encode_for_cache(
    value: Any,
    compress_enabled: bool,
    compress_threshold: int,
) -> bytes:
    raw = _serialize(value)
    if compress_enabled and _should_compress(raw, compress_threshold):
        return _compress(raw)
    return raw


def _decode_from_cache(data: bytes) -> Any:
    return _deserialize(_decompress(data))


def _get_cache_backend():
    """获取当前默认缓存后端，异常时返回 None 用于降级。"""
    try:
        return cache
    except Exception as exc:
        logger.warning(f"获取缓存后端失败: {exc}")
        return None


def _is_redis_backend() -> bool:
    """判断当前缓存后端是否为 django-redis。"""
    try:
        backend = settings.CACHES["default"]["BACKEND"]
        return "django_redis" in backend
    except Exception:
        return False


def _get_namespace_version(namespace: str) -> int:
    """获取命名空间当前版本号。"""
    key = _VERSION_KEY_TEMPLATE.format(namespace=namespace)
    try:
        version = cache.get(key)
        return int(version) if version is not None else 0
    except Exception as exc:
        logger.warning(f"读取缓存版本号失败 [{namespace}]: {exc}")
        return 0


def bump_cache_version(namespace: str) -> None:
    """提升命名空间版本号，使该空间下所有 key 失效。"""
    key = _VERSION_KEY_TEMPLATE.format(namespace=namespace)
    try:
        cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout=None)
    except Exception as exc:
        logger.warning(f"提升缓存版本号失败 [{namespace}]: {exc}")


def invalidate_namespace(namespace: str) -> None:
    """使指定命名空间下所有缓存失效。"""
    bump_cache_version(namespace)
    logger.info(f"缓存命名空间已失效: {namespace}")


def cache_delete(key: str, namespace: Optional[str] = None) -> None:
    """删除单个缓存 key；若提供 namespace 会附加版本号检查。"""
    try:
        cache.delete(key)
    except Exception as exc:
        logger.warning(f"删除缓存失败 [{key}]: {exc}")


def cache_get(
    key: str,
    default: Any = None,
    namespace: Optional[str] = None,
    decompress: bool = True,
    fallback_on_error: bool = True,
) -> Any:
    """读取缓存，支持版本号、解压与异常降级。"""
    try:
        if namespace:
            version = _get_namespace_version(namespace)
            key = f"{key}:v{version}"

        data = cache.get(key)
        if data is None:
            return default

        if decompress and isinstance(data, bytes):
            return _decode_from_cache(data)
        return data
    except Exception as exc:
        if fallback_on_error:
            logger.warning(f"读取缓存失败，降级到 default [{key}]: {exc}")
            return default
        raise


def cache_set(
    key: str,
    value: Any,
    timeout: Optional[int] = None,
    namespace: Optional[str] = None,
    compress: bool = True,
    compress_threshold: int = 1024,
    fallback_on_error: bool = True,
) -> bool:
    """写入缓存，支持压缩、版本号与异常降级。"""
    try:
        if namespace:
            version = _get_namespace_version(namespace)
            key = f"{key}:v{version}"

        if timeout is None:
            timeout = get_default_timeout("medium")

        encoded = _encode_for_cache(value, compress, compress_threshold)
        cache.set(key, encoded, timeout=_jitter(timeout))
        return True
    except Exception as exc:
        if fallback_on_error:
            logger.warning(f"写入缓存失败，已降级 [{key}]: {exc}")
            return False
        raise


def _acquire_lock(lock_key: str, timeout: int) -> Optional[Any]:
    """尝试获取分布式锁，返回锁对象或 None。"""
    if not _is_redis_backend() or timeout <= 0:
        return None
    try:
        # django-redis 原生支持 lock()
        lock = cache.lock(lock_key, expire=timeout)
        if lock.acquire(blocking=False):
            return lock
    except Exception as exc:
        logger.warning(f"获取缓存锁失败 [{lock_key}]: {exc}")
    return None


def _release_lock(lock: Optional[Any]) -> None:
    if lock is None:
        return
    try:
        lock.release()
    except Exception as exc:
        logger.warning(f"释放缓存锁失败: {exc}")


def cached_result(
    key: str,
    loader: Callable[[], T],
    timeout: Optional[int] = None,
    namespace: Optional[str] = None,
    cache_empty: bool = True,
    empty_timeout: Optional[int] = None,
    lock_timeout: int = 10,
    compress: bool = True,
    compress_threshold: int = 1024,
    fallback_on_error: bool = True,
) -> T:
    """带完整保护策略的缓存读取/写入。

    流程：
    1. 先读缓存；命中则直接返回。
    2. 未命中时尝试获取互斥锁，防止缓存击穿。
    3. 拿到锁后再次检查缓存（可能其他线程已回填）。
    4. 执行 loader 计算结果。
    5. 结果为空时可选缓存短时空值，防止缓存穿透。
    6. 回填缓存并返回。
    7. 任何缓存操作异常时，若启用 fallback 则直接执行 loader。
    """
    if timeout is None:
        timeout = get_default_timeout("medium")
    if empty_timeout is None:
        empty_timeout = max(30, timeout // 10)

    versioned_key = key
    try:
        if namespace:
            version = _get_namespace_version(namespace)
            versioned_key = f"{key}:v{version}"

        data = cache.get(versioned_key)
        if data is not None:
            decoded = _decode_from_cache(data) if isinstance(data, bytes) else data
            if decoded == _EMPTY_VALUE:
                return None
            return decoded
    except Exception as exc:
        if fallback_on_error:
            logger.warning(f"读取缓存失败，直接执行 loader [{key}]: {exc}")
            return loader()
        raise

    lock_key = f"{versioned_key}:lock"
    lock = _acquire_lock(lock_key, lock_timeout)

    try:
        if lock:
            # 拿到锁后再次检查，避免重复计算
            try:
                data = cache.get(versioned_key)
                if data is not None:
                    decoded = _decode_from_cache(data) if isinstance(data, bytes) else data
                    if decoded == _EMPTY_VALUE:
                        return None
                    return decoded
            except Exception:
                pass

        result = loader()

        try:
            if result is None and cache_empty:
                cache.set(
                    versioned_key,
                    _encode_for_cache(_EMPTY_VALUE, compress=False, compress_threshold=compress_threshold),
                    timeout=_jitter(empty_timeout),
                )
            elif result is not None:
                encoded = _encode_for_cache(result, compress, compress_threshold)
                cache.set(versioned_key, encoded, timeout=_jitter(timeout))
        except Exception as exc:
            if fallback_on_error:
                logger.warning(f"回填缓存失败 [{key}]: {exc}")
            else:
                raise

        return result
    finally:
        _release_lock(lock)


def cached(
    key_or_builder: Union[str, Callable[..., str]],
    timeout: Optional[int] = None,
    namespace: Optional[str] = None,
    cache_empty: bool = True,
    empty_timeout: Optional[int] = None,
    lock_timeout: int = 10,
    compress: bool = True,
    compress_threshold: int = 1024,
    fallback_on_error: bool = True,
):
    """函数装饰器，自动缓存函数返回结果。

    key_or_builder 可以是固定字符串，也可以是接收函数原参数的 Callable，
    用于根据参数动态生成 key。
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if callable(key_or_builder):
                key = key_or_builder(*args, **kwargs)
            else:
                key = key_or_builder

            return cached_result(
                key=key,
                loader=lambda: func(*args, **kwargs),
                timeout=timeout,
                namespace=namespace,
                cache_empty=cache_empty,
                empty_timeout=empty_timeout,
                lock_timeout=lock_timeout,
                compress=compress,
                compress_threshold=compress_threshold,
                fallback_on_error=fallback_on_error,
            )
        return wrapper
    return decorator
