from django.conf.urls import url,include
from blogApp import views
from django.urls import path
#from . import views

urlpatterns = [
                       url(r'^$', views.login, name='login'),
                       url(r'^login/$', views.login, name='login'),
                       url(r'^regist/$', views.regist, name='regist'),
                       url(r'^index/$', views.index, name='index'),
                       url(r'^logout/$', views.logout, name='logout'),
]