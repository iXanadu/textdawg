from django.urls import path
from . import views

urlpatterns = [
    # ... your other url patterns ...
    # Modify your existing urlpatterns in the urls.py file

    path('prompts/list', views.prompt_list, name='prompt_list'),
    path('prompts/add/', views.prompt_add, name='prompt_add'),
    path('prompts/edit/<int:id>/', views.prompt_edit, name='prompt_edit'),
    path('prompts/delete/', views.prompt_delete, name='prompt_delete'),
]

