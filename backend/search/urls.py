from django.urls import path
from .views import global_search, search_suggestions

urlpatterns = [
    path('', global_search, name='global-search'),
    path('suggestions/', search_suggestions, name='search-suggestions'),
]
