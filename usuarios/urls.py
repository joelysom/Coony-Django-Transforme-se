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
    path('eventos/criar/', views.create_event, name='create_event'),
    path('eventos/toggle_favorite/<int:evento_id>/', views.toggle_favorite_event, name='toggle_favorite_event'),
    path('social/like/<int:post_id>/', views.like_post, name='like_post'),
    path('social/comment/<int:post_id>/', views.comment_post, name='comment_post'),
    path('social/delete/<int:post_id>/', views.delete_post, name='delete_post'),
    path('notifications/', views.notifications, name='notifications'),
    path('perfil/', views.perfil, name='perfil'),
    path('chat/', views.chat, name='chat'),
    path('chat/api/conversations/', views.chat_conversations_api, name='chat_conversations_api'),
    path('chat/api/search/', views.chat_search_users_api, name='chat_search_users_api'),
    path('chat/api/conversations/start/', views.chat_start_conversation_api, name='chat_start_conversation_api'),
    path('chat/api/conversations/<int:conversation_id>/messages/', views.chat_messages_api, name='chat_messages_api'),
    path('chat/api/conversations/<int:conversation_id>/messages/send/', views.chat_send_message_api, name='chat_send_message_api'),
    path('chat/api/messages/<int:message_id>/delete/', views.chat_delete_message_api, name='chat_delete_message_api'),
]
