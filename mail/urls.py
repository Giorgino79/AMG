"""
URLs for Mail App
"""

from django.urls import path
from . import views

app_name = 'mail'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Email Configuration
    path('config/', views.email_config, name='config'),
    path('config/test/', views.test_config, name='test_config'),

    # Templates
    path('templates/', views.template_list, name='template_list'),
    path('templates/create/', views.template_create, name='template_create'),
    path('templates/<uuid:pk>/edit/', views.template_edit, name='template_edit'),
    path('templates/<uuid:pk>/delete/', views.template_delete, name='template_delete'),

    # Messages
    path('messages/', views.message_list, name='message_list'),
    path('messages/<uuid:pk>/', views.message_detail, name='message_detail'),
    path('messages/<uuid:pk>/toggle-flag/', views.message_toggle_flag, name='message_toggle_flag'),
    path('compose/', views.compose_email, name='compose'),

    # Promemoria
    path('promemoria/', views.promemoria_list, name='promemoria_list'),
    path('promemoria/create/', views.promemoria_create, name='promemoria_create'),
    path('promemoria/<uuid:pk>/', views.promemoria_detail, name='promemoria_detail'),
    path('promemoria/<uuid:pk>/edit/', views.promemoria_edit, name='promemoria_edit'),
    path('promemoria/<uuid:pk>/complete/', views.promemoria_complete, name='promemoria_complete'),
    path('promemoria/<uuid:pk>/delete/', views.promemoria_delete, name='promemoria_delete'),

    # Chat - Pagina unificata
    path('chat/', views.chat, name='chat'),
    path('chat/<uuid:pk>/', views.chat_conversation_detail, name='chat_detail'),

    # Email Sync
    path('sync/', views.sync_emails_manual, name='sync_emails'),
]
