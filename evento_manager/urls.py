from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView

urlpatterns = [
    # Panel de administración
    path('admin/', admin.site.urls),
    
    # URLs de autenticación
    path('iniciar-sesion/', auth_views.LoginView.as_view(template_name='eventos/login.html'), name='login'),
    path('cerrar-sesion/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Recuperación de contraseña
    path('reiniciar-password/', 
         auth_views.PasswordResetView.as_view(template_name='eventos/password_reset.html'), 
         name='password_reset'),
    path('reiniciar-password/enviado/', 
         auth_views.PasswordResetDoneView.as_view(template_name='eventos/password_reset_done.html'), 
         name='password_reset_done'),
    path('reiniciar-password/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name='eventos/password_reset_confirm.html'), 
         name='password_reset_confirm'),
    path('reiniciar-password/completado/', 
         auth_views.PasswordResetCompleteView.as_view(template_name='eventos/password_reset_complete.html'), 
         name='password_reset_complete'),
    
    # URLs de la aplicación principal
    path('', include('eventos.urls')),
    
    # Redirección para cualquier URL no definida a la página principal
    path('favicon.ico', RedirectView.as_view(url=settings.STATIC_URL + 'img/favicon.ico')),
]

# Configuración para servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Habilitar la barra de depuración de Django (si está instalada)
    try:
        import debug_toolbar
        urlpatterns.append(path('__debug__/', include(debug_toolbar.urls)))
    except ImportError:
        pass