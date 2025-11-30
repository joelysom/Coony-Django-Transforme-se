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
    path('social/', views.social, name='social'),
    path('social/like/<int:post_id>/', views.like_post, name='like_post'),
    path('social/comment/<int:post_id>/', views.comment_post, name='comment_post'),
]
