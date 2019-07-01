from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name = 'index'),
    path('index/', views.index, name = 'index'),

    path('login/', views.login, name = 'login'),
    path('regist/', views.regist, name = 'regist'),

    path('search/', views.search, name = 'search'),
    
    path('personalIndex/<string:username>/', views.personalIndex, name = 'personalIndex'),
    path('personalIndex/<string:username>/manage', views.manage, name = 'manage'),
    path('personalIndex/<string:username>/edit', views.edit, name = 'edit'),
    path('personalIndex/<string:username>/info', views.info, name = 'edit'),
    path('personalIndex/<string:username>/editInfo', views.editInfo, name = 'editInfo'),

    path('blog/<int:blogID>/', views.blogContent, name = 'blogCotent'),
]
