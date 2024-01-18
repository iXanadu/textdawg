from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LoginView
from django.contrib.auth import views as auth_views
from main import views  # Import your views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('webhook/', include('webhook.urls')),
    path('webhook_lab/', include('webhook_lab.urls')),  # Include webhook_lab URLs
    path('dashboard/', views.dashboard, name='dashboard'),
    path('login/', LoginView.as_view(template_name='main/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/login/'), name='logout'),
    path('admin/', admin.site.urls),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

