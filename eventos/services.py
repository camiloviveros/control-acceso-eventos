# eventos/services.py

from django.utils import timezone
from django.db import transaction
from django.contrib.auth.models import User
import uuid
import logging

# Importar modelos explícitamente para evitar errores
from .models import Event, TicketType, Ticket, Payment, UserProfile
from .repositories import EventRepository, TicketTypeRepository, TicketRepository, PaymentRepository, UserProfileRepository

# Configurar logging para mejor depuración
logger = logging.getLogger(__name__)

class EventService:
    """Servicio para manejar la lógica de negocio relacionada con eventos"""
    
    @staticmethod
    def create_event(event_data):
        """Crear un nuevo evento"""
        # Verificar que la fecha del evento no esté en el pasado
        event_date = event_data.event_date if hasattr(event_data, 'event_date') else event_data.get('event_date')
        if event_date and event_date < timezone.now():
            raise ValueError('No se pueden crear eventos en el pasado. Por favor, selecciona una fecha futura.')
        
        return EventRepository.save_event(event_data)
    
    @staticmethod
    def update_event(event, event_data):
        """Actualizar un evento existente"""
        # Verificar que la fecha del evento no esté en el pasado
        event_date = event_data.get('event_date') if isinstance(event_data, dict) else getattr(event_data, 'event_date', None)
        if event_date and event_date < timezone.now():
            raise ValueError('No se pueden actualizar eventos con fechas en el pasado. Por favor, selecciona una fecha futura.')
        
        # Actualizar los campos del evento
        if isinstance(event_data, dict):
            for key, value in event_data.items():
                if hasattr(event, key) and key != 'id':  # No intentar actualizar el ID
                    setattr(event, key, value)
        else:
            # Si es un modelo, copiar atributos
            for field in Event._meta.fields:
                field_name = field.name
                if field_name != 'id' and hasattr(event_data, field_name):
                    setattr(event, field_name, getattr(event_data, field_name))
        
        return EventRepository.save_event(event)
    
    @staticmethod
    def delete_event(event):
        """Eliminar un evento"""
        try:
            return EventRepository.delete_event(event)
        except Exception as e:
            logger.error(f"Error al eliminar evento: {str(e)}")
            raise
    
    @staticmethod
    def get_dashboard_stats():
        """Obtener estadísticas para el panel de control"""
        # Estadísticas generales
        try:
            stats = {
                'total_events': Event.objects.count(),
                'upcoming_events': EventRepository.get_upcoming_events().count(),
                'total_tickets': Ticket.objects.count(),
                'used_tickets': Ticket.objects.filter(is_used=True).count(),
                'paid_tickets': Ticket.objects.filter(is_paid=True).count(),
                'total_users': User.objects.count(),
                'total_revenue': PaymentRepository.get_total_revenue(),
                'popular_events': EventRepository.get_popular_events(),
                'sales_by_event': EventRepository.get_sales_by_event()
            }
            return stats
        except Exception as e:
            logger.error(f"Error al obtener estadísticas del dashboard: {str(e)}")
            # Devolver estadísticas básicas en caso de error
            return {
                'total_events': 0,
                'upcoming_events': 0,
                'total_tickets': 0,
                'used_tickets': 0,
                'paid_tickets': 0,
                'total_users': 0,
                'total_revenue': 0,
                'popular_events': [],
                'sales_by_event': []
            }


class TicketTypeService:
    """Servicio para manejar la lógica de negocio relacionada con tipos de entradas"""
    
    @staticmethod
    def create_ticket_type(event, ticket_type_data):
        """Crear un nuevo tipo de entrada"""
        # Verificar que el evento no haya pasado
        if event.event_date < timezone.now():
            raise ValueError('No se pueden crear tipos de entradas para eventos pasados.')
        
        ticket_type = ticket_type_data
        ticket_type.event = event
        
        return TicketTypeRepository.save_ticket_type(ticket_type)


class TicketService:
    """Servicio para manejar la lógica de negocio relacionada con entradas"""
    
    @staticmethod
    def purchase_tickets(user, ticket_type, quantity):
        """Comprar entradas para un tipo de entrada específico"""
        # Verificar disponibilidad
        if not ticket_type.is_available():
            raise ValueError('Este tipo de entrada no está disponible.')
        
        # Verificar que hay suficientes entradas disponibles
        if quantity > ticket_type.available_quantity:
            raise ValueError(f'Solo hay {ticket_type.available_quantity} entradas disponibles.')
        
        # Crear las entradas
        tickets = []
        try:
            # Usar transacción para garantizar que todas las entradas se crean o ninguna
            with transaction.atomic():
                for _ in range(quantity):
                    ticket = Ticket(
                        ticket_type=ticket_type,
                        user=user,
                        ticket_code=str(uuid.uuid4())  # Generar código único
                    )
                    # Guardar la entrada
                    TicketRepository.save_ticket(ticket)
                    tickets.append(ticket)
                
                # Actualizar la cantidad disponible en el tipo de entrada
                ticket_type.available_quantity -= quantity
                TicketTypeRepository.save_ticket_type(ticket_type)
                
            return tickets
        except Exception as e:
            logger.error(f"Error al crear entradas: {str(e)}")
            raise
    
    @staticmethod
    def assign_seat(ticket, seat_number, section):
        """Asignar un asiento a una entrada"""
        # Verificar que la entrada no esté pagada
        if ticket.is_paid:
            raise ValueError('Esta entrada ya está pagada y tiene asiento asignado.')
        
        # Verificar que el asiento no esté ocupado
        occupied_seats = TicketRepository.get_occupied_seats(ticket.ticket_type.event.id)
        if seat_number in occupied_seats:
            raise ValueError('Este asiento ya está ocupado. Por favor, selecciona otro.')
        
        # Asignar asiento
        return TicketRepository.update_ticket(ticket, seat_number=seat_number, section=section)
    
    @staticmethod
    def process_payment(ticket, payment_data):
        """Procesar el pago de una entrada"""
        # Verificar que la entrada no haya sido pagada
        if ticket.is_paid:
            raise ValueError('Esta entrada ya ha sido pagada.')
        
        payment_method = payment_data.get('payment_method')
        if not payment_method:
            raise ValueError('Por favor, selecciona un método de pago.')
        
        # Procesar información de tarjeta (si aplica)
        card_last_digits = None
        card_type = None
        
        if payment_method in ['credit_card', 'debit_card']:
            card_number = payment_data.get('card_number', '').replace(' ', '')
            if not card_number or len(card_number) < 13:
                raise ValueError('Número de tarjeta inválido.')
            
            # Guardar últimos 4 dígitos
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
        
        try:
            # Crear registro de pago
            payment = Payment(
                user=ticket.user,
                ticket=ticket,
                amount=ticket.ticket_type.price,
                payment_method=payment_method,
                status='completed',
                transaction_id=str(uuid.uuid4())[:8],  # Simulación de ID de transacción
                card_last_digits=card_last_digits,
                card_type=card_type
            )
            
            # Usar transacción para garantizar que tanto el pago como la actualización de la entrada se realiza atómicamente
            with transaction.atomic():
                # Guardar el pago
                PaymentRepository.save_payment(payment)
                
                # Actualizar estado de la entrada
                TicketRepository.update_ticket(ticket, is_paid=True)
            
            return payment
        except Exception as e:
            logger.error(f"Error en proceso de pago: {str(e)}")
            raise
    
    @staticmethod
    def verify_ticket(ticket_code, entry_time=None):
        """Verificar una entrada por su código QR"""
        try:
            # Buscar la entrada por su código
            ticket = TicketRepository.get_ticket_by_code(ticket_code)
            
            # Verificar si ya fue utilizada
            if ticket.is_used:
                return {
                    'valid': False,
                    'message': 'Esta entrada ya ha sido utilizada.',
                    'ticket': ticket
                }
            
            # Verificar si ha expirado
            if ticket.is_expired():
                return {
                    'valid': False,
                    'message': 'Esta entrada ha expirado.',
                    'ticket': ticket
                }
            
            # Verificar si está pagada
            if not ticket.is_paid:
                return {
                    'valid': False,
                    'message': 'Esta entrada no ha sido pagada.',
                    'ticket': ticket
                }
            
            # Si todo está correcto, marcar como utilizada
            if not entry_time:
                entry_time = timezone.now()
                
            TicketRepository.update_ticket(
                ticket, 
                is_used=True, 
                entry_time=entry_time, 
                scan_count=ticket.scan_count + 1
            )
            
            return {
                'valid': True,
                'message': 'Entrada verificada con éxito.',
                'ticket': ticket
            }
        except Ticket.DoesNotExist:
            return {
                'valid': False,
                'message': 'Código de entrada inválido o no encontrado.',
                'ticket': None
            }
        except Exception as e:
            logger.error(f"Error al verificar entrada: {str(e)}")
            return {
                'valid': False,
                'message': f'Error al verificar la entrada: {str(e)}',
                'ticket': None
            }