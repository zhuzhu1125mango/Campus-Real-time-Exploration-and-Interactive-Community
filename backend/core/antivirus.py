"""上传文件病毒扫描（ClamAV clamd INSTREAM 协议）。

默认关闭，避免开发环境强依赖 ClamAV。生产环境建议：

    ANTIVIRUS_ENABLED=True
    CLAMAV_HOST=clamav
    CLAMAV_PORT=3310

启用后采用 fail-closed 策略：扫描发现病毒或扫描服务不可用时均拒绝上传。
"""

import logging
import socket
import struct

from django.conf import settings
from rest_framework import serializers

logger = logging.getLogger(__name__)

CHUNK_SIZE = 64 * 1024


class VirusScanError(Exception):
    """文件中检测到恶意内容。"""


class VirusScanUnavailable(Exception):
    """扫描服务不可用，无法确认文件安全。"""


def _read_response(sock):
    """读取 clamd 以 NUL 结尾的响应。"""
    chunks = []
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        chunks.append(chunk)
        if chunk.endswith(b'\0'):
            break
    return b''.join(chunks)


def scan_stream(fileobj):
    """将文件流送入 clamd 扫描。

    未启用时直接返回；发现病毒抛出 ``VirusScanError``，
    服务异常抛出 ``VirusScanUnavailable``。
    """
    if not getattr(settings, 'ANTIVIRUS_ENABLED', False):
        return

    host = getattr(settings, 'CLAMAV_HOST', 'clamav')
    port = int(getattr(settings, 'CLAMAV_PORT', 3310))
    timeout = int(getattr(settings, 'CLAMAV_TIMEOUT', 10))

    try:
        fileobj.seek(0)
    except (AttributeError, OSError):
        pass

    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            sock.sendall(b'zINSTREAM\0')
            while True:
                chunk = fileobj.read(CHUNK_SIZE)
                if not chunk:
                    break
                sock.sendall(struct.pack('!I', len(chunk)))
                sock.sendall(chunk)
            sock.sendall(struct.pack('!I', 0))
            response = _read_response(sock)
    except (OSError, socket.timeout) as exc:
        logger.error('病毒扫描服务不可用: %s', exc)
        raise VirusScanUnavailable('病毒扫描服务不可用') from exc
    finally:
        try:
            fileobj.seek(0)
        except (AttributeError, OSError):
            pass

    if b'FOUND' in response:
        signature = response.decode('utf-8', errors='ignore').strip('\0').strip()
        logger.warning('检测到恶意文件: %s', signature)
        raise VirusScanError(signature)
    if b'OK' not in response:
        logger.error('病毒扫描返回未知结果: %r', response)
        raise VirusScanUnavailable('病毒扫描返回异常结果')


def validate_upload(fileobj):
    """DRF 序列化器/视图使用的上传校验入口。"""
    if not fileobj:
        return fileobj
    try:
        scan_stream(fileobj)
    except VirusScanError:
        raise serializers.ValidationError('文件未通过病毒扫描')
    except VirusScanUnavailable:
        raise serializers.ValidationError('病毒扫描服务暂不可用，请稍后重试')
    return fileobj
