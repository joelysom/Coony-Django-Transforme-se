from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('mobile/', views.mobile, name='mobile'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/mobile/', views.dashboard_mobile, name='dashboard_mobile'),
]
