from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
# 先注册子资源路由
router.register(r'majors', views.MajorViewSet)
router.register(r'admission-scores', views.AdmissionScoreViewSet)
router.register(r'events', views.EventViewSet)
router.register(r'event-registrations', views.EventRegistrationViewSet)
router.register(r'explore', views.ExploreViewSet, basename='explore')
# 最后注册根路径视图集
router.register(r'', views.SchoolViewSet)

urlpatterns = [
    # 添加新的API路由（放在router.urls之前）
    path('test-connection/', views.test_connection, name='test-connection'),
    path('provinces/', views.get_provinces, name='provinces-list'),
    path('cities/', views.get_cities, name='cities-list'),
    path('types/', views.get_school_types, name='school-types'),
    path('levels/', views.get_school_levels, name='school-levels'),
    path('major-types/', views.get_major_types, name='major-types'),
    path('subject-categories/', views.get_subject_categories, name='subject-categories'),
    path('favorite-schools/', views.get_favorite_schools, name='favorite-schools'),
    path('log-activity/', views.log_user_activity, name='log-user-activity'),
    path('recommendations/', views.get_recommendations, name='recommendations'),
    path('import_csv/', views.SchoolViewSet.as_view({'post': 'import_csv'}), name='import-csv'),
    path('stats/school/', views.get_school_stats, name='school-stats'),
    path('stats/forum/', views.get_forum_stats, name='forum-stats'),
    path('stats/event/', views.get_event_stats, name='event-stats'),
    path('stats/user/', views.get_user_stats, name='user-stats'),
    path('stats/dashboard/', views.get_dashboard_stats, name='dashboard-stats'),
    
    # 将router.urls放在最后
    path('', include(router.urls)),
] 