import json
from channels.generic.websocket import AsyncWebsocketConsumer
import logging
from .views import online_users
from asgiref.sync import sync_to_async
from datetime import datetime
from users.notifications import Notification
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
        
        # 接受连接，但记录更明确的认证状态
        await self.accept()
        
        if self.user.is_authenticated:
            logger.info(f"已认证用户已连接: {self.user.username} (ID: {self.user.id})")
            # 添加到在线用户列表
            await sync_to_async(online_users.add)(self.user.id)
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
        
        # 获取在线用户数量
        online_count = await sync_to_async(len)(online_users)
        
        # 发送欢迎消息和在线用户数量
        await self.send(text_data=json.dumps({
            'type': 'welcome',
            'message': "欢迎来到聊天室！",
            'time': datetime.now().isoformat(),
            'online_users': {
                'count': online_count or 1
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
        
        # 从在线用户列表中移除
        if hasattr(self, 'user') and self.user.is_authenticated:
            await sync_to_async(online_users.discard)(self.user.id)
            logger.info(f"用户 {self.user.username} (ID: {self.user.id}) 已从在线列表移除")
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
        
        # 广播在线用户更新
        online_count = await sync_to_async(len)(online_users)
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

    async def online_users_update(self, event):
        """当在线用户数量变化时，发送给WebSocket客户端"""
        await self.send(text_data=json.dumps({
            'type': 'online_users',
            'count': event['count'],
            'time': datetime.now().isoformat()
        }))
        
    async def notification(self, event):
        """当收到通知时，发送给WebSocket客户端"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': event['notification'],
            'time': event.get('time', datetime.now().isoformat())
        }))
        
    async def unread_notifications_update(self, event):
        """当未读通知数量变化时，发送给WebSocket客户端"""
        await self.send(text_data=json.dumps({
            'type': 'unread_notifications',
            'count': event['count'],
            'time': datetime.now().isoformat()
        })) 