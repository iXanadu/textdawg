from django.urls import path
from . import views

urlpatterns = [
    path('sms_receiver/', views.sms_receiver, name='sms_receiver'),
    path('smsweb_receiver/', views.smsweb_receiver, name='smsweb_receiver'),
    path('chat_receiver/', views.chat_receiver, name='chat_receiver'),
    path('api/create_topic/', views.create_chat_topic, name='create_topic'),
    path('api/list_topics/', views.list_chat_topics, name='list_topics'),
    path('api/get_messages/<int:topic_id>/', views.get_chat_messages, name='get_messages'),
]
