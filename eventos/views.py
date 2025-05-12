# Importaciones del sistema Django
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count, Sum, Prefetch
from django.http import JsonResponse, HttpResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib.auth.models import User  # Importación que faltaba
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.exceptions import PermissionDenied
from django.db import transaction  # Importación para transacciones

# Importaciones de bibliotecas externas
import qrcode
from io import BytesIO
import uuid
import logging

# Importaciones locales de la aplicación
from .models import Event, TicketType, Ticket, UserProfile
from .forms import EventForm, TicketTypeForm, TicketPurchaseForm, UserRegistrationForm, UserProfileForm

# Configurar logging para mejor depuración
logger = logging.getLogger(__name__)

# -------------------------------------------------------------
# Vistas relacionadas con la página principal y listado de eventos
# -------------------------------------------------------------

class IndexView(ListView):
    """Vista de la página principal que muestra eventos próximos"""
    model = Event
    template_name = 'eventos/index.html'
    context_object_name = 'events'
    
    def get_queryset(self):
        """Obtener los 6 próximos eventos ordenados por fecha"""
        return Event.objects.filter(
            event_date__gte=timezone.now()
        ).order_by('event_date')[:6]
    
    def get_context_data(self, **kwargs):
        """Añadir estadísticas adicionales al contexto"""
        context = super().get_context_data(**kwargs)
        # Contar eventos próximos y total
        context['upcoming_count'] = Event.objects.filter(
            event_date__gte=timezone.now()
        ).count()
        context['total_events'] = Event.objects.count()
        
        # Añadir contador de entradas si el usuario está autenticado
        if self.request.user.is_authenticated:
            context['user_tickets_count'] = Ticket.objects.filter(
                user=self.request.user
            ).count()
        return context


class EventListView(ListView):
    """Vista que muestra la lista completa de eventos con filtros"""
    model = Event
    template_name = 'eventos/event_list.html'
    context_object_name = 'events'
    paginate_by = 9
    
    def get_queryset(self):
        """Obtener eventos con filtros aplicados"""
        queryset = Event.objects.all()
        
        # Filtrar por búsqueda
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) | 
                Q(description__icontains=query) |
                Q(location__icontains=query)
            )
        
        # Filtrar por fecha
        date_filter = self.request.GET.get('date')
        if date_filter == 'upcoming':
            queryset = queryset.filter(event_date__gte=timezone.now())
        elif date_filter == 'past':
            queryset = queryset.filter(event_date__lt=timezone.now())
        
        # Ordenar resultados
        ordering = self.request.GET.get('order_by', '-event_date')
        return queryset.order_by(ordering)
    
    def get_context_data(self, **kwargs):
        """Añadir parámetros de filtrado al contexto"""
        context = super().get_context_data(**kwargs)
        # Pasar los parámetros de filtro para mantenerlos en la UI
        context['q'] = self.request.GET.get('q', '')
        context['date'] = self.request.GET.get('date', '')
        context['order_by'] = self.request.GET.get('order_by', '-event_date')
        return context


class EventDetailView(DetailView):
    """Vista para ver los detalles de un evento específico"""
    model = Event
    template_name = 'eventos/event_detail.html'
    context_object_name = 'event'
    
    def get_context_data(self, **kwargs):
        """Añadir tipos de entradas y entradas del usuario al contexto"""
        context = super().get_context_data(**kwargs)
        # Obtener todos los tipos de entradas para este evento
        context['ticket_types'] = TicketType.objects.filter(event=self.object)
        
        # Si el usuario está autenticado, obtener sus entradas para este evento
        if self.request.user.is_authenticated:
            user_tickets = Ticket.objects.filter(
                user=self.request.user,
                ticket_type__event=self.object
            ).select_related('ticket_type')  # Optimización: reducir consultas SQL
            
            context['user_tickets'] = user_tickets
        
        return context

# -------------------------------------------------------------
# Vistas para la gestión de eventos (CRUD)
# -------------------------------------------------------------

@staff_member_required
def event_create(request):
    """Vista para crear un nuevo evento (solo staff)"""
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save()
            messages.success(request, 'Evento creado con éxito.')
            return redirect('eventos:event_detail', pk=event.pk)
    else:
        form = EventForm()
    
    return render(request, 'eventos/event_form.html', {
        'form': form,
        'title': 'Crear Evento',
        'button_text': 'Crear'
    })


@staff_member_required
def event_update(request, pk):
    """Vista para actualizar un evento existente (solo staff)"""
    event = get_object_or_404(Event, pk=pk)
    
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, 'Evento actualizado con éxito.')
            return redirect('eventos:event_detail', pk=event.pk)
    else:
        form = EventForm(instance=event)
    
    return render(request, 'eventos/event_form.html', {
        'form': form,
        'event': event,
        'title': 'Editar Evento',
        'button_text': 'Actualizar'
    })


@staff_member_required
def event_delete(request, pk):
    """Vista para eliminar un evento (solo staff)"""
    event = get_object_or_404(Event, pk=pk)
    
    if request.method == 'POST':
        # Guardar nombre para mensaje
        event_name = event.name
        # Eliminar evento
        event.delete()
        messages.success(request, f'Evento "{event_name}" eliminado con éxito.')
        return redirect('eventos:event_list')
    
    return render(request, 'eventos/event_confirm_delete.html', {
        'event': event
    })

# -------------------------------------------------------------
# Vistas para gestión de tipos de entradas
# -------------------------------------------------------------

@staff_member_required
def ticket_type_create(request, event_id):
    """Vista para crear un nuevo tipo de entrada para un evento (solo staff)"""
    event = get_object_or_404(Event, pk=event_id)
    
    # Verificar que el evento no haya pasado
    if event.event_date < timezone.now():
        messages.error(request, 'No se pueden crear tipos de entradas para eventos pasados.')
        return redirect('eventos:event_detail', pk=event_id)
    
    if request.method == 'POST':
        form = TicketTypeForm(request.POST)
        if form.is_valid():
            ticket_type = form.save(commit=False)
            ticket_type.event = event
            ticket_type.save()
            messages.success(request, f'Tipo de entrada "{ticket_type.name}" creado con éxito.')
            return redirect('eventos:event_detail', pk=event.pk)
    else:
        form = TicketTypeForm()
    
    return render(request, 'eventos/ticket_type_form.html', {
        'form': form,
        'event': event
    })

# -------------------------------------------------------------
# Vistas para compra y gestión de entradas
# -------------------------------------------------------------

@login_required
def ticket_purchase(request, ticket_type_id):
    """Vista para la compra de entradas"""
    ticket_type = get_object_or_404(TicketType, pk=ticket_type_id)
    
    # Verificar disponibilidad
    if not ticket_type.is_available():
        messages.error(request, 'Este tipo de entrada no está disponible.')
        return redirect('eventos:event_detail', pk=ticket_type.event.pk)
    
    if request.method == 'POST':
        form = TicketPurchaseForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            
            # Verificar que hay suficientes entradas disponibles
            if quantity > ticket_type.available_quantity:
                messages.error(request, f'Solo hay {ticket_type.available_quantity} entradas disponibles.')
                return redirect('eventos:ticket_purchase', ticket_type_id=ticket_type.pk)
            
            # Crear las entradas
            tickets = []
            try:
                # Usar transacción para garantizar que todas las entradas se crean o ninguna
                with transaction.atomic():
                    for _ in range(quantity):
                        ticket = Ticket(
                            ticket_type=ticket_type,
                            user=request.user,
                            ticket_code=str(uuid.uuid4())  # Generar código único
                        )
                        ticket.save()
                        tickets.append(ticket)
                
                # Mensaje de éxito y redirección
                messages.success(request, f'Has comprado {quantity} entrada(s) con éxito.')
                return redirect('eventos:my_tickets')
                
            except Exception as e:
                logger.error(f"Error al crear entradas: {str(e)}")
                messages.error(request, f'Error al procesar la compra: {str(e)}')
                return redirect('eventos:event_detail', pk=ticket_type.event.pk)
    else:
        form = TicketPurchaseForm()
    
    return render(request, 'eventos/ticket_purchase.html', {
        'form': form,
        'ticket_type': ticket_type
    })


@login_required
def my_tickets(request):
    """Vista para mostrar las entradas del usuario"""
    # Obtener todas las entradas del usuario ordenadas por fecha de compra
    base_tickets = Ticket.objects.filter(user=request.user).select_related(
        'ticket_type', 'ticket_type__event'
    ).order_by('-purchase_date')
    
    # Filtrar por evento si se especifica
    event_id = request.GET.get('event')
    if event_id:
        try:
            event_id = int(event_id)
            base_tickets = base_tickets.filter(ticket_type__event__id=event_id)
        except (ValueError, TypeError):
            pass  # Si el event_id no es un número válido, ignorar el filtro
    
    # Filtrar por estado si se especifica
    status = request.GET.get('status')
    if status == 'used':
        base_tickets = base_tickets.filter(is_used=True)
    elif status == 'unused':
        base_tickets = base_tickets.filter(is_used=False)
    
    # Obtener eventos para el filtro desplegable
    events = Event.objects.filter(
        tickettype__ticket__user=request.user
    ).distinct()
    
    # Obtener el contexto actual
    now = timezone.now()
    
    return render(request, 'eventos/my_tickets.html', {
        'tickets': base_tickets,
        'events': events,
        'selected_event': event_id,
        'selected_status': status,
        'now': now  # Pasar la fecha actual al template
    })


@login_required
def ticket_qr(request, ticket_id):
    """Vista para generar y mostrar el código QR de una entrada"""
    # Obtener la entrada, verificando que pertenezca al usuario actual
    ticket = get_object_or_404(Ticket, pk=ticket_id, user=request.user)
    
    # Generar código QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(ticket.ticket_code)
    qr.make(fit=True)
    
    # Crear imagen
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Guardar la imagen en un buffer
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    
    # Devolver la imagen como respuesta
    return HttpResponse(buffer, content_type="image/png")


@staff_member_required
def verify_ticket(request):
    """Vista para verificar entradas en la entrada del evento (solo staff)"""
    if request.method == 'POST':
        ticket_code = request.POST.get('ticket_code')
        if not ticket_code:
            return JsonResponse({
                'valid': False,
                'message': 'Código de entrada no proporcionado.'
            })
            
        try:
            # Buscar la entrada por su código
            ticket = Ticket.objects.select_related(
                'ticket_type', 'ticket_type__event', 'user'
            ).get(ticket_code=ticket_code)
            
            # Verificar si ya fue utilizada
            if ticket.is_used:
                return JsonResponse({
                    'valid': False,
                    'message': 'Esta entrada ya ha sido utilizada.'
                })
            
            # Verificar si el evento ya comenzó
            if ticket.ticket_type.event.event_date > timezone.now():
                return JsonResponse({
                    'valid': False,
                    'message': 'El evento aún no ha comenzado.'
                })
            
            # Si todo está correcto, marcar como utilizada
            ticket.is_used = True
            ticket.save(update_fields=['is_used'])
            
            # Devolver información de la entrada verificada
            return JsonResponse({
                'valid': True,
                'ticket': {
                    'id': ticket.id,
                    'event': ticket.ticket_type.event.name,
                    'ticket_type': ticket.ticket_type.name,
                    'user': f"{ticket.user.first_name} {ticket.user.last_name}" if ticket.user.first_name else ticket.user.username,
                    'purchase_date': ticket.purchase_date.strftime('%d/%m/%Y %H:%M')
                },
                'message': 'Entrada verificada con éxito.'
            })
        except Ticket.DoesNotExist:
            return JsonResponse({
                'valid': False,
                'message': 'Código de entrada inválido o no encontrado.'
            })
        except Exception as e:
            logger.error(f"Error al verificar entrada: {str(e)}")
            return JsonResponse({
                'valid': False,
                'message': f'Error al verificar la entrada: {str(e)}'
            })
    
    # Si es GET, mostrar la página de verificación
    return render(request, 'eventos/verify_ticket.html')

# -------------------------------------------------------------
# Vistas de autenticación y perfil de usuario
# -------------------------------------------------------------

def register(request):
    """Vista para registro de nuevos usuarios"""
    # Redirigir si ya está autenticado
    if request.user.is_authenticated:
        messages.info(request, 'Ya tienes una cuenta activa.')
        return redirect('/')  # Usar URL absoluta en lugar de nombre de URL
        
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        profile_form = UserProfileForm(request.POST)
        
        if user_form.is_valid() and profile_form.is_valid():
            # Crear usuario
            user = user_form.save()
            
            # Crear perfil asociado
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            
            messages.success(request, 'Registro completado con éxito. Ahora puedes iniciar sesión.')
            return redirect('login')
    else:
        user_form = UserRegistrationForm()
        profile_form = UserProfileForm()
    
    return render(request, 'eventos/register.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })


@login_required
def profile(request):
    """Vista para el perfil del usuario y su actualización"""
    if request.method == 'POST':
        # Formulario para datos de usuario
        user_form = UserRegistrationForm(request.POST, instance=request.user)
        
        # Intentar obtener el perfil o crear uno nuevo si no existe
        try:
            profile = request.user.profile
        except UserProfile.DoesNotExist:
            profile = UserProfile(user=request.user)
            
        # Formulario para datos de perfil
        profile_form = UserProfileForm(request.POST, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Perfil actualizado con éxito.')
            return redirect('profile')  # Usar URL absoluta
    else:
        # Preparar formularios con datos actuales
        user_form = UserRegistrationForm(instance=request.user)
        
        try:
            profile = request.user.profile
        except UserProfile.DoesNotExist:
            profile = UserProfile(user=request.user)
            
        profile_form = UserProfileForm(instance=profile)
    
    # Obtener estadísticas de tickets del usuario
    tickets = Ticket.objects.filter(user=request.user)
    upcoming_tickets = tickets.filter(ticket_type__event__event_date__gte=timezone.now())
    used_tickets = tickets.filter(is_used=True)
    
    return render(request, 'eventos/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'ticket_count': tickets.count(),
        'upcoming_tickets': upcoming_tickets.count(),
        'used_tickets': used_tickets.count()
    })

# -------------------------------------------------------------
# Vistas de administración y estadísticas
# -------------------------------------------------------------

@staff_member_required
def dashboard(request):
    """Vista de panel de control con estadísticas (solo staff)"""
    try:
        # Estadísticas generales
        total_events = Event.objects.count()
        upcoming_events = Event.objects.filter(event_date__gte=timezone.now()).count()
        total_tickets = Ticket.objects.count()
        used_tickets = Ticket.objects.filter(is_used=True).count()
        total_users = User.objects.count()
        
        # Eventos más populares (con más entradas vendidas)
        popular_events = Event.objects.annotate(
            ticket_count=Count('tickettype__ticket')
        ).order_by('-ticket_count')[:5]
        
        # Ventas por evento (ingresos)
        sales_by_event = Event.objects.annotate(
            ticket_count=Count('tickettype__ticket'),
            revenue=Sum('tickettype__ticket__ticket_type__price')
        ).order_by('-revenue')[:10]
        
        return render(request, 'eventos/dashboard.html', {
            'total_events': total_events,
            'upcoming_events': upcoming_events,
            'total_tickets': total_tickets,
            'used_tickets': used_tickets,
            'total_users': total_users,
            'popular_events': popular_events,
            'sales_by_event': sales_by_event
        })
    except Exception as e:
        logger.error(f"Error en dashboard: {str(e)}")
        messages.error(request, f"Error al cargar el panel de control: {str(e)}")
        return redirect('/')  # Usar URL absoluta