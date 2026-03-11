from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    UserViewSet, UserProfileViewSet, debug_avatar, 
    test_static_file, list_avatar_files, test_html_media
)
from .favorites_views import FavoriteViewSet
from .notifications_views import NotificationViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'profiles', UserProfileViewSet, basename='profile')
router.register(r'favorites', FavoriteViewSet, basename='favorite')
router.register(r'notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
    path('email-code/', UserViewSet.as_view({'post': 'send_email_code'}), name='email-code'),
    path('phone-code/', UserViewSet.as_view({'post': 'send_phone_code'}), name='phone-code'),
    path('verify-code/', UserViewSet.as_view({'post': 'verify_code'}), name='verify-code'),
    path('email-code-login/', UserViewSet.as_view({'post': 'email_code_login'}), name='email-code-login'),
    path('phone-code-login/', UserViewSet.as_view({'post': 'phone_code_login'}), name='phone-code-login'),
    path('reset-password/', UserViewSet.as_view({'post': 'reset_password'}), name='reset-password'),
    path('debug-avatar/', debug_avatar, name='debug-avatar'),
    path('test-static/', test_static_file, name='test-static'),
    path('list-avatars/', list_avatar_files, name='list-avatars'),
    path('test-html-media/', test_html_media, name='test-html-media'),
]