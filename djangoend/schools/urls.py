from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from . import views

router = DefaultRouter()
# 先注册子资源路由
router.register(r'majors', views.MajorViewSet)
router.register(r'admission-scores', views.AdmissionScoreViewSet)
router.register(r'forums', views.ForumViewSet)
router.register(r'posts', views.PostViewSet)
router.register(r'comments', views.CommentViewSet)
router.register(r'tags', views.TagViewSet)
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
    path('import_csv/', views.SchoolViewSet.as_view({'post': 'import_csv'}), name='import-csv'),
    
    # 将router.urls放在最后
    path('', include(router.urls)),
] 