from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'eventos'

urlpatterns = [
    # Página principal
    path('', views.IndexView.as_view(), name='index'),
    
    # Gestión de eventos
    path('eventos/', views.EventListView.as_view(), name='event_list'),
    path('eventos/<int:pk>/', views.EventDetailView.as_view(), name='event_detail'),
    path('eventos/crear/', views.event_create, name='event_create'),
    path('eventos/<int:pk>/editar/', views.event_update, name='event_update'),
    path('eventos/<int:pk>/eliminar/', views.event_delete, name='event_delete'),
    
    # Gestión de tipos de entradas
    path('eventos/<int:event_id>/ticket-type/crear/', views.ticket_type_create, name='ticket_type_create'),
    path('ticket-type/<int:ticket_type_id>/comprar/', views.ticket_purchase, name='ticket_purchase'),
    
    # Gestión de entradas
    path('mis-entradas/', views.my_tickets, name='my_tickets'),
    path('ticket/<int:ticket_id>/qr/', views.ticket_qr, name='ticket_qr'),
    path('verificar-entrada/', views.verify_ticket, name='verify_ticket'),
    
    # Autenticación y perfil de usuario
    path('registro/', views.register, name='register'),
    path('iniciar-sesion/', 
         auth_views.LoginView.as_view(template_name='eventos/login.html'), 
         name='login'),
    path('cerrar-sesion/', 
         auth_views.LogoutView.as_view(next_page='/'), 
         name='logout'),
    path('perfil/', views.profile, name='profile'),
    
    # Cambio de contraseña
    path('cambiar-password/', 
         auth_views.PasswordChangeView.as_view(
             template_name='eventos/password_change_form.html',
             success_url='/perfil/'
         ),
         name='password_change'),
    
    # Restablecimiento de contraseña
    path('reiniciar-password/', 
         auth_views.PasswordResetView.as_view(
             template_name='eventos/password_reset_form.html',
             email_template_name='eventos/password_reset_email.html',
             subject_template_name='eventos/password_reset_subject.txt'
         ),
         name='password_reset'),
    path('reiniciar-password/enviado/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='eventos/password_reset_done.html'
         ),
         name='password_reset_done'),
    path('reiniciar-password/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='eventos/password_reset_confirm.html'
         ),
         name='password_reset_confirm'),
    path('reiniciar-password/completado/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='eventos/password_reset_complete.html'
         ),
         name='password_reset_complete'),
    
    # Panel de administración
    path('panel-control/', views.dashboard, name='dashboard'),
]