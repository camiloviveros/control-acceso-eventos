# eventos/statistics.py (nuevo archivo)

from django.db.models import Count, Sum, Q, F
from django.utils import timezone
import logging

from .models import Event, TicketType, Ticket, User

logger = logging.getLogger(__name__)

class EventStatisticsService:
    """Servicio para generar estadísticas de eventos"""
    
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
    def get_events_with_low_availability(threshold_percent=20, limit=5):
        """Obtener eventos con baja disponibilidad de asientos"""
        try:
            return Event.objects.annotate(
                available_seats=Sum('tickettype__available_quantity')
            ).filter(
                available_seats__lt=F('capacity') * threshold_percent/100,  # Menos del porcentaje indicado
                event_date__gt=timezone.now()  # Solo eventos futuros
            ).order_by('event_date')[:limit]
        except Exception as e:
            logger.error(f"Error al obtener eventos con baja disponibilidad: {str(e)}")
            return Event.objects.none()
    
    @staticmethod
    def get_sales_by_time_period(days=30):
        """Obtener ventas agrupadas por día para un período determinado"""
        try:
            from django.db.models.functions import TruncDate
            
            start_date = timezone.now() - timezone.timedelta(days=days)
            
            return Ticket.objects.filter(
                is_paid=True,
                purchase_date__gte=start_date
            ).annotate(
                day=TruncDate('purchase_date')
            ).values('day').annotate(
                count=Count('id'),
                revenue=Sum('ticket_type__price')
            ).order_by('day')
        except Exception as e:
            logger.error(f"Error al obtener ventas por período: {str(e)}")
            return []
    
    @staticmethod
    def get_detailed_dashboard_stats():
        """Obtener estadísticas detalladas para el dashboard avanzado"""
        try:
            stats = {
                'popular_events': EventStatisticsService.get_events_by_popularity(),
                'revenue_by_event': EventStatisticsService.get_revenue_by_event(),
                'ticket_distribution': EventStatisticsService.get_ticket_type_distribution(),
                'low_availability': EventStatisticsService.get_events_with_low_availability(),
                'sales_last_30_days': EventStatisticsService.get_sales_by_time_period(30),
                'sales_last_7_days': EventStatisticsService.get_sales_by_time_period(7),
                
                # Estadísticas adicionales
                'total_revenue': Ticket.objects.filter(is_paid=True).aggregate(
                    total=Sum('ticket_type__price')
                )['total'] or 0,
                
                'total_events': Event.objects.count(),
                'upcoming_events': Event.objects.filter(event_date__gt=timezone.now()).count(),
                'past_events': Event.objects.filter(event_date__lte=timezone.now()).count(),
                
                'total_tickets': Ticket.objects.count(),
                'paid_tickets': Ticket.objects.filter(is_paid=True).count(),
                'used_tickets': Ticket.objects.filter(is_used=True).count(),
                
                'total_users': User.objects.count(),
                'active_users': User.objects.filter(is_active=True).count(),
            }
            
            return stats
        except Exception as e:
            logger.error(f"Error al obtener estadísticas detalladas: {str(e)}")
            return {}