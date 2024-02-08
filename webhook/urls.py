from django.urls import path,re_path
from . import views

urlpatterns = [
    re_path(r'^api/fubhook/(?P<event_type>\w+)/$', views.fubhook_handler, name='fubhook_handler'),
    path('sms_receiver/', views.sms_receiver, name='sms_receiver'),
    path('smsweb_receiver/', views.smsweb_receiver, name='smsweb_receiver'),
    path('chat_receiver/', views.chat_receiver, name='chat_receiver'),
    path('api/mark_sms_message/', views.mark_sms_message, name='mark_sms_message'),
    path('api/create_topic/', views.create_chat_topic, name='create_topic'),
    path('api/list_topics/', views.list_chat_topics, name='list_topics'),
    path('api/get_chat_messages/<int:topic_id>/', views.get_chat_messages, name='get_chat_messages'),
    path('api/get_sms_messages/<str:phone_number>/', views.get_sms_messages, name='get_sms_messages'),
]
