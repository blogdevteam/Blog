from django.urls import path
from . import views

urlpatterns = [
#     path('', views.index, name = 'index'),
     path('', views.login, name = 'login'),

    path('index/', views.index, name = 'index'),

    path('login/', views.login, name = 'login'),
    path('regist/', views.regist, name = 'regist'),

    path('search/', views.search, name = 'search'),
    path('manage/<slug:username>/', views.manage, name = 'manage'),
    path('edit/<slug:blogid>/', views.edit, name = 'edit'),
    path('info/<slug:username>', views.info, name='edit'),
    path('editInfo/<slug:username>', views.editInfo, name='editInfo'),
    path('edit/submit/<slug:username>', views.submit, name='submit'),

    path('download/<slug:username>/', views.download, name = 'download'),
    
    path('personalIndex/<string:username>/', views.personalIndex, name = 'personalIndex'),
    path('blogcontent/<int:blog_id>/', views.blog_content, name='content'),
    # path('manage/<string:username>', views.manage, name = 'manage'),
    # path('edit/<string:username>', views.edit, name = 'edit'),
    # path('info/<string:username>', views.info, name = 'edit'),
    # path('editInfo/<string:username>', views.editInfo, name = 'editInfo'),

    # path('blog/<int:blogID>/', views.blogContent, name = 'blogCotent'),
]
