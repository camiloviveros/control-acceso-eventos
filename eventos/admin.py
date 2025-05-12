from django.contrib import admin
from .models import Event, TicketType, Ticket, UserProfile

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'event_date', 'location', 'capacity', 'get_available_tickets', 'is_upcoming')
    list_filter = ('event_date', 'location')
    search_fields = ('name', 'description', 'location')
    date_hierarchy = 'event_date'

@admin.register(TicketType)
class TicketTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'event', 'price', 'available_quantity', 'is_available')
    list_filter = ('event', 'price')
    search_fields = ('name', 'event__name')

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_code', 'ticket_type', 'user', 'purchase_date', 'is_used')
    list_filter = ('ticket_type__event', 'is_used', 'purchase_date')
    search_fields = ('ticket_code', 'user__username', 'ticket_type__event__name')
    date_hierarchy = 'purchase_date'
    readonly_fields = ('ticket_code', 'purchase_date')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'address')
    search_fields = ('user__username', 'user__email', 'phone')