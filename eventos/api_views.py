from django.http import JsonResponse
from django.db.models import Q
from .models import Event
from django.utils import timezone

def search_suggestions(request):
    """Vista API para proporcionar sugerencias de eventos mientras el usuario escribe en el buscador"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'suggestions': []})
    
    # Buscar eventos que coincidan con la consulta
    events = Event.objects.filter(
        Q(name__icontains=query) | 
        Q(description__icontains=query) |
        Q(location__icontains=query)
    ).filter(
        event_date__gte=timezone.now()  # Solo eventos futuros
    ).order_by('event_date')[:5]  # Limitar a 5 resultados
    
    # Preparar datos para la respuesta JSON
    suggestions = []
    for event in events:
        suggestions.append({
            'id': event.id,
            'name': event.name,
            'location': event.location,
            'event_date': event.event_date.isoformat(),
            'image': event.image.url if event.image else None
        })
    
    return JsonResponse({'suggestions': suggestions})