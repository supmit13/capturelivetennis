from django.contrib import admin
from django.urls import include, path
from django.conf.urls.static import static
from django.conf import settings
from feedman import views

urlpatterns = [
    path('listfeeds/', views.listfeeds, name='listfeeds'),
    path('', views.listfeeds, name='listfeeds'),
    path('editfeed/', views.editfeed, name='editfeed'),
    path('deletefeed/', views.deletefeed, name='deletefeed'),
    path('savefeed/', views.savefeed, name='savefeed'),
    path('searchfeeds/', views.searchfeeds, name='searchfeeds'),
    path('settings/', views.feedsettings, name='feedsettings'),
    path('sendmail/', views.sendmail, name='sendmail'),
    #path('showfeed/', views.showfeed, name='showfeed'),
    path('getfeedpath/', views.getfeedpath, name='getfeedpath')
]

