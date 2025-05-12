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
    
    # Gestión de entradas y pagos
    path('mis-entradas/', views.my_tickets, name='my_tickets'),
    path('entrada/<int:ticket_id>/', views.ticket_detail, name='ticket_detail'),
    path('entrada/<int:ticket_id>/asiento/', views.seat_selection, name='seat_selection'),
    path('entrada/<int:ticket_id>/pago/', views.payment_process, name='payment_process'),
    path('ticket/<int:ticket_id>/qr/', views.ticket_qr, name='ticket_qr'),
    path('verificar-entrada/', views.verify_ticket, name='verify_ticket'),
    
    # Autenticación y perfil de usuario
    path('registro/', views.register, name='register'),
    # Eliminar estas rutas ya que ahora están en evento_manager/urls.py
    # path('iniciar-sesion/', auth_views.LoginView.as_view(template_name='eventos/login.html'), name='login'),
    # path('cerrar-sesion/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('perfil/', views.profile, name='profile'),
    
    # Cambio de contraseña
    path('cambiar-password/',
         auth_views.PasswordChangeView.as_view(
             template_name='eventos/password_change_form.html',
             success_url='/perfil/'
         ),
         name='password_change'),
    
    # Eliminar estas rutas de restablecimiento de contraseña ya que están en evento_manager/urls.py
    # path('reiniciar-password/', ...),
    # path('reiniciar-password/enviado/', ...),
    # path('reiniciar-password/<uidb64>/<token>/', ...),
    # path('reiniciar-password/completado/', ...),
    
    # Panel de administración
    path('panel-control/', views.dashboard, name='dashboard'),
]