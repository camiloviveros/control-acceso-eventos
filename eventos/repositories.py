
from django.db.models import Q, Count, Sum, F, Prefetch
from django.utils import timezone
import logging

# Importar modelos explícitamente para evitar errores
from .models import Event, TicketType, Ticket, UserProfile, Payment

# Configurar logging para mejor depuración
logger = logging.getLogger(__name__)

class EventRepository:
    """Repositorio para manejar operaciones de consulta y persistencia de eventos"""
    
    @staticmethod
    def get_all_events(order_by='-event_date'):
        """Obtener todos los eventos ordenados según el criterio especificado"""
        try:
            return Event.objects.all().order_by(order_by)
        except Exception as e:
            logger.error(f"Error al obtener todos los eventos: {str(e)}")
            return Event.objects.none()  # Devolver un queryset vacío en caso de error
    
    @staticmethod
    def get_event_by_id(event_id):
        """Obtener un evento específico por su ID"""
        try:
            return Event.objects.select_related().get(id=event_id)
        except Event.DoesNotExist:
            logger.warning(f"Evento con ID {event_id} no encontrado")
            raise
        except Exception as e:
            logger.error(f"Error al obtener evento por ID {event_id}: {str(e)}")
            raise
    
    @staticmethod
    def get_upcoming_events(limit=None):
        """Obtener eventos próximos"""
        try:
            queryset = Event.objects.filter(
                event_date__gte=timezone.now()
            ).order_by('event_date')
            
            if limit:
                queryset = queryset[:limit]
                
            return queryset
        except Exception as e:
            logger.error(f"Error al obtener eventos próximos: {str(e)}")
            return Event.objects.none()
    
    @staticmethod
    def get_past_events():
        """Obtener eventos pasados"""
        try:
            return Event.objects.filter(
                event_date__lt=timezone.now()
            ).order_by('-event_date')
        except Exception as e:
            logger.error(f"Error al obtener eventos pasados: {str(e)}")
            return Event.objects.none()
    
    @staticmethod
    def search_events(query=None, date_filter=None, order_by='-event_date'):
        """Buscar eventos con filtros aplicados"""
        try:
            queryset = Event.objects.all()
            
            # Filtrar por búsqueda
            if query:
                queryset = queryset.filter(
                    Q(name__icontains=query) | 
                    Q(description__icontains=query) |
                    Q(location__icontains=query)
                )
            
            # Filtrar por fecha
            if date_filter == 'upcoming':
                queryset = queryset.filter(event_date__gte=timezone.now())
            elif date_filter == 'past':
                queryset = queryset.filter(event_date__lt=timezone.now())
            
            # Ordenar resultados
            return queryset.order_by(order_by)
        except Exception as e:
            logger.error(f"Error al buscar eventos: {str(e)}")
            return Event.objects.none()
    
    @staticmethod
    def get_popular_events(limit=5):
        """Obtener eventos más populares (con más entradas vendidas)"""
        try:
            return Event.objects.annotate(
                ticket_count=Count('tickettype__ticket', filter=Q(tickettype__ticket__is_paid=True))
            ).order_by('-ticket_count')[:limit]
        except Exception as e:
            logger.error(f"Error al obtener eventos populares: {str(e)}")
            return Event.objects.none()
    
    @staticmethod
    def get_sales_by_event(limit=10):
        """Obtener ventas por evento (ingresos)"""
        try:
            return Event.objects.annotate(
                ticket_count=Count('tickettype__ticket', filter=Q(tickettype__ticket__is_paid=True)),
                revenue=Sum('tickettype__ticket__ticket_type__price', filter=Q(tickettype__ticket__is_paid=True))
            ).order_by('-revenue')[:limit]
        except Exception as e:
            logger.error(f"Error al obtener ventas por evento: {str(e)}")
            return Event.objects.none()
    
    @staticmethod
    def get_categories():
        """Obtener todas las categorías de eventos"""
        try:
            return Event.objects.values_list('category', flat=True).distinct()
        except Exception as e:
            logger.error(f"Error al obtener categorías de eventos: {str(e)}")
            return []
    
    @staticmethod
    def get_events_by_category(category):
        """Obtener eventos filtrados por categoría"""
        try:
            return Event.objects.filter(category=category)
        except Exception as e:
            logger.error(f"Error al obtener eventos por categoría {category}: {str(e)}")
            return Event.objects.none()
    
    @staticmethod
    def get_events_by_popularity(limit=10):
        """Obtener eventos ordenados por cantidad de entradas vendidas"""
        try:
            return Event.objects.annotate(
                tickets_sold=Count('tickettype__ticket', filter=Q(tickettype__ticket__is_paid=True))
            ).order_by('-tickets_sold')[:limit]
        except Exception as e:
            logger.error(f"Error al obtener eventos por popularidad: {str(e)}")
            return Event.objects.none()
    
    @staticmethod
    def get_revenue_by_event(limit=10):
        """Obtener ingresos por evento"""
        try:
            return Event.objects.annotate(
                revenue=Sum(
                    'tickettype__ticket__ticket_type__price', 
                    filter=Q(tickettype__ticket__is_paid=True)
                )
            ).exclude(revenue__isnull=True).order_by('-revenue')[:limit]
        except Exception as e:
            logger.error(f"Error al obtener ingresos por evento: {str(e)}")
            return Event.objects.none()
    
    @staticmethod
    def get_ticket_type_distribution():
        """Obtener distribución de tipos de entradas vendidas"""
        try:
            return TicketType.objects.annotate(
                tickets_sold=Count('ticket', filter=Q(ticket__is_paid=True))
            ).values('name', 'tickets_sold').order_by('-tickets_sold')[:10]
        except Exception as e:
            logger.error(f"Error al obtener distribución de tipos de entradas: {str(e)}")
            return []
    
    @staticmethod
    def save_event(event):
        """Guardar un evento en la base de datos"""
        try:
            event.save()
            return event
        except Exception as e:
            logger.error(f"Error al guardar evento: {str(e)}")
            raise
    
    @staticmethod
    def delete_event(event):
        """Eliminar un evento de la base de datos"""
        try:
            event_name = event.name
            event.delete()
            return event_name
        except Exception as e:
            logger.error(f"Error al eliminar evento: {str(e)}")
            raise


class TicketTypeRepository:
    """Repositorio para manejar operaciones de consulta y persistencia de tipos de entradas"""
    
    @staticmethod
    def get_ticket_types_by_event(event_id):
        """Obtener todos los tipos de entradas para un evento específico"""
        try:
            return TicketType.objects.filter(event_id=event_id)
        except Exception as e:
            logger.error(f"Error al obtener tipos de entradas para el evento {event_id}: {str(e)}")
            return TicketType.objects.none()
    
    @staticmethod
    def get_ticket_type_by_id(ticket_type_id):
        """Obtener un tipo de entrada específico por su ID"""
        try:
            return TicketType.objects.select_related('event').get(id=ticket_type_id)
        except TicketType.DoesNotExist:
            logger.warning(f"Tipo de entrada con ID {ticket_type_id} no encontrado")
            raise
        except Exception as e:
            logger.error(f"Error al obtener tipo de entrada por ID {ticket_type_id}: {str(e)}")
            raise
    
    @staticmethod
    def save_ticket_type(ticket_type):
        """Guardar un tipo de entrada en la base de datos"""
        try:
            ticket_type.save()
            return ticket_type
        except Exception as e:
            logger.error(f"Error al guardar tipo de entrada: {str(e)}")
            raise


class TicketRepository:
    """Repositorio para manejar operaciones de consulta y persistencia de entradas"""
    
    @staticmethod
    def get_ticket_by_id(ticket_id):
        """Obtener una entrada específica por su ID"""
        try:
            return Ticket.objects.select_related(
                'ticket_type', 
                'ticket_type__event', 
                'user'
            ).get(id=ticket_id)
        except Ticket.DoesNotExist:
            logger.warning(f"Entrada con ID {ticket_id} no encontrada")
            raise
        except Exception as e:
            logger.error(f"Error al obtener entrada por ID {ticket_id}: {str(e)}")
            raise
    
    @staticmethod
    def get_ticket_by_code(ticket_code):
        """Obtener una entrada por su código único"""
        try:
            return Ticket.objects.select_related(
                'ticket_type', 
                'ticket_type__event', 
                'user'
            ).get(ticket_code=ticket_code)
        except Ticket.DoesNotExist:
            logger.warning(f"Entrada con código {ticket_code} no encontrada")
            raise
        except Exception as e:
            logger.error(f"Error al obtener entrada por código {ticket_code}: {str(e)}")
            raise
    
    @staticmethod
    def get_tickets_by_user(user_id):
        """Obtener todas las entradas de un usuario"""
        try:
            return Ticket.objects.filter(user_id=user_id).select_related(
                'ticket_type', 'ticket_type__event'
            ).order_by('-purchase_date')
        except Exception as e:
            logger.error(f"Error al obtener entradas del usuario {user_id}: {str(e)}")
            return Ticket.objects.none()
    
    @staticmethod
    def get_tickets_by_user_and_event(user_id, event_id):
        """Obtener entradas de un usuario para un evento específico"""
        try:
            return Ticket.objects.filter(
                user_id=user_id, 
                ticket_type__event_id=event_id
            ).select_related('ticket_type', 'ticket_type__event')
        except Exception as e:
            logger.error(f"Error al obtener entradas del usuario {user_id} para el evento {event_id}: {str(e)}")
            return Ticket.objects.none()
    
    @staticmethod
    def get_tickets_by_status(user_id, status):
        """Obtener entradas filtradas por estado"""
        try:
            queryset = Ticket.objects.filter(user_id=user_id)
            
            if status == 'used':
                queryset = queryset.filter(is_used=True)
            elif status == 'unused':
                queryset = queryset.filter(is_used=False)
            elif status == 'paid':
                queryset = queryset.filter(is_paid=True)
            elif status == 'unpaid':
                queryset = queryset.filter(is_paid=False)
            
            return queryset.select_related('ticket_type', 'ticket_type__event')
        except Exception as e:
            logger.error(f"Error al obtener entradas del usuario {user_id} por estado {status}: {str(e)}")
            return Ticket.objects.none()
    
    @staticmethod
    def get_occupied_seats(event_id):
        """Obtener asientos ocupados para un evento"""
        try:
            return Ticket.objects.filter(
                ticket_type__event_id=event_id, 
                seat_number__isnull=False
            ).values_list('seat_number', flat=True)
        except Exception as e:
            logger.error(f"Error al obtener asientos ocupados para el evento {event_id}: {str(e)}")
            return []
    
    @staticmethod
    def save_ticket(ticket):
        """Guardar una entrada en la base de datos"""
        try:
            ticket.save()
            return ticket
        except Exception as e:
            logger.error(f"Error al guardar entrada: {str(e)}")
            raise
    
    @staticmethod
    def save_tickets_batch(tickets):
        """Guardar varias entradas en lote"""
        saved_tickets = []
        for ticket in tickets:
            try:
                ticket.save()
                saved_tickets.append(ticket)
            except Exception as e:
                logger.error(f"Error al guardar entrada en lote: {str(e)}")
                raise
        return saved_tickets
    
    @staticmethod
    def update_ticket(ticket, **kwargs):
        """Actualizar campos específicos de una entrada"""
        try:
            for key, value in kwargs.items():
                setattr(ticket, key, value)
            ticket.save(update_fields=list(kwargs.keys()))
            return ticket
        except Exception as e:
            logger.error(f"Error al actualizar entrada: {str(e)}")
            raise


class PaymentRepository:
    """Repositorio para manejar operaciones de consulta y persistencia de pagos"""
    
    @staticmethod
    def get_payment_by_ticket(ticket_id):
        """Obtener el pago asociado a una entrada específica"""
        try:
            return Payment.objects.filter(ticket_id=ticket_id).first()
        except Exception as e:
            logger.error(f"Error al obtener pago para la entrada {ticket_id}: {str(e)}")
            return None
    
    @staticmethod
    def get_payments_by_user(user_id):
        """Obtener todos los pagos de un usuario"""
        try:
            return Payment.objects.filter(user_id=user_id).select_related('ticket')
        except Exception as e:
            logger.error(f"Error al obtener pagos del usuario {user_id}: {str(e)}")
            return Payment.objects.none()
    
    @staticmethod
    def get_total_revenue():
        """Obtener el ingreso total de todos los pagos completados"""
        try:
            return Payment.objects.filter(
                status='completed'
            ).aggregate(Sum('amount'))['amount__sum'] or 0
        except Exception as e:
            logger.error(f"Error al obtener ingresos totales: {str(e)}")
            return 0
    
    @staticmethod
    def save_payment(payment):
        """Guardar un pago en la base de datos"""
        try:
            payment.save()
            return payment
        except Exception as e:
            logger.error(f"Error al guardar pago: {str(e)}")
            raise


class UserProfileRepository:
    """Repositorio para manejar operaciones de consulta y persistencia de perfiles de usuario"""
    
    @staticmethod
    def get_profile_by_user(user_id):
        """Obtener el perfil de un usuario específico"""
        try:
            return UserProfile.objects.filter(user_id=user_id).first()
        except Exception as e:
            logger.error(f"Error al obtener perfil del usuario {user_id}: {str(e)}")
            return None
    
    @staticmethod
    def save_profile(profile):
        """Guardar un perfil de usuario en la base de datos"""
        try:
            profile.save()
            return profile
        except Exception as e:
            logger.error(f"Error al guardar perfil de usuario: {str(e)}")
            raise