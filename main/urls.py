from django.urls import path
from . import views

urlpatterns = [
    # ... your other url patterns ...
    # Modify your existing urlpatterns in the urls.py file

    path('get_perms/', views.get_model_permissions, name='get_model_permissions'),
    path('fub_webhooks/fub_webhook_add', views.fub_webhook_add, name='fub_webhook_add'),
    path('fub_webhooks/fub_webhook_toggle', views.fub_webhook_toggle, name='fub_webhook_toggle'),
    path('fub_webhooks/fub_webhook_list', views.fub_webhook_list, name='fub_webhook_list'),
    path('fub_webhooks/fub_webhook_delete/<int:id>', views.fub_webhook_delete, name='fub_webhook_delete'),
    path('fub_webhooks/fub_webhook_get/<int:id>', views.fub_webhook_get, name='fub_webhook_get'),
    path('prompts/list', views.prompt_list, name='prompt_list'),
    path('prompts/get_full_prompt/<int:id>', views.prompt_get_full_prompt, name='prompt_get_full_prompt'),
    path('prompts/add/', views.prompt_add, name='prompt_add'),
    path('prompts/edit/<int:id>/', views.prompt_edit, name='prompt_edit'),
    path('prompts/delete/', views.prompt_delete, name='prompt_delete'),
    path('audit/messages/', views.audit_messages, name='/audit_messages/'),
    path('audit/get_messages/', views.audit_get_messages, name='/audit_get_messages/'),
    path('audit/message/<int:message_id>/', views.audit_get_message, name='/audit_get_message/'),
    path('audit/resolve_message/', views.audit_resolve_message, name='/audit_resolve_message/'),
    path('audit/delete_messages/', views.audit_delete_messages, name='/audit_delete_messages/'),
]



