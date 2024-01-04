from django.urls import path
from . import views

urlpatterns = [
    path('textbot/', views.textbot_view, name='textbot'),
    path('chatbot/', views.chatbot_view, name='chatbot'),
    path('test-ai/', views.test_ai_assistant, name='test_ai_assistant'),

    # ... other url patterns for your app ...
]
