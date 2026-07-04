from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'messages', views.ChatMessageViewSet)

urlpatterns = [
    path('health/', views.health, name='health'),
    path('messages/recent_messages/', views.recent_messages, name='recent_messages'),
    path('messages/online_users/', views.get_online_users, name='online_users'),
    path('send_message/', views.send_message, name='send_message'),
    path('', include(router.urls)),
] 