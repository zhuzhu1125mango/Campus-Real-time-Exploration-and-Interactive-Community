import json
from channels.generic.websocket import AsyncWebsocketConsumer
import logging
from .views import presence
from asgiref.sync import sync_to_async
from datetime import datetime
from users.notifications import Notification
from users.friendship import Friend
from users.messages import Message
from users.notification_sender import send_notification_to_user
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger(__name__)

# 改进版ChatConsumer
class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = "chat"
        self.user = self.scope["user"]

        # 增强连接日志
        logger.info(f"新WebSocket连接请求: {self.channel_name}")
        logger.info(f"用户认证状态: {self.user.is_authenticated}")

        # 公共聊天室要求用户必须登录
        if not self.user.is_authenticated:
            logger.warning("未认证用户尝试连接公共聊天室，拒绝连接")
            await self.close(code=4001)
            return

        # 将消费者添加到聊天室组
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # 如果用户已认证，添加到用户特定的通知组
        if self.user.is_authenticated:
            self.user_group_name = f"user_{self.user.id}"
            await self.channel_layer.group_add(
                self.user_group_name,
                self.channel_name
            )
            logger.info(f"用户 {self.user.username} (ID: {self.user.id}) 已添加到通知组 {self.user_group_name}")

        # 接受连接；若客户端声明了 jwt 子协议则选择该子协议
        subprotocol = self._select_subprotocol()
        await self.accept(subprotocol=subprotocol)
        
        if self.user.is_authenticated:
            logger.info(f"已认证用户已连接: {self.user.username} (ID: {self.user.id})")
            # 标记用户为活跃（基于 Redis 的最近活跃统计）
            await sync_to_async(presence.mark_active)(self.user.id)
            # 发送认证成功消息
            await self.send(text_data=json.dumps({
                'type': 'auth_success',
                'message': "身份验证成功，欢迎回来！",
                'user': {
                    'id': self.user.id,
                    'username': self.user.username
                }
            }))
            # 发送未读通知数量
            unread_count = await sync_to_async(Notification.get_unread_count)(self.user)
            await self.send(text_data=json.dumps({
                'type': 'unread_notifications',
                'count': unread_count
            }))
        else:
            logger.info(f"未认证用户已连接: {self.channel_name}")
            # 虽然允许未认证用户连接，但发送警告信息
            await self.send(text_data=json.dumps({
                'type': 'auth_warning',
                'message': "您尚未登录，部分功能可能受限。"
            }))

        # 获取最近活跃用户数量
        online_count = await sync_to_async(presence.count)()

        # 发送欢迎消息和在线用户数量
        await self.send(text_data=json.dumps({
            'type': 'welcome',
            'message': "欢迎来到聊天室！",
            'time': datetime.now().isoformat(),
            'online_users': {
                'count': online_count or 1,
                'metric': 'recently_active'
            }
        }))

        # 广播在线用户更新
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'online_users_update',
                'count': online_count or 1
            }
        )

    async def disconnect(self, close_code):
        logger.info(f"断开WebSocket连接: {self.channel_name}, 代码: {close_code}")

        # 基于"最近活跃"统计，断开时不立即移除用户；
        # 用户会在 WINDOW_SECONDS 窗口过期后自动从在线统计中下线。
        # 这种设计对多标签页更友好，也避免连接异常断开导致统计抖动。
        if hasattr(self, 'user') and self.user.is_authenticated:
            logger.info(f"用户 {self.user.username} (ID: {self.user.id}) 连接断开")
            # 从用户特定的通知组中移除
            if hasattr(self, 'user_group_name'):
                await self.channel_layer.group_discard(
                    self.user_group_name,
                    self.channel_name
                )
                logger.info(f"用户 {self.user.username} (ID: {self.user.id}) 已从通知组中移除")

        # 从群组中移除
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        # 广播在线用户更新（基于最近活跃统计）
        online_count = await sync_to_async(presence.count)()
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'online_users_update',
                'count': online_count or 0
            }
        )

    async def receive(self, text_data):
        logger.info(f"接收消息: {text_data[:100]}..." if len(text_data) > 100 else f"接收消息: {text_data}")
        
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'unknown')
            
            # 处理心跳消息
            if message_type == 'heartbeat':
                if self.user.is_authenticated:
                    await sync_to_async(presence.mark_active)(self.user.id)
                await self.send(text_data=json.dumps({
                    'type': 'heartbeat_response',
                    'timestamp': data.get('timestamp', 0)
                }))
                return
            
            # 处理聊天消息 - 增加验证和安全检查
            if message_type == 'chat_message':
                content = data.get('message', '').strip()
                
                # 内容验证
                if not content:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': '消息内容不能为空'
                    }))
                    return
                
                # 消息长度限制 (1000字符)
                if len(content) > 1000:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': '消息内容过长，请限制在1000字符以内'
                    }))
                    return
                
                # 构建用户信息
                if self.user.is_authenticated:
                    username = self.user.username
                    user_id = self.user.id
                    
                    # 增加头像支持
                    avatar = None
                    if hasattr(self.user, 'avatar') and self.user.avatar:
                        try:
                            avatar = self.user.avatar.url
                        except Exception:
                            avatar = None
                else:
                    username = "游客"
                    user_id = 0
                    avatar = None
                
                current_time = datetime.now().isoformat()

                # 发消息时刷新用户活跃时间
                if self.user.is_authenticated:
                    await sync_to_async(presence.mark_active)(self.user.id)

                # 持久化到数据库，便于历史消息查询
                from .models import ChatMessage
                try:
                    await sync_to_async(ChatMessage.objects.create)(
                        user=self.user,
                        content=content
                    )
                    logger.info(f"公共聊天室消息已持久化: {content[:50]}")
                except Exception as e:
                    logger.error(f"公共聊天室消息持久化失败: {e}")

                # 广播消息给所有连接的客户端
                logger.info(f"广播消息给所有连接的客户端: {content}")
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': content,
                        'username': username,
                        'user_id': user_id,
                        'avatar': avatar,
                        'time': current_time,
                        'client_id': data.get('client_id')
                    }
                )
                logger.info("消息广播完成")
                
                # 确认消息已收到
                await self.send(text_data=json.dumps({
                    'type': 'message_received',
                    'message': f"已收到并广播消息",
                    'time': current_time
                }))
                return
            
            # 处理通知相关消息
            if message_type == 'mark_notification_read':
                if not self.user.is_authenticated:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': '请先登录'
                    }))
                    return
                
                notification_id = data.get('notification_id')
                if not notification_id:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': '通知ID不能为空'
                    }))
                    return
                
                try:
                    notification = await sync_to_async(Notification.objects.get)(
                        id=notification_id,
                        recipient=self.user
                    )
                    await sync_to_async(notification.mark_as_read)()
                    await self.send(text_data=json.dumps({
                        'type': 'notification_marked_read',
                        'notification_id': notification_id
                    }))
                except Notification.DoesNotExist:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': '通知不存在'
                    }))
                return
            
            if message_type == 'mark_all_notifications_read':
                if not self.user.is_authenticated:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': '请先登录'
                    }))
                    return
                
                await sync_to_async(Notification.mark_all_as_read)(self.user)
                await self.send(text_data=json.dumps({
                    'type': 'all_notifications_marked_read'
                }))
                return
            
            # 其他类型的消息
            await self.send(text_data=json.dumps({
                'type': 'message_received',
                'message': f"已收到{message_type}类型消息",
                'time': datetime.now().isoformat()
            }))
            
        except json.JSONDecodeError:
            logger.error("接收到无效的JSON数据")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': '无效的消息格式',
                'time': datetime.now().isoformat()
            }))
        except Exception as e:
            logger.error(f"处理消息时出错: {str(e)}", exc_info=True)
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'服务器错误: {str(e)}',
                'time': datetime.now().isoformat()
            }))

    async def chat_message(self, event):
        """当收到群组消息时，发送给WebSocket客户端"""
        try:
            logger.info(f"发送消息给客户端: {event['message']}")
            await self.send(text_data=json.dumps({
                'type': 'chat_message',
                'message': event['message'],
                'username': event.get('username', '未知用户'),
                'user_id': event.get('user_id', 0),
                'avatar': event.get('avatar'),
                'time': event.get('time', datetime.now().isoformat())
            }))
            logger.info("消息发送完成")
        except RuntimeError as e:
            logger.debug(f"无法发送消息到已关闭的连接: {e}")

    async def online_users_update(self, event):
        """当在线用户数量变化时，发送给WebSocket客户端"""
        try:
            await self.send(text_data=json.dumps({
                'type': 'online_users',
                'count': event['count'],
                'time': datetime.now().isoformat()
            }))
        except RuntimeError as e:
            logger.debug(f"无法发送在线用户更新到已关闭的连接: {e}")
        
    def _select_subprotocol(self):
        """从客户端声明的子协议中选择 jwt 子协议（若存在）。"""
        subprotocols = self.scope.get('subprotocols', [])
        for protocol in subprotocols:
            if protocol and protocol.lower() == 'jwt':
                return 'jwt'
        return None

    async def notification(self, event):
        """当收到通知时，发送给WebSocket客户端"""
        try:
            await self.send(text_data=json.dumps({
                'type': 'notification',
                'notification': event['notification'],
                'time': event.get('time', datetime.now().isoformat())
            }))
        except RuntimeError as e:
            logger.debug(f"无法发送通知到已关闭的连接: {e}")

    async def unread_notifications_update(self, event):
        """当未读通知数量变化时，发送给WebSocket客户端"""
        try:
            await self.send(text_data=json.dumps({
                'type': 'unread_notifications',
                'count': event['count'],
                'time': datetime.now().isoformat()
            }))
        except RuntimeError as e:
            logger.debug(f"无法发送未读通知更新到已关闭的连接: {e}")


class PrivateChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.target_user_id = self.scope['url_route']['kwargs'].get('user_id')
        
        logger.info(f"新私聊WebSocket连接请求: {self.channel_name}")
        logger.info(f"用户认证状态: {self.user.is_authenticated}")
        logger.info(f"目标用户ID: {self.target_user_id}")
        
        if not self.user.is_authenticated:
            logger.warning("未认证用户尝试连接私聊")
            await self.close(code=4001)
            return
            
        if not self.target_user_id:
            logger.warning("缺少目标用户ID")
            await self.close(code=4002)
            return

        # 校验目标用户是否存在
        try:
            self.target_user = await sync_to_async(User.objects.get)(id=self.target_user_id)
        except User.DoesNotExist:
            logger.warning(f"目标用户不存在: {self.target_user_id}")
            await self.close(code=4004)
            return

        # 校验双方是否为好友关系（防止陌生人私聊）
        is_friend = await sync_to_async(Friend.is_friend)(self.user, self.target_user)
        if not is_friend:
            logger.warning(f"用户 {self.user.id} 与用户 {self.target_user_id} 不是好友，拒绝私聊连接")
            await self.close(code=4003)
            return

        # 创建私聊组名（按用户ID排序，确保双方加入同一个组）
        user_ids = sorted([str(self.user.id), str(self.target_user_id)])
        self.room_group_name = f"private_chat_{user_ids[0]}_{user_ids[1]}"
        
        # 将消费者添加到私聊组
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # 接受连接；若客户端声明了 jwt 子协议则选择该子协议
        subprotocol = self._select_subprotocol()
        await self.accept(subprotocol=subprotocol)
        logger.info(f"私聊连接已接受: 用户 {self.user.username} (ID: {self.user.id}) 与用户 {self.target_user_id}")
        
        await self.send(text_data=json.dumps({
            'type': 'private_chat_ready',
            'message': "私聊连接已建立",
            'target_user_id': self.target_user_id,
            'time': datetime.now().isoformat()
        }))

    async def disconnect(self, close_code):
        logger.info(f"私聊WebSocket断开连接: {self.channel_name}, 代码: {close_code}")
        
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            logger.info(f"用户 {self.user.username} 已从私聊组 {self.room_group_name} 移除")

    async def receive(self, text_data):
        logger.info(f"私聊接收消息: {text_data[:100]}..." if len(text_data) > 100 else f"私聊接收消息: {text_data}")
        
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'unknown')
            
            if message_type == 'heartbeat':
                await self.send(text_data=json.dumps({
                    'type': 'heartbeat_response',
                    'timestamp': data.get('timestamp', 0)
                }))
                return
                
            if message_type == 'private_message':
                content = data.get('content', '').strip()

                if not content:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': '消息内容不能为空'
                    }))
                    return

                if len(content) > 1000:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': '消息内容过长，请限制在1000字符以内'
                    }))
                    return

                # 持久化到数据库，确保 WebSocket 直发也不会丢失消息
                message = await sync_to_async(Message.objects.create)(
                    sender=self.user,
                    receiver=self.target_user,
                    content=content
                )

                avatar = None
                if hasattr(self.user, 'avatar') and self.user.avatar:
                    try:
                        avatar = self.user.avatar.url
                    except Exception:
                        avatar = None

                created_at = message.created_at.isoformat()

                # 广播消息给私聊组的所有成员
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'private_message',
                        'id': message.id,
                        'content': content,
                        'sender_id': self.user.id,
                        'sender_username': self.user.username,
                        'sender_avatar': avatar,
                        'receiver_id': self.target_user_id,
                        'receiver_username': await self.get_receiver_username(),
                        'is_read': False,
                        'created_at': created_at
                    }
                )

                # 发送私信通知给接收者
                await sync_to_async(send_notification_to_user)(
                    self.target_user,
                    '新私信',
                    f'{self.user.username} 给您发送了一条私信',
                    'message',
                    f'/chat/{self.user.id}'
                )

                await self.send(text_data=json.dumps({
                    'type': 'message_received',
                    'message': "消息已发送",
                    'time': created_at
                }))
                return
                
        except json.JSONDecodeError:
            logger.error("私聊接收到无效的JSON数据")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': '无效的消息格式',
                'time': datetime.now().isoformat()
            }))
        except Exception as e:
            logger.error(f"私聊处理消息时出错: {str(e)}", exc_info=True)
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'服务器错误: {str(e)}',
                'time': datetime.now().isoformat()
            }))

    async def private_message(self, event):
        """发送私聊消息给客户端"""
        try:
            logger.info(f"发送私聊消息: {event['content']}")
            await self.send(text_data=json.dumps({
                'type': 'private_message',
                'id': event.get('id'),
                'content': event.get('content'),
                'sender_id': event.get('sender_id'),
                'sender_username': event.get('sender_username'),
                'sender_avatar': event.get('sender_avatar'),
                'receiver_id': event.get('receiver_id'),
                'receiver_username': event.get('receiver_username'),
                'is_read': event.get('is_read', False),
                'created_at': event.get('created_at', datetime.now().isoformat())
            }))
        except RuntimeError as e:
            logger.debug(f"无法发送私聊消息到已关闭的连接: {e}")

    def _select_subprotocol(self):
        """从客户端声明的子协议中选择 jwt 子协议（若存在）。"""
        subprotocols = self.scope.get('subprotocols', [])
        for protocol in subprotocols:
            if protocol and protocol.lower() == 'jwt':
                return 'jwt'
        return None

    async def get_receiver_username(self):
        """获取接收者用户名"""
        try:
            receiver = await sync_to_async(User.objects.get)(id=self.target_user_id)
            return receiver.username
        except User.DoesNotExist:
            return "未知用户" 