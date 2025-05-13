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
from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.exceptions import PermissionDenied
from django.db import transaction
from datetime import datetime

# Importaciones de bibliotecas externas
import qrcode
from io import BytesIO
import uuid
import logging

# Importaciones locales de la aplicación
from .models import Event, TicketType, Ticket, UserProfile, Payment
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
            # Verificar que la fecha del evento no esté en el pasado
            event_date = form.cleaned_data['event_date']
            if event_date < timezone.now():
                messages.error(request, 'No se pueden crear eventos en el pasado. Por favor, selecciona una fecha futura.')
                return render(request, 'eventos/event_form.html', {
                    'form': form,
                    'title': 'Crear Evento',
                    'button_text': 'Crear'
                })
            
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
            # Verificar que la fecha del evento no esté en el pasado
            event_date = form.cleaned_data['event_date']
            if event_date < timezone.now():
                messages.error(request, 'No se pueden actualizar eventos con fechas en el pasado. Por favor, selecciona una fecha futura.')
                return render(request, 'eventos/event_form.html', {
                    'form': form,
                    'event': event,
                    'title': 'Editar Evento',
                    'button_text': 'Actualizar'
                })
                
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
        try:
            # Guardar nombre para mensaje
            event_name = event.name
            # Eliminar evento - esto eliminará cascada todos los ticket_types y tickets asociados
            event.delete()
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
    
    # Verificar que los administradores no puedan comprar entradas
    if request.user.is_staff:
        messages.warning(request, 'Los administradores no pueden comprar entradas.')
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
    ticket = get_object_or_404(Ticket, pk=ticket_id, user=request.user)
    
    # Verificar que la entrada no esté pagada
    if ticket.is_paid:
        messages.warning(request, 'Esta entrada ya está pagada y tiene asiento asignado.')
        return redirect('eventos:ticket_detail', ticket_id=ticket.id)
    
    # Verificar que el evento permita selección de asientos
    if not ticket.ticket_type.event.has_seats:
        messages.warning(request, 'Este evento no requiere selección de asientos.')
        return redirect('eventos:payment_process', ticket_id=ticket.id)
    
    # Obtener asientos ocupados
    taken_seats = Ticket.objects.filter(
        ticket_type__event=ticket.ticket_type.event, 
        seat_number__isnull=False
    ).values_list('seat_number', flat=True)
    
    if request.method == 'POST':
        seat_number = request.POST.get('seat_number')
        section = request.POST.get('section')
        
        if not seat_number or not section:
            messages.error(request, 'Por favor, selecciona un asiento y sección.')
            return render(request, 'eventos/seat_selection.html', {
                'ticket': ticket,
                'taken_seats': taken_seats
            })
        
        # Verificar que el asiento no esté ocupado
        if seat_number in taken_seats:
            messages.error(request, 'Este asiento ya está ocupado. Por favor, selecciona otro.')
            return render(request, 'eventos/seat_selection.html', {
                'ticket': ticket,
                'taken_seats': taken_seats
            })
        
        # Asignar asiento
        ticket.seat_number = seat_number
        ticket.section = section
        ticket.save()
        
        messages.success(request, 'Asiento seleccionado correctamente.')
        return redirect('eventos:payment_process', ticket_id=ticket.id)
    
    return render(request, 'eventos/seat_selection.html', {
        'ticket': ticket,
        'taken_seats': taken_seats
    })


@login_required
def payment_process(request, ticket_id):
    """Vista para procesar el pago de una entrada"""
    ticket = get_object_or_404(Ticket, pk=ticket_id, user=request.user)
    
    # Verificar que la entrada no haya sido pagada
    if ticket.is_paid:
        messages.warning(request, 'Esta entrada ya ha sido pagada.')
        return redirect('eventos:ticket_detail', ticket_id=ticket.id)
    
    if request.method == 'POST':
        # Obtener datos del formulario
        payment_method = request.POST.get('payment_method')
        
        if not payment_method:
            messages.error(request, 'Por favor, selecciona un método de pago.')
            return render(request, 'eventos/payment_process.html', {'ticket': ticket})
        
        try:
            # Procesar información de tarjeta (si aplica)
            card_last_digits = None
            card_type = None
            
            if payment_method in ['credit_card', 'debit_card']:
                card_number = request.POST.get('card_number', '').replace(' ', '')
                card_expiry = request.POST.get('card_expiry')
                card_cvv = request.POST.get('card_cvv')
                card_holder = request.POST.get('card_holder')
                
                # Validaciones básicas
                if not card_number or len(card_number) < 13:
                    messages.error(request, 'Número de tarjeta inválido.')
                    return render(request, 'eventos/payment_process.html', {'ticket': ticket})
                
                if not card_expiry or not card_cvv or not card_holder:
                    messages.error(request, 'Por favor, completa todos los campos de la tarjeta.')
                    return render(request, 'eventos/payment_process.html', {'ticket': ticket})
                
                # Guardar últimos 4 dígitos (en un sistema real, no guardaríamos el número completo)
                card_last_digits = card_number[-4:]
                
                # Determinar tipo de tarjeta según el primer dígito
                first_digit = card_number[0] if card_number else ''
                if first_digit == '4':
                    card_type = 'Visa'
                elif first_digit == '5':
                    card_type = 'MasterCard'
                elif first_digit == '3':
                    card_type = 'American Express'
                else:
                    card_type = 'Otra'
            
            # Crear registro de pago
            payment = Payment(
                user=request.user,
                ticket=ticket,
                amount=ticket.ticket_type.price,
                payment_method=payment_method,
                status='completed',
                transaction_id=str(uuid.uuid4())[:8],  # Simulación de ID de transacción
                card_last_digits=card_last_digits,
                card_type=card_type
            )
            payment.save()
            
            # Actualizar estado de la entrada
            ticket.is_paid = True
            ticket.save(update_fields=['is_paid'])
            
            messages.success(request, '¡Pago procesado con éxito! Ya puedes acceder a tu entrada con código QR.')
            return redirect('eventos:ticket_detail', ticket_id=ticket.id)
            
        except Exception as e:
            logger.error(f"Error en proceso de pago: {str(e)}")
            messages.error(request, f'Error al procesar el pago: {str(e)}')
    
    return render(request, 'eventos/payment_process.html', {'ticket': ticket})


@login_required
def ticket_detail(request, ticket_id):
    """Vista para mostrar el detalle de una entrada con su QR"""
    ticket = get_object_or_404(Ticket, pk=ticket_id, user=request.user)
    
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
    elif status == 'paid':
        base_tickets = base_tickets.filter(is_paid=True)
    elif status == 'unpaid':
        base_tickets = base_tickets.filter(is_paid=False)
    
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
    # Obtener la entrada, verificando que pertenezca al usuario actual o sea staff
    ticket = None
    if request.user.is_staff:
        ticket = get_object_or_404(Ticket, pk=ticket_id)
    else:
        ticket = get_object_or_404(Ticket, pk=ticket_id, user=request.user)
    
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
            
            # Verificar si ha expirado
            if ticket.is_expired():
                return JsonResponse({
                    'valid': False,
                    'message': 'Esta entrada ha expirado.'
                })
            
            # Verificar si está pagada
            if not ticket.is_paid:
                return JsonResponse({
                    'valid': False,
                    'message': 'Esta entrada no ha sido pagada.'
                })
            
            # Quitamos estas verificaciones para pruebas
            # No verificamos si el evento comenzó o finalizó
            # De esta forma se puede escanear en cualquier momento
            
            # Si todo está correcto, marcar como utilizada
            ticket.is_used = True
            ticket.entry_time = entry_time
            
            # Incrementar contador de escaneos
            ticket.scan_count = ticket.scan_count + 1
            
            ticket.save(update_fields=['is_used', 'entry_time', 'scan_count'])
            
            # Devolver información de la entrada verificada
            return JsonResponse({
                'valid': True,
                'ticket': {
                    'id': ticket.id,
                    'event': ticket.ticket_type.event.name,
                    'ticket_type': ticket.ticket_type.name,
                    'user': f"{ticket.user.first_name} {ticket.user.last_name}" if ticket.user.first_name else ticket.user.username,
                    'purchase_date': ticket.purchase_date.strftime('%d/%m/%Y %H:%M'),
                    'seat_number': ticket.seat_number or 'N/A',
                    'section': ticket.section or 'N/A',
                    'entry_time': entry_time.strftime('%d/%m/%Y %H:%M') if entry_time else 'N/A',
                    'scan_count': ticket.scan_count
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
    return render(request, 'eventos/verify_ticket.html', {
        'now': timezone.now()
    })

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
            return redirect('eventos:profile')
    else:
        # Preparar formularios con datos actuales
        user_form = UserRegistrationForm(instance=request.user)
        
        try:
            profile = request.user.profile
        except UserProfile.DoesNotExist:
            profile = UserProfile(user=request.user)
            
        profile_form = UserProfileForm(instance=profile)
    
    # Crear contexto base
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    
    # Añadir estadísticas de tickets solo para usuarios normales, no para administradores
    if not request.user.is_staff:
        tickets = Ticket.objects.filter(user=request.user)
        upcoming_tickets = tickets.filter(ticket_type__event__event_date__gte=timezone.now())
        used_tickets = tickets.filter(is_used=True)
        paid_tickets = tickets.filter(is_paid=True)
        unpaid_tickets = tickets.filter(is_paid=False)
        
        context.update({
            'ticket_count': tickets.count(),
            'upcoming_tickets': upcoming_tickets.count(),
            'used_tickets': used_tickets.count(),
            'paid_tickets': paid_tickets.count(),
            'unpaid_tickets': unpaid_tickets.count()
        })
    
    return render(request, 'eventos/profile.html', context)

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
        paid_tickets = Ticket.objects.filter(is_paid=True).count()
        total_users = User.objects.count()
        total_revenue = Payment.objects.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Eventos más populares (con más entradas vendidas)
        popular_events = Event.objects.annotate(
            ticket_count=Count('tickettype__ticket', filter=Q(tickettype__ticket__is_paid=True))
        ).order_by('-ticket_count')[:5]
        
        # Ventas por evento (ingresos)
        sales_by_event = Event.objects.annotate(
            ticket_count=Count('tickettype__ticket', filter=Q(tickettype__ticket__is_paid=True)),
            revenue=Sum('tickettype__ticket__ticket_type__price', filter=Q(tickettype__ticket__is_paid=True))
        ).order_by('-revenue')[:10]
        
        return render(request, 'eventos/dashboard.html', {
            'total_events': total_events,
            'upcoming_events': upcoming_events,
            'total_tickets': total_tickets,
            'used_tickets': used_tickets,
            'paid_tickets': paid_tickets,
            'total_users': total_users,
            'total_revenue': total_revenue,
            'popular_events': popular_events,
            'sales_by_event': sales_by_event
        })
    except Exception as e:
        logger.error(f"Error en dashboard: {str(e)}")
        messages.error(request, f"Error al cargar el panel de control: {str(e)}")
        return redirect('/')  # Usar URL absoluta
            