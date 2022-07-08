from django.contrib import admin
from django.urls import include, path
from django.conf.urls.static import static
from django.conf import settings
from feedauth import views

urlpatterns = [
    path('showlogin/', views.showlogin, name='showlogin'),
    path('dologin/', views.dologin, name='dologin'),
    path('logout/', views.dologout, name='dologout'),
]

