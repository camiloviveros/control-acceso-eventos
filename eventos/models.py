from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

class Event(models.Model):
    CATEGORY_CHOICES = (
        ('music', 'Música'),
        ('sports', 'Deportes'),
        ('culture', 'Cultura'),
        ('education', 'Educación'),
        ('business', 'Negocios'),
        ('other', 'Otro'),
    )
    
    name = models.CharField(max_length=255, verbose_name="Nombre del evento")
    description = models.TextField(verbose_name="Descripción")
    event_date = models.DateTimeField(verbose_name="Fecha y hora")
    location = models.CharField(max_length=255, verbose_name="Ubicación")
    capacity = models.PositiveIntegerField(verbose_name="Capacidad")
    image = models.ImageField(upload_to='event_images/', null=True, blank=True, verbose_name="Imagen")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    has_seats = models.BooleanField(default=False, verbose_name="¿Tiene asientos numerados?")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other', verbose_name="Categoría")
    
    class Meta:
        verbose_name = "Evento"
        verbose_name_plural = "Eventos"
        ordering = ['-event_date']
    
    def __str__(self):
        return self.name
    
    def get_available_tickets(self):
        """Devuelve el número total de entradas disponibles para este evento"""
        available = 0
        for ticket_type in self.tickettype_set.all():
            available += ticket_type.available_quantity
        return available
    
    def is_upcoming(self):
        """Comprueba si el evento está por venir"""
        return self.event_date > timezone.now()

class TicketType(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, verbose_name="Evento")
    name = models.CharField(max_length=255, verbose_name="Tipo de entrada")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio")
    available_quantity = models.PositiveIntegerField(verbose_name="Cantidad disponible")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Tipo de entrada"
        verbose_name_plural = "Tipos de entradas"
    
    def __str__(self):
        return f"{self.name} - {self.event.name}"
    
    def is_available(self):
        """Comprueba si este tipo de entrada está disponible"""
        return self.available_quantity > 0 and self.event.is_upcoming()

class Ticket(models.Model):
    ticket_type = models.ForeignKey(TicketType, on_delete=models.CASCADE, verbose_name="Tipo de entrada")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Usuario")
    purchase_date = models.DateTimeField(default=timezone.now, verbose_name="Fecha de compra")
    ticket_code = models.CharField(max_length=255, unique=True, default=uuid.uuid4, verbose_name="Código de entrada")
    is_used = models.BooleanField(default=False, verbose_name="Utilizada")
    
    # Campos existentes
    seat_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="Número de asiento")
    section = models.CharField(max_length=50, blank=True, null=True, verbose_name="Sección")
    entry_time = models.DateTimeField(blank=True, null=True, verbose_name="Hora de entrada")
    exit_time = models.DateTimeField(blank=True, null=True, verbose_name="Hora de salida")
    expiration_date = models.DateTimeField(blank=True, null=True, verbose_name="Fecha de expiración")
    is_paid = models.BooleanField(default=False, verbose_name="Pagado")
    
    # Nuevo campo para contador de escaneos
    scan_count = models.PositiveIntegerField(default=0, verbose_name="Número de escaneos")
    
    class Meta:
        verbose_name = "Entrada"
        verbose_name_plural = "Entradas"
    
    def __str__(self):
        return f"Entrada {self.ticket_code} - {self.ticket_type.event.name}"
    
    def save(self, *args, **kwargs):
        """Sobreescribe el método save para disminuir la cantidad disponible y configurar expiración"""
        if not self.pk:  # Si es una nueva entrada
            ticket_type = self.ticket_type
            if ticket_type.available_quantity > 0:
                ticket_type.available_quantity -= 1
                ticket_type.save()
                
                # Establecer fecha de expiración (4 horas después del evento en lugar de 2)
                if not self.expiration_date and self.ticket_type.event.event_date:
                    self.expiration_date = self.ticket_type.event.event_date + timezone.timedelta(hours=4)
            else:
                raise ValueError("No hay entradas disponibles de este tipo")
        super().save(*args, **kwargs)
    
    def is_expired(self):
        """Comprueba si la entrada ha expirado"""
        if self.expiration_date:
            return timezone.now() > self.expiration_date
        return False

class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pendiente'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Usuario")
    ticket = models.OneToOneField(Ticket, on_delete=models.CASCADE, verbose_name="Entrada")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Monto")
    payment_date = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de pago")
    payment_method = models.CharField(max_length=50, verbose_name="Método de pago")
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending', verbose_name="Estado")
    transaction_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="ID de transacción")
    
    # Nuevos campos para información de tarjeta
    card_last_digits = models.CharField(max_length=4, blank=True, null=True, verbose_name="Últimos 4 dígitos")
    card_type = models.CharField(max_length=20, blank=True, null=True, verbose_name="Tipo de tarjeta")
    
    class Meta:
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"
    
    def __str__(self):
        return f"Pago {self.id} - {self.user.username} - {self.status}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono")
    address = models.CharField(max_length=255, blank=True, null=True, verbose_name="Dirección")
    
    class Meta:
        verbose_name = "Perfil de usuario"
        verbose_name_plural = "Perfiles de usuarios"
    
    def __str__(self):
        return f"Perfil de {self.user.username}"