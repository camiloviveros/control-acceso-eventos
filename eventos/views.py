from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.db import transaction
from django.urls import reverse
from datetime import datetime
from django.contrib.auth.models import User
from django.db.models import Count, Sum

import qrcode
from io import BytesIO
import logging

from .models import Event, TicketType, Ticket, UserProfile, Payment
from .forms import EventForm, TicketTypeForm, TicketPurchaseForm, UserRegistrationForm, UserProfileForm
from .repositories import (
    EventRepository, TicketTypeRepository, TicketRepository, 
    PaymentRepository, UserProfileRepository
)
from .services import EventService, TicketTypeService, TicketService

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
        return EventRepository.get_upcoming_events(limit=6)
    
    def get_context_data(self, **kwargs):
        """Añadir estadísticas adicionales al contexto basado en el tipo de usuario"""
        context = super().get_context_data(**kwargs)
        
        # Agregar estadísticas al contexto dependiendo del tipo de usuario
        if self.request.user.is_authenticated:
            # Contar eventos próximos y total para todos los usuarios autenticados
            context['upcoming_count'] = EventRepository.get_upcoming_events().count()
            context['total_events'] = EventRepository.get_all_events().count()
            
            if self.request.user.is_staff:
                # Estadísticas adicionales para administradores
                context['total_users'] = User.objects.count()
                context['tickets_count'] = Ticket.objects.count()
                
                # Obtener eventos con más ventas
                context['popular_events'] = Event.objects.annotate(
                    tickets_sold=Count('tickettype__ticket')
                ).order_by('-tickets_sold')[:5]
                
                # Ventas totales
                context['total_sales'] = Ticket.objects.filter(is_paid=True).aggregate(
                    total=Sum('ticket_type__price')
                )['total'] or 0
            else:
                # Estadísticas para usuarios normales
                context['user_tickets_count'] = TicketRepository.get_tickets_by_user(
                    self.request.user.id
                ).count()
                
                # Entradas pendientes (no pagadas)
                context['pending_tickets'] = TicketRepository.get_tickets_by_status(
                    self.request.user.id, 'unpaid'
                ).count()
                
                # Eventos disponibles
                context['events_count'] = EventRepository.get_upcoming_events().count()
        
        return context


class EventListView(ListView):
    """Vista que muestra la lista completa de eventos con filtros"""
    model = Event
    template_name = 'eventos/event_list.html'
    context_object_name = 'events'
    paginate_by = 9
    
    def get_queryset(self):
        """Obtener eventos con filtros aplicados"""
        query = self.request.GET.get('q')
        date_filter = self.request.GET.get('date')
        ordering = self.request.GET.get('order_by', '-event_date')
        
        return EventRepository.search_events(
            query=query, 
            date_filter=date_filter, 
            order_by=ordering
        )
    
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
        context['ticket_types'] = TicketTypeRepository.get_ticket_types_by_event(self.object.id)
        
        # Si el usuario está autenticado, obtener sus entradas para este evento
        if self.request.user.is_authenticated:
            user_tickets = TicketRepository.get_tickets_by_user_and_event(
                self.request.user.id,
                self.object.id
            )
            
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
            try:
                # Usar el servicio para crear el evento
                event = EventService.create_event(form.save(commit=False))
                messages.success(request, 'Evento creado con éxito.')
                return redirect('eventos:event_detail', pk=event.pk)
            except ValueError as e:
                messages.error(request, str(e))
                return render(request, 'eventos/event_form.html', {
                    'form': form,
                    'title': 'Crear Evento',
                    'button_text': 'Crear'
                })
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
            try:
                # Usar el servicio para actualizar el evento
                event_data = form.save(commit=False)
                EventService.update_event(event, event_data.__dict__)
                messages.success(request, 'Evento actualizado con éxito.')
                return redirect('eventos:event_detail', pk=event.pk)
            except ValueError as e:
                messages.error(request, str(e))
                return render(request, 'eventos/event_form.html', {
                    'form': form,
                    'event': event,
                    'title': 'Editar Evento',
                    'button_text': 'Actualizar'
                })
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
        try:
            # Usar el servicio para eliminar el evento
            event_name = EventService.delete_event(event)
            messages.success(request, f'Evento "{event_name}" eliminado con éxito.')
            return redirect('eventos:event_list')
        except Exception as e:
            logger.error(f"Error al eliminar evento: {str(e)}")
            messages.error(request, f'Error al eliminar el evento: {str(e)}')
            return redirect('eventos:event_detail', pk=event.pk)
    
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
    
    if request.method == 'POST':
        form = TicketTypeForm(request.POST)
        if form.is_valid():
            try:
                # Usar el servicio para crear el tipo de entrada
                ticket_type = TicketTypeService.create_ticket_type(event, form.save(commit=False))
                messages.success(request, f'Tipo de entrada "{ticket_type.name}" creado con éxito.')
                return redirect('eventos:event_detail', pk=event.pk)
            except ValueError as e:
                messages.error(request, str(e))
                return render(request, 'eventos/ticket_type_form.html', {
                    'form': form,
                    'event': event
                })
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
    ticket_type = TicketTypeRepository.get_ticket_type_by_id(ticket_type_id)
    
    # Verificar disponibilidad usando el repositorio
    if not ticket_type.is_available():
        messages.error(request, 'Este tipo de entrada no está disponible.')
        return redirect('eventos:event_detail', pk=ticket_type.event.pk)
    
    # Verificar que los administradores no puedan comprar entradas
    if request.user.is_staff:
        messages.warning(request, 'Los administradores no pueden comprar entradas.')
        return redirect('eventos:event_detail', pk=ticket_type.event.pk)
    
    if request.method == 'POST':
        form = TicketPurchaseForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            
            try:
                # Usar el servicio para comprar las entradas
                tickets = TicketService.purchase_tickets(request.user, ticket_type, quantity)
                
                # Mensaje de éxito y redirección al primer ticket para seleccionar asiento/pagar
                messages.success(request, f'Has reservado {quantity} entrada(s) con éxito. Ahora selecciona asiento y completa el pago.')
                
                # Si es solo 1 entrada, redirigir directamente a selección de asientos
                if quantity == 1:
                    if ticket_type.event.has_seats:
                        return redirect('eventos:seat_selection', ticket_id=tickets[0].id)
                    else:
                        return redirect('eventos:payment_process', ticket_id=tickets[0].id)
                else:
                    return redirect('eventos:my_tickets')
                
            except ValueError as e:
                messages.error(request, str(e))
                return redirect('eventos:ticket_purchase', ticket_type_id=ticket_type.pk)
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
def seat_selection(request, ticket_id):
    """Vista para seleccionar asiento para una entrada"""
    # Usar el repositorio para obtener la entrada
    ticket = TicketRepository.get_ticket_by_id(ticket_id)
    
    # Verificar que la entrada pertenece al usuario actual
    if ticket.user.id != request.user.id:
        messages.error(request, 'No tienes permiso para acceder a esta entrada.')
        return redirect('eventos:my_tickets')
    
    # Verificar que la entrada no esté pagada
    if ticket.is_paid:
        messages.warning(request, 'Esta entrada ya está pagada y tiene asiento asignado.')
        return redirect('eventos:ticket_detail', ticket_id=ticket.id)
    
    # Verificar que el evento permita selección de asientos
    if not ticket.ticket_type.event.has_seats:
        messages.warning(request, 'Este evento no requiere selección de asientos.')
        return redirect('eventos:payment_process', ticket_id=ticket.id)
    
    # Obtener asientos ocupados usando el repositorio
    taken_seats = TicketRepository.get_occupied_seats(ticket.ticket_type.event.id)
    
    if request.method == 'POST':
        seat_number = request.POST.get('seat_number')
        section = request.POST.get('section')
        
        if not seat_number or not section:
            messages.error(request, 'Por favor, selecciona un asiento y sección.')
            return render(request, 'eventos/seat_selection.html', {
                'ticket': ticket,
                'taken_seats': taken_seats
            })
        
        try:
            # Usar el servicio para asignar asiento
            TicketService.assign_seat(ticket, seat_number, section)
            messages.success(request, 'Asiento seleccionado correctamente.')
            return redirect('eventos:payment_process', ticket_id=ticket.id)
        except ValueError as e:
            messages.error(request, str(e))
    
    return render(request, 'eventos/seat_selection.html', {
        'ticket': ticket,
        'taken_seats': taken_seats
    })


@login_required
def payment_process(request, ticket_id):
    """Vista para procesar el pago de una entrada"""
    # Usar el repositorio para obtener la entrada
    ticket = TicketRepository.get_ticket_by_id(ticket_id)
    
    # Verificar que la entrada pertenece al usuario actual
    if ticket.user.id != request.user.id:
        messages.error(request, 'No tienes permiso para acceder a esta entrada.')
        return redirect('eventos:my_tickets')
    
    # Verificar que la entrada no haya sido pagada
    if ticket.is_paid:
        messages.warning(request, 'Esta entrada ya ha sido pagada.')
        return redirect('eventos:ticket_detail', ticket_id=ticket.id)
    
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            payment_data = {
                'payment_method': request.POST.get('payment_method'),
                'card_number': request.POST.get('card_number', '').replace(' ', ''),
                'card_expiry': request.POST.get('card_expiry'),
                'card_cvv': request.POST.get('card_cvv'),
                'card_holder': request.POST.get('card_holder')
            }
            
            # Usar el servicio para procesar el pago
            payment = TicketService.process_payment(ticket, payment_data)
            
            messages.success(request, '¡Pago procesado con éxito! Ya puedes acceder a tu entrada con código QR.')
            return redirect('eventos:ticket_detail', ticket_id=ticket.id)
            
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            logger.error(f"Error en proceso de pago: {str(e)}")
            messages.error(request, f'Error al procesar el pago: {str(e)}')
    
    return render(request, 'eventos/payment_process.html', {'ticket': ticket})


@login_required
def ticket_detail(request, ticket_id):
    """Vista para mostrar el detalle de una entrada con su QR"""
    # Usar el repositorio para obtener la entrada
    ticket = TicketRepository.get_ticket_by_id(ticket_id)
    
    # Verificar que la entrada pertenece al usuario actual
    if ticket.user.id != request.user.id and not request.user.is_staff:
        messages.error(request, 'No tienes permiso para acceder a esta entrada.')
        return redirect('eventos:my_tickets')
    
    # Si la entrada no está pagada y el usuario no es staff, redirigir al proceso de pago
    if not ticket.is_paid and not request.user.is_staff:
        return redirect('eventos:payment_process', ticket_id=ticket.id)
    
    return render(request, 'eventos/ticket_detail.html', {
        'ticket': ticket,
        'is_expired': ticket.is_expired(),
        'now': timezone.now(),
    })


@login_required
def my_tickets(request):
    """Vista para mostrar las entradas del usuario"""
    # Usar el repositorio para obtener las entradas del usuario
    base_tickets = TicketRepository.get_tickets_by_user(request.user.id)
    
    # Filtrar por evento si se especifica
    event_id = request.GET.get('event')
    if event_id:
        try:
            event_id = int(event_id)
            base_tickets = TicketRepository.get_tickets_by_user_and_event(request.user.id, event_id)
        except (ValueError, TypeError):
            pass  # Si el event_id no es un número válido, ignorar el filtro
    
    # Filtrar por estado si se especifica
    status = request.GET.get('status')
    if status in ['used', 'unused', 'paid', 'unpaid']:
        base_tickets = TicketRepository.get_tickets_by_status(request.user.id, status)
    
    # Paginación de entradas
    paginator = Paginator(base_tickets, 9)  # 9 entradas por página
    page = request.GET.get('page')
    tickets = paginator.get_page(page)
    
    # Obtener eventos para el filtro desplegable usando el repositorio
    # Eventos en los que el usuario tiene entradas
    events = Event.objects.filter(
        tickettype__ticket__user=request.user
    ).distinct()
    
    # Estadísticas rápidas
    stats = {
        'total': TicketRepository.get_tickets_by_user(request.user.id).count(),
        'paid': TicketRepository.get_tickets_by_status(request.user.id, 'paid').count(),
        'unpaid': TicketRepository.get_tickets_by_status(request.user.id, 'unpaid').count(),
        'upcoming': Event.objects.filter(
            tickettype__ticket__user=request.user,
            event_date__gte=timezone.now()
        ).distinct().count()
    }
    
    return render(request, 'eventos/my_tickets.html', {
        'tickets': tickets,
        'events': events,
        'selected_event': event_id,
        'selected_status': status,
        'stats': stats,
        'now': timezone.now()  # Pasar la fecha actual al template
    })


@login_required
def ticket_qr(request, ticket_id):
    """Vista para generar y mostrar el código QR de una entrada"""
    # Obtener la entrada, verificando que pertenezca al usuario actual o sea staff
    try:
        if request.user.is_staff:
            ticket = TicketRepository.get_ticket_by_id(ticket_id)
        else:
            ticket = TicketRepository.get_ticket_by_id(ticket_id)
            if ticket.user.id != request.user.id:
                return HttpResponse("No tienes permiso para acceder a este QR", status=403)
        
        # Verificar si está pagada (a menos que sea staff)
        if not ticket.is_paid and not request.user.is_staff:
            return HttpResponse("Esta entrada no ha sido pagada", status=403)
        
        # Configurar el tamaño y calidad del QR
        qr = qrcode.QRCode(
            version=4,
            error_correction=qrcode.constants.ERROR_CORRECT_H,  # Mayor corrección de errores
            box_size=10,
            border=4,
        )
        
        # Añadir los datos del ticket
        qr.add_data(ticket.ticket_code)
        qr.make(fit=True)
        
        # Crear imagen con mayor calidad
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Guardar la imagen en un buffer
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        
        # Devolver la imagen como respuesta
        return HttpResponse(buffer, content_type="image/png")
    
    except Exception as e:
        logger.error(f"Error al generar QR: {str(e)}")
        return HttpResponse("Error al generar el código QR", status=500)


@staff_member_required
def verify_ticket(request):
    """Vista para verificar entradas en la entrada del evento (solo staff)"""
    if request.method == 'POST':
        ticket_code = request.POST.get('ticket_code')
        entry_time_str = request.POST.get('entry_time')
        
        # Convertir la hora de entrada si se proporcionó
        entry_time = None
        if entry_time_str:
            try:
                entry_time = timezone.make_aware(datetime.fromisoformat(entry_time_str))
            except (ValueError, TypeError):
                entry_time = timezone.now()
        else:
            entry_time = timezone.now()
        
        if not ticket_code:
            return JsonResponse({
                'valid': False,
                'message': 'Código de entrada no proporcionado.'
            })
        
        # Usar el servicio para verificar la entrada
        result = TicketService.verify_ticket(ticket_code, entry_time)
        
        # Si es una solicitud AJAX, devolver JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            if result['valid']:
                result['redirect_url'] = reverse('eventos:access_permitted', args=[result['ticket'].id])
            else:
                result['redirect_url'] = reverse('eventos:access_denied') + f"?message={result['message']}"
                if result['ticket']:
                    result['redirect_url'] += f"&ticket_id={result['ticket'].id}"
            
            return JsonResponse(result)
        
        # Si no es AJAX, redirigir a la página correspondiente
        if result['valid']:
            return redirect('eventos:access_permitted', ticket_id=result['ticket'].id)
        else:
            url = reverse('eventos:access_denied') + f"?message={result['message']}"
            if result['ticket']:
                url += f"&ticket_id={result['ticket'].id}"
            return redirect(url)
    
    # Si es GET, mostrar la página de verificación
    return render(request, 'eventos/verify_ticket.html', {
        'now': timezone.now()
    })


@staff_member_required
def access_permitted(request, ticket_id):
    """Vista para mostrar que el acceso está permitido"""
    # Usar el repositorio para obtener la entrada
    ticket = TicketRepository.get_ticket_by_id(ticket_id)
    
    return render(request, 'eventos/access_permitted.html', {
        'ticket': ticket
    })


@staff_member_required
def access_denied(request):
    """Vista para mostrar que el acceso está denegado"""
    message = request.GET.get('message', 'Acceso denegado')
    ticket_id = request.GET.get('ticket_id')
    
    context = {
        'message': message,
        'ticket': None
    }
    
    if ticket_id:
        try:
            ticket = TicketRepository.get_ticket_by_id(int(ticket_id))
            context['ticket'] = ticket
        except (ValueError, Ticket.DoesNotExist):
            pass
    
    return render(request, 'eventos/access_denied.html', context)

# -------------------------------------------------------------
# Vistas de autenticación y perfil de usuario
# -------------------------------------------------------------

def register(request):
    """Vista para registro de nuevos usuarios"""
    # Redirigir si ya está autenticado
    if request.user.is_authenticated:
        messages.info(request, 'Ya tienes una cuenta activa.')
        return redirect('/')
        
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        profile_form = UserProfileForm(request.POST)
        
        if user_form.is_valid() and profile_form.is_valid():
            # Usar transacción para asegurar que ambos se crean o ninguno
            with transaction.atomic():
                # Crear usuario
                user = user_form.save()
                
                # Crear perfil asociado
                profile = profile_form.save(commit=False)
                profile.user = user
                UserProfileRepository.save_profile(profile)
            
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
        profile = UserProfileRepository.get_profile_by_user(request.user.id)
        if not profile:
            profile = UserProfile(user=request.user)
            
        # Formulario para datos de perfil
        profile_form = UserProfileForm(request.POST, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            with transaction.atomic():
                user_form.save()
                UserProfileRepository.save_profile(profile_form.save(commit=False))
            messages.success(request, 'Perfil actualizado con éxito.')
            return redirect('eventos:profile')
    else:
        # Preparar formularios con datos actuales
        user_form = UserRegistrationForm(instance=request.user)
        
        profile = UserProfileRepository.get_profile_by_user(request.user.id)
        if not profile:
            profile = UserProfile(user=request.user)
            
        profile_form = UserProfileForm(instance=profile)
    
    # Crear contexto base
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    
    # Añadir estadísticas de tickets solo para usuarios normales, no para administradores
    if not request.user.is_staff:
        ticket_count = TicketRepository.get_tickets_by_user(request.user.id).count()
        upcoming_tickets = TicketRepository.get_tickets_by_user_and_event(
            request.user.id, 
            EventRepository.get_upcoming_events().values_list('id', flat=True)
        ).count()
        used_tickets = TicketRepository.get_tickets_by_status(request.user.id, 'used').count()
        paid_tickets = TicketRepository.get_tickets_by_status(request.user.id, 'paid').count()
        unpaid_tickets = TicketRepository.get_tickets_by_status(request.user.id, 'unpaid').count()
        
        context.update({
            'ticket_count': ticket_count,
            'upcoming_tickets': upcoming_tickets,
            'used_tickets': used_tickets,
            'paid_tickets': paid_tickets,
            'unpaid_tickets': unpaid_tickets
        })
    
    return render(request, 'eventos/profile.html', context)

# -------------------------------------------------------------
# Vistas de administración y estadísticas
# -------------------------------------------------------------

@staff_member_required
def dashboard(request):
    """Vista de panel de control con estadísticas (solo staff)"""
    try:
        # Usar el servicio para obtener las estadísticas del dashboard
        stats = EventService.get_dashboard_stats()
        return render(request, 'eventos/dashboard.html', stats)
    except Exception as e:
        logger.error(f"Error en dashboard: {str(e)}")
        messages.error(request, f"Error al cargar el panel de control: {str(e)}")
        return redirect('/')